"""Path bindings for immutable Anatomy Gallery delivery routes."""
from pathlib import Path, PurePosixPath

DELIVERY_INDEX = Path('sites/anatomy-gallery/app/src/content/assets/delivery-index.json')


def source_path(name: str) -> str:
    if (not isinstance(name, str) or not 0 < len(name) <= 4096
            or PurePosixPath(name).is_absolute() or '\\' in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(part.lower() in ('', '.', '..', '.git') for part in name.split('/'))):
        raise ValueError('Use an exact repository-relative file path')
    return name


def current_paths(asset: dict) -> list[str]:
    paths = asset.get('paths', [asset['path']] if asset.get('path') else [])
    if not isinstance(paths, list):
        raise ValueError('Current delivery paths must be a list')
    return paths


def assets_by_path(catalog: dict) -> dict[str, dict]:
    result = {}
    for asset in catalog['assets']:
        for path in current_paths(asset):
            source_path(path)
            if path in result:
                raise ValueError(f'Ambiguous current delivery path: {path}')
            result[path] = asset
    return result
