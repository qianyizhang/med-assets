"""Verify the exact ultrasound recipe pins without requiring hydrated geometry."""

from pathlib import Path

import pytest

from assetkit import AssetKitError, AssetRegistry, CurationStore, DeliveryGraph
from assetkit.ultrasound import EXTERIOR_ATLAS_CONFIG, read_exterior_atlas

REPO = Path(__file__).resolve().parents[3]
READER = "ultrasound:recipe:exterior-atlas"
EXPECTED = (
    ("anatomy:bp3d:skin", "bp3d-envelope-r01", "envelope", "models/skin/asset.record.json"),
    (
        "anatomy:bp3d:skeleton",
        "teaching-economy-r01",
        "skeleton",
        "models/skeleton/asset.record.json",
    ),
)


def test_exterior_pins_are_exact_recipe_readers_without_runtime_cost(tmp_path: Path) -> None:
    atlas = read_exterior_atlas(REPO)
    assert (
        tuple((ref.asset, ref.revision, ref.export, ref.record) for ref in atlas.inputs())
        == EXPECTED
    )
    for relative in (EXTERIOR_ATLAS_CONFIG, *(ref.record for ref in atlas.inputs())):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO / relative).read_bytes())

    registry = AssetRegistry.load_records(tmp_path, (ref.record for ref in atlas.inputs()))
    graph = DeliveryGraph.load(tmp_path, include_legacy_adapters=False)
    curation = CurationStore()
    assert graph.validate(registry) == []
    for ref in atlas.inputs():
        key = f"{ref.asset}@{ref.revision}:{ref.export}"
        impact = graph.impact(key, registry, curation)
        asset, _, export = registry.require_record_export(ref)
        assert export.storage_status == "unverified"
        assert asset.source_manifest == ref.record
        assert impact.found and not impact.qualifications
        (reader,) = impact.consumers
        assert reader.consumer_id == READER
        assert reader.owner_path == EXTERIOR_ATLAS_CONFIG
        (pin,) = reader.pins
        assert (pin.asset_id, pin.revision_id, pin.export_id) == (
            ref.asset,
            ref.revision,
            ref.export,
        )
        assert pin.record == ref.record
        assert pin.stage == "recipe"
    assert graph.bundle_for(READER, registry).items == ()
    (costs,) = graph.economy(registry).consumer_metrics
    assert (costs.loads, costs.total_bytes, costs.total_triangles) == (0, 0, 0)
    assert curation.plan_r2_sync(registry, graph) == []

    unrelated = tmp_path / "unrelated/asset.record.json"
    unrelated.parent.mkdir()
    unrelated.write_text("broken JSON")
    assert AssetRegistry.load_records(tmp_path, (ref.record for ref in atlas.inputs())) == registry
    wrong_record = atlas.skin.model_copy(update={"record": atlas.skeleton.record})
    with pytest.raises(AssetKitError, match="outside its declared record"):
        registry.require_record_export(wrong_record)
