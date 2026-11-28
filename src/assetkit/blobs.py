"""Foundation context: safe repository paths, LFS/hydrated blob verification, and GLB inspection."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import struct
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Literal

from med_assets.artifacts import parse_pointer

from .errors import AssetKitError
from .models import AssetModel

HEX64 = re.compile(r"^[0-9a-f]{64}$")
LFS_HEADER = b"version https://git-lfs.github.com/spec/"

BlobStatus = Literal[
    "verified",
    "pointer-match",
    "hydrated",
    "pointer",
    "missing",
    "mismatch",
    "invalid-pointer",
]


def normalize_path(value: str) -> str:
    """Normalize and validate a relative POSIX path inside a repository."""
    if not isinstance(value, str) or not value.strip():
        raise AssetKitError("Repository path must be a non-empty string")
    raw = value.replace("\\", "/").strip()
    if raw.startswith("/") or ".." in PurePosixPath(raw).parts:
        raise AssetKitError(f"Unsafe repository path: {value}")
    normalized = PurePosixPath(raw).as_posix()
    if normalized in {"", "."}:
        raise AssetKitError(f"Invalid repository path: {value}")
    return normalized


def safe_path(repo: Path, rel_path: str) -> Path:
    """Resolve a repository-relative path while rejecting symlinks and escapes."""
    norm = normalize_path(rel_path)
    root = repo.resolve()
    target = root / PurePosixPath(norm)
    try:
        resolved = target.resolve()
        resolved.relative_to(root)
    except ValueError as exc:
        raise AssetKitError(f"Path escapes repository: {rel_path}") from exc
    if target.is_symlink() or resolved != target:
        raise AssetKitError(f"Symlink path rejected: {rel_path}")
    return target


class BlobRef(AssetModel):
    """Observational identity of a file on disk (hydrated bytes vs. Git LFS pointer)."""

    path: str
    status: BlobStatus
    sha256: str | None = None
    bytes: int | None = None


def read_verified(repo: Path, rel_path: str, expected_sha256: str, expected_bytes: int) -> bytes:
    """Return the same hydrated bytes that were checked against the expected identity."""
    path = safe_path(repo, rel_path)
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise AssetKitError(f"Missing export bytes: {rel_path}") from exc
    if data.startswith(LFS_HEADER):
        raise AssetKitError(f"Export needs LFS hydration: {rel_path}")
    if len(data) != expected_bytes or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise AssetKitError(f"Export size or SHA-256 mismatch: {rel_path}")
    return data


def verify(
    repo: Path,
    rel_path: str,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> BlobRef:
    """Inspect a file without ever claiming an LFS pointer is hydrated content."""
    norm = normalize_path(rel_path)
    target = safe_path(repo, norm)
    if not target.is_file():
        return BlobRef(path=norm, status="missing")

    with target.open("rb") as stream:
        prefix = stream.read(1025)
        if prefix.startswith(LFS_HEADER):
            try:
                digest, size = parse_pointer(prefix)
            except ValueError:
                return BlobRef(path=norm, status="invalid-pointer")
            if expected_sha256 is not None or expected_bytes is not None:
                ok = (expected_sha256 is None or digest == expected_sha256) and (
                    expected_bytes is None or size == expected_bytes
                )
                return BlobRef(
                    path=norm,
                    status="pointer-match" if ok else "mismatch",
                    sha256=digest,
                    bytes=size,
                )
            return BlobRef(path=norm, status="pointer", sha256=digest, bytes=size)

        stream.seek(0)
        size = os.fstat(stream.fileno()).st_size
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if expected_sha256 is not None or expected_bytes is not None:
            ok = (expected_sha256 is None or digest == expected_sha256) and (
                expected_bytes is None or size == expected_bytes
            )
            return BlobRef(
                path=norm,
                status="verified" if ok else "mismatch",
                sha256=digest,
                bytes=size,
            )
        return BlobRef(path=norm, status="hydrated", sha256=digest, bytes=size)


class MeshStats(AssetModel):
    """Geometry summary extracted from a hydrated GLB v2 binary."""

    bytes: int
    triangles: int
    node_names: tuple[str, ...]
    node_triangles: dict[str, int]


def inspect_mesh(repo: Path, rel_path: str) -> MeshStats | None:
    """Read GLB v2 JSON chunk via stdlib only. Returns None for pointers or non-GLB files."""
    target = safe_path(repo, rel_path)
    if not target.is_file():
        return None
    with target.open("rb") as stream:
        return _inspect_mesh(stream, os.fstat(stream.fileno()).st_size)


def inspect_mesh_bytes(data: bytes) -> MeshStats | None:
    """Inspect the same hydrated bytes that a caller verified."""
    return _inspect_mesh(io.BytesIO(data), len(data))


def _inspect_mesh(stream: BinaryIO, size: int) -> MeshStats | None:
    if size < 20:
        return None
    header = stream.read(20)
    if len(header) != 20 or header.startswith(LFS_HEADER):
        return None
    magic, version, length, chunk_len, chunk_type = struct.unpack("<4sIIII", header)
    if (
        magic != b"glTF"
        or version != 2
        or length != size
        or chunk_type != 0x4E4F534A
        or chunk_len > size - 20
    ):
        return None
    raw_json = stream.read(chunk_len)
    try:
        doc = json.loads(raw_json.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict):
        return None

    accessors = doc.get("accessors", [])
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])

    def mesh_tris(mesh_idx: int) -> int:
        if mesh_idx < 0 or mesh_idx >= len(meshes):
            return 0
        total = 0
        for prim in meshes[mesh_idx].get("primitives", []):
            mode = prim.get("mode", 4)
            if mode not in (4, 5, 6):
                continue
            acc_idx = prim.get("indices")
            if acc_idx is None:
                acc_idx = prim.get("attributes", {}).get("POSITION")
            if acc_idx is None or acc_idx < 0 or acc_idx >= len(accessors):
                continue
            count = int(accessors[acc_idx].get("count", 0))
            if mode == 4:
                total += count // 3
            elif count >= 3:
                total += count - 2
        return total

    node_names: list[str] = []
    node_tris: dict[str, int] = {}
    total_tris = 0
    for node in nodes:
        name = node.get("name")
        if isinstance(name, str) and name:
            node_names.append(name)
        if "mesh" in node:
            tris = mesh_tris(int(node["mesh"]))
            if isinstance(name, str) and name:
                node_tris[name] = node_tris.get(name, 0) + tris
            total_tris += tris

    if total_tris == 0 and meshes:
        total_tris = sum(mesh_tris(i) for i in range(len(meshes)))

    return MeshStats(
        bytes=size,
        triangles=total_tris,
        node_names=tuple(node_names),
        node_triangles=node_tris,
    )
