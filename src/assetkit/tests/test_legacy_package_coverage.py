"""Legacy discovery keeps unported paths visible beside canonical package exports."""

import json
from pathlib import Path

from assetkit import ShowAssetResult, UnknownTargetResult, Workspace


def test_legacy_projection_excludes_exact_native_exports_and_keeps_other_paths(tmp_path: Path):
    parent = "models/study"
    child = f"{parent}/child"
    owned = f"{parent}/owned.glb"
    nested_owned = f"{child}/owned.glb"
    legacy = f"{parent}/retained.glb"
    for path in (owned, nested_owned, legacy):
        file = tmp_path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"fixture")
    (tmp_path / parent / "linked.glb").symlink_to(tmp_path / nested_owned)

    for owner, name, payload in ((parent, "parent", owned), (child, "child", nested_owned)):
        record = {
            "schemaVersion": 1,
            "assetId": f"anatomy:fixture:{name}",
            "status": "provisional",
            "owner": owner,
            "sources": [{"sourceId": "base", "path": legacy}],
            "exports": [{"path": legacy}],
            "revisions": [
                {
                    "revisionId": "r01",
                    "status": "provisional",
                    "sourceIds": ["base"],
                    "exports": [{"id": "main", "path": payload}],
                }
            ],
        }
        (tmp_path / owner / "asset.record.json").write_text(json.dumps(record))

    workspace = Workspace.load(tmp_path)
    legacy_view = workspace.show(legacy)
    assert isinstance(legacy_view, ShowAssetResult)
    assert legacy_view.asset.status == "legacy-candidate"
    assert legacy_view.asset.source_manifest is None
    assert {export.path for revision in legacy_view.revisions for export in revision.exports} == {
        legacy
    }
    parent_view = workspace.show(parent)
    assert isinstance(parent_view, ShowAssetResult)
    assert parent_view.asset.id == "anatomy:fixture:parent"
    assert workspace.impact(owned).matched_assets == ("anatomy:fixture:parent",)
    assert workspace.impact(nested_owned).matched_assets == ("anatomy:fixture:child",)
    assert isinstance(workspace.show(f"{parent}/linked.glb"), UnknownTargetResult)
    assert workspace.impact(parent).matched_assets == ("anatomy:fixture:parent", "study")
    assert {item.status for item in workspace.find("study").assets} == {
        "provisional",
        "legacy-candidate",
    }

    native_workspace = Workspace.load(tmp_path, include_legacy_adapters=False)
    assert isinstance(native_workspace.show(legacy), UnknownTargetResult)
    assert native_workspace.impact(nested_owned).matched_assets == ("anatomy:fixture:child",)


def test_retained_anatomy_paths_remain_discoverable_alongside_native_owners():
    root = Path(__file__).resolve().parents[3]
    workspace = Workspace.load(root)
    retained = {
        "models/liver/exports/metadata-cleanup-r01/liver.glb",
        "models/liver/exports/hra-female-v1.10-r02/liver.glb",
    }
    for path in retained:
        view = workspace.show(path)
        assert isinstance(view, ShowAssetResult)
        assert view.asset.status == "legacy-candidate"
        assert workspace.impact(path).matched_export_paths == (path,)

    original_skeleton = "models/skeleton/exports/source-candidate-03/skeleton_source_frame.glb"
    skeleton_view = workspace.show(original_skeleton)
    assert isinstance(skeleton_view, ShowAssetResult)
    assert skeleton_view.asset.source_manifest == "models/skeleton/asset.record.json"
    skeleton_impact = workspace.impact("anatomy:bp3d:skeleton@source-candidate-03:skeleton")
    assert skeleton_impact.matched_export_paths == (original_skeleton,)

    skin_owners = {
        "models/skin/exports/teaching-economy-r01/skin_source_frame.glb": "models/skin/asset.record.json",
        "models/skin/nail-study-r02/nail.glb": "models/skin/nail-study-r02/asset.record.json",
    }
    for path, owner in skin_owners.items():
        view = workspace.show(path)
        assert isinstance(view, ShowAssetResult)
        assert view.asset.source_manifest == owner
        assert workspace.impact(path).matched_export_paths == (path,)

    selected = {selection.export_path: selection for selection in workspace.curation.selections}
    r2_paths = {item.path for item in workspace.plan_r2_sync()}
    expected_defaults = {
        "models/skin/exports/teaching-economy-r01/skin_source_frame.glb",
        "models/skin/nail-study-r02/nail.glb",
        "models/skeleton/exports/teaching-economy-r01/skeleton_source_frame.glb",
    }
    assert expected_defaults <= selected.keys()
    assert expected_defaults <= r2_paths
