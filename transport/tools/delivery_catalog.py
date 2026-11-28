"""Path bindings for immutable Anatomy Gallery delivery routes."""
from pathlib import Path

from med_assets.artifacts import source_path

DELIVERY_INDEX = Path('sites/anatomy-gallery/app/src/content/assets/delivery-index.json')


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
