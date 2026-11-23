"""Materialize the two original ED JSON exports, including in portable packages."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

EXPORTS = Path(__file__).resolve().parent / 'exports'
GEOMETRY = {'anatomy_meshes.json': 6983512, 'anatomy_details.json': 2697915}


def ensure_geometry_exports(directory=EXPORTS):
    pins = json.loads((directory / 'EXPORT_CONTRACT.json').read_text())['sha256']
    with tempfile.TemporaryDirectory(dir=directory) as scratch:
        pending = []
        for name, size in GEOMETRY.items():
            output = directory / name
            if output.resolve() != output.absolute():
                raise ValueError(f'Linked geometry export: {name}')
            if output.exists():
                check(output, size, pins[name])
                continue
            packed = output.with_suffix('.json.gz')
            if packed.resolve() != packed.absolute():
                raise ValueError(f'Linked geometry source: {name}')
            staged = Path(scratch) / name
            with gzip.open(packed, 'rb') as stream:
                staged.write_bytes(stream.read(size + 1))
            check(staged, size, pins[name])
            pending.append((staged, output, size, pins[name]))
        for staged, output, size, digest in pending:
            try:
                os.link(staged, output)
            except FileExistsError:
                check(output, size, digest)


def check(path, size, digest):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
        raise ValueError(f'Geometry export differs from its contract: {path.name}')
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
            raise ValueError(f'Geometry export differs from its contract: {path.name}')


if __name__ == '__main__':
    ensure_geometry_exports()
