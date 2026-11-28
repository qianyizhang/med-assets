"""Resolve sweep scene ports on the exact source CT grid."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


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
    case = track.get('case', 's1233')
    if case == 's1127':
        from build_thyroid import AFFINE, SHAPE

        grid = VoxelGrid(case=case, shape=SHAPE, rasMmFromVoxel=AFFINE.tolist())
    elif case == 's1233':
        from build_study import WORKSHOP

        grid = VoxelGrid.model_validate({key: WORKSHOP[key] for key in ('case', 'shape', 'rasMmFromVoxel')})
    else:
        raise ValueError(f'{track["id"]}: Unknown native CT frame {case!r}')
    slots = {entry['id'] for entry in track['parts']}
    meshes = {}
    for part, raw_ref in references.items():
        if part not in slots:
            raise ValueError(f'{track["id"]}: Unknown scene asset slot {part!r}')
        ref = SweepSceneAssetRef.model_validate(raw_ref)
        if ref.registration != 'native':
            raise ValueError(f'{track["id"]}: Expected native registration for {part}')
        export = registry.require_voxel_export(ref, grid)
        if export.format != 'mesh' or export.sha256 is None or export.bytes is None:
            raise ValueError(f'{track["id"]}: Expected an identity-pinned packed mesh for {part}')
        if scene_directory is None:
            meshes[part] = read_verified(repo, export.path, export.sha256, export.bytes)
        else:
            meshes[part] = read_verified(scene_directory, f'{part}.mesh', export.sha256, export.bytes)
    return meshes
