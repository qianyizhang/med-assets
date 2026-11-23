"""Repository path, identity, and verified-install primitives for asset consumers."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat

HEX64 = re.compile(r'[0-9a-f]{64}')
POINTER_PREFIX = b'version https://git-lfs.github.com/spec/'
POINTER = re.compile(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (0|[1-9][0-9]*)\n')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def source_path(name: str) -> str:
    if (not isinstance(name, str) or not 0 < len(name) <= 4096
            or PurePosixPath(name).is_absolute() or '\\' in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(part.lower() in ('', '.', '..', '.git') for part in name.split('/'))):
        raise ValueError('Use an exact repository-relative file path')
    return name


def regular_path(path: Path, *, exists=True) -> Path:
    if path != path.resolve():
        raise ValueError(f'Linked artifact path: {path}')
    try:
        info = path.lstat()
    except FileNotFoundError:
        if not exists:
            return path
        raise ValueError(f'Missing artifact file: {path}') from None
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f'Artifact path is not a regular file: {path}')
    return path


def repo_file(repo: Path, relative: str, *, exists=True) -> Path:
    return regular_path(repo.resolve() / source_path(relative), exists=exists)


def parse_pointer(data: bytes) -> tuple[str, int]:
    match = POINTER.fullmatch(data)
    if match is None:
        raise ValueError('Malformed LFS pointer')
    return match[1].decode(), int(match[2])


def declared_identity(repo: Path, relative: str) -> tuple[str, int]:
    """Read the identity declared by a canonical LFS pointer or hash an ordinary file."""
    path = repo_file(repo, relative)
    with path.open('rb') as stream:
        prefix = stream.read(1025)
        if prefix.startswith(POINTER_PREFIX):
            return parse_pointer(prefix)
        stream.seek(0)
        return hashlib.file_digest(stream, 'sha256').hexdigest(), os.fstat(stream.fileno()).st_size


def claim_identity(claim) -> tuple[str, int]:
    digest, size = claim['sha256'], claim['bytes']
    if not isinstance(digest, str) or not HEX64.fullmatch(digest) or type(size) is not int or size < 0:
        raise ValueError(f"Invalid artifact identity: {claim['path']}")
    return digest, size


def verify_bytes(raw: bytes, claim) -> bytes:
    digest, size = claim_identity(claim)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"File differs from its recorded size or SHA-256: {claim['path']}")
    return raw


def verify_payload(path: Path, claim) -> Path:
    """Verify hydrated bytes, even when an LFS pointer declares the expected identity."""
    path = regular_path(path.absolute())
    digest, size = claim_identity(claim)
    with path.open('rb') as stream:
        if stream.read(len(POINTER_PREFIX)) == POINTER_PREFIX:
            raise ValueError(f'Unresolved LFS pointer; fetch payload first: {path}')
        stream.seek(0)
        if os.fstat(stream.fileno()).st_size != size or hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
            raise ValueError(f"File differs from its recorded size or SHA-256: {claim['path']}")
    return path


def install_verified(staged: Path, destination: Path, claim, *, replace=False) -> bool:
    """Install same-volume staged bytes atomically and reuse an identical destination."""
    staged = verify_payload(staged, claim)
    destination = regular_path(destination.absolute(), exists=False)
    if staged == destination:
        return False
    if replace:
        if destination.exists():
            try:
                verify_payload(destination, claim)
            except ValueError:
                pass
            else:
                return False
        os.replace(staged, destination)
        return True
    try:
        os.link(staged, destination, follow_symlinks=False)
    except FileExistsError:
        verify_payload(destination, claim)
        return False
    return True
