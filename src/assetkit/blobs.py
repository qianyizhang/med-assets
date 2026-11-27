"""Foundation context: safe repository paths, LFS/hydrated blob verification, and GLB inspection."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import AssetKitError

HEX64 = re.compile(r"^[0-9a-f]{64}$")
LFS_HEADER = b"version https://git-lfs.github.com/spec/"


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


def _parse_lfs_pointer(prefix: bytes) -> tuple[str, int]:
    text = prefix.decode("utf-8", errors="strict")
    oid: str | None = None
    size: int | None = None
    for line in text.splitlines():
        if line.startswith("oid sha256:"):
            oid = line.split("oid sha256:", 1)[1].strip()
        elif line.startswith("size "):
            size = int(line.split("size ", 1)[1].strip())
    if oid is None or size is None or not HEX64.fullmatch(oid) or size < 0:
        raise ValueError("Invalid Git LFS pointer")
    return oid, size


@dataclass(frozen=True)
class BlobRef:
    """Observational identity of a file on disk (hydrated bytes vs. Git LFS pointer)."""

    path: str
    status: (
        str  # verified | pointer-match | hydrated | pointer | missing | mismatch | invalid-pointer
    )
    sha256: str | None
    bytes: int | None


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
        return BlobRef(norm, "missing", None, None)

    with target.open("rb") as stream:
        prefix = stream.read(1025)
        if prefix.startswith(LFS_HEADER):
            try:
                digest, size = _parse_lfs_pointer(prefix)
            except ValueError:
                return BlobRef(norm, "invalid-pointer", None, None)
            if expected_sha256 is not None or expected_bytes is not None:
                ok = (expected_sha256 is None or digest == expected_sha256) and (
                    expected_bytes is None or size == expected_bytes
                )
                return BlobRef(norm, "pointer-match" if ok else "mismatch", digest, size)
            return BlobRef(norm, "pointer", digest, size)

        stream.seek(0)
        size = target.stat().st_size
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if expected_sha256 is not None or expected_bytes is not None:
            ok = (expected_sha256 is None or digest == expected_sha256) and (
                expected_bytes is None or size == expected_bytes
            )
            return BlobRef(norm, "verified" if ok else "mismatch", digest, size)
        return BlobRef(norm, "hydrated", digest, size)


@dataclass(frozen=True)
class MeshStats:
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
    size = target.stat().st_size
    if size < 20:
        return None
    with target.open("rb") as stream:
        header = stream.read(20)
        if header.startswith(LFS_HEADER):
            return None
        magic, version, _length, chunk_len, chunk_type = struct.unpack("<4sIIII", header)
        if magic != b"glTF" or version != 2 or chunk_type != 0x4E4F534A:
            return None
        raw_json = stream.read(chunk_len)
    try:
        doc = json.loads(raw_json.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
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
    for idx, node in enumerate(nodes):
        name = node.get("name") or f"node_{idx}"
        node_names.append(name)
        if "mesh" in node:
            tris = mesh_tris(int(node["mesh"]))
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
