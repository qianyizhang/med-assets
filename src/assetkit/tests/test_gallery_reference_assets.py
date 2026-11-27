"""Check the exact native workbench and mammary recipe dependency edges."""

from pathlib import Path

from assetkit import AssetRegistry, CurationStore, DeliveryGraph
from assetkit.ultrasound import GALLERY_REFERENCE_CONFIG, read_gallery_references

REPO = Path(__file__).resolve().parents[3]
WORKBENCH = "ultrasound:recipe:gallery-reference-assets"
BREAST = "ultrasound:recipe:breast-acquisition"


def test_reference_donors_are_recipe_reads_and_mammary_has_both_readers(tmp_path: Path) -> None:
    config = read_gallery_references(REPO)
    expected = {
        "breasts_hra": ("anatomy:hra:breasts", "teaching-economy-r01", 5),
        "vagina_hra": ("anatomy:hra:vagina", "context-r02", 6),
        "ovaries": ("anatomy:hra:ovaries", "hra-ovary-tubal-r01", 4),
        "placenta": ("anatomy:hra:placenta", "hra-v1-1-r02", 6),
        "lymph_node": ("anatomy:hra:lymph-node", "tissue-color-pack-r02", 3),
        "bladder": ("anatomy:hra:bladder", "pelvic-base-r01", 8),
        "pancreas": ("anatomy:hra:pancreas", "hra-female-context-r04", 6),
        "kidney_left": ("anatomy:hra:kidney-left", "teaching-economy-r01", 2),
        "kidney_right": ("anatomy:hra:kidney-right", "teaching-economy-r01", 2),
        "diaphragm": ("anatomy:z-anatomy:diaphragm", "normal-pack-r02", 1),
    }
    assert {
        donor.slot: (donor.ref.asset, donor.ref.revision, len(donor.nodes))
        for donor in config.donors
    } == expected
    assert sum(len(donor.nodes) for donor in config.donors) == 43
    assert all(donor.ref.export == "reference" for donor in config.donors)
    records = tuple(donor.ref.record for donor in config.donors)
    for relative in (GALLERY_REFERENCE_CONFIG, *records):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO / relative).read_bytes())

    registry = AssetRegistry.load_records(tmp_path, records)
    graph = DeliveryGraph.load(tmp_path, include_legacy_adapters=False)
    curation = CurationStore()
    assert graph.validate(registry) == []
    for donor in config.donors:
        ref = donor.ref
        _, _, export = registry.require_record_export(ref)
        assert donor.nodes.keys() <= {
            selector for part in export.parts for selector in part.selectors
        }
        impact = graph.impact(f"{ref.asset}@{ref.revision}:{ref.export}", registry, curation)
        expected_readers = {WORKBENCH, BREAST} if donor == config.mammary() else {WORKBENCH}
        assert impact.found and not impact.qualifications
        assert {reader.consumer_id for reader in impact.consumers} == expected_readers
        for reader in impact.consumers:
            assert reader.owner_path == GALLERY_REFERENCE_CONFIG
            (pin,) = reader.pins
            assert pin.record == ref.record and pin.stage == "recipe"

    assert graph.bundle_for(WORKBENCH, registry).items == ()
    assert graph.bundle_for(BREAST, registry).items == ()
    assert curation.plan_r2_sync(registry, graph) == []
