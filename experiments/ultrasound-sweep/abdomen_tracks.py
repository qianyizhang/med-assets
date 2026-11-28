"""Read the abdominal sweep catalogue and resolve its governed scene meshes."""

import json
from pathlib import Path

from build_study import WORKSHOP

HERE = Path(__file__).resolve().parent


def read_tracks():
    catalogue = json.loads((HERE / 'abdomen-tracks.json').read_text())
    structures = catalogue['structures']
    tracks = []
    for row in catalogue['sweeps']:
        track = row.copy()
        styles = track.pop('partStyles', {})
        track['parts'] = [{'id': key, **structures[key], **styles.get(key, {})} for key in row['parts']]
        tracks.append(track)
    return tracks


def scene_assets(track, scene_directory=None):
    """Read exact governed meshes, or verify their staged copies before assembly."""
    references = track.get('sceneAssets', {})
    if not references:
        return {}

    from assetkit.blobs import read_verified
    from assetkit.registry import AssetRegistry, VoxelGrid
    from assetkit.ultrasound import SweepSceneAssetRef

    repo = HERE.parents[1]
    registry = AssetRegistry.load(repo, include_legacy_adapters=False)
    grid = VoxelGrid.model_validate({key: WORKSHOP[key] for key in ('case', 'shape', 'rasMmFromVoxel')})
    slots = {entry['id'] for entry in track['parts']}
    meshes = {}
    for part, raw_ref in references.items():
        if part not in slots:
            raise ValueError(f'{track["id"]}: Unknown scene asset slot {part!r}')
        export = registry.require_voxel_export(SweepSceneAssetRef.model_validate(raw_ref), grid)
        if export.format != 'mesh' or export.sha256 is None or export.bytes is None:
            raise ValueError(f'{track["id"]}: Expected an identity-pinned packed mesh for {part}')
        if scene_directory is None:
            meshes[part] = read_verified(repo, export.path, export.sha256, export.bytes)
        else:
            meshes[part] = read_verified(scene_directory, f'{part}.mesh', export.sha256, export.bytes)
    return meshes
