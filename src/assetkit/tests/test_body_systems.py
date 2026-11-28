"""Acceptance of the maintained Body Systems replay and runtime dependency paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assetkit import AssetKitError, Workspace
from assetkit import body_systems as systems

REPO = Path(__file__).resolve().parents[3]
SKELETON = "anatomy:bp3d:skeleton@source-candidate-03:skeleton"
SKIN = "anatomy:bp3d:skin@bp3d-envelope-r01:envelope"
MUSCLE = "anatomy:z-anatomy:muscle@z-anatomy-r02:muscle"
LEFT_LUNG = "anatomy:workshop:s1233-body@r1:lung-left"
RIGHT_LUNG = "anatomy:workshop:s1233-body@r1:lung-right"
BRONCHI = "anatomy:workshop:s1233-body@r1:bronchial-tree"
DIAPHRAGM = "assembly:workshop:breathing@r1:diaphragm"
VAS = "body-systems:urinary:detail:urinary-left-vesical"
CERVIX = "body-systems:reproductive:detail:reproductive-female-context"


def test_body_systems_freezes_the_plate_sources_and_indexes_only_exact_readers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_open = Path.open

    def no_local_survey(path, *args, **kwargs):
        assert ".artifacts" not in path.parts, path
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_local_survey)
    ws = Workspace.load(REPO, include_legacy_adapters=False)
    bindings, _ = systems.read_body_systems(REPO, ws.registry)
    assert len(bindings.plates) == 70
    assert sum(len(scene.views) for scene in bindings.scenes.values()) == 66
    assert len(bindings.inputs) == 21
    assert sum(source.archive is not None for source in bindings.inputs) == 12
    assert sum(source.workshop is not None for source in bindings.inputs) == 2

    replay = {
        "body-systems:skeletal:assembly:skeleton-assembly:replay": {SKELETON, SKIN},
        "body-systems:muscular:assembly:muscles-assembly:replay": {MUSCLE},
        "body-systems:respiratory:assembly:thorax-assembly:replay": {
            LEFT_LUNG,
            RIGHT_LUNG,
            BRONCHI,
            DIAPHRAGM,
        },
        "body-systems:integumentary:assembly:skin-assembly:replay": {SKIN},
    }
    actual = {c.id: c for c in ws.delivery.consumers if c.id.startswith("body-systems:")}
    assert actual.keys() == {*replay, VAS, CERVIX}
    for consumer, expected in replay.items():
        row = actual[consumer]
        assert row.owner_path == systems.REPLAY_BINDINGS
        assert {f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}" for pin in row.pins} == expected
        assert all(pin.stage == "recipe" and pin.sha256 for pin in row.pins)
        assert not ws.bundle(consumer).items
        assert ws.bundle(consumer).total_bytes == 0
        for target in expected:
            assert consumer in {reader.consumer_id for reader in ws.impact(target).consumers}

    assert actual[VAS].owner_path == actual[CERVIX].owner_path == systems.PELVIC_EXPORTS
    (bladder,) = actual[VAS].runtime_pins
    assert (bladder.asset_id, bladder.revision_id, bladder.export_id) == (
        "anatomy:hra:bladder",
        "pelvic-base-r01",
        "reference",
    )
    assert set(bladder.parts) == {
        "right-ureter",
        "left-ureter",
        "dome",
        "neck",
        "base",
        "trigone",
        "right-ureteral-orifice",
        "left-ureteral-orifice",
    }
    (vagina,) = actual[CERVIX].runtime_pins
    assert (vagina.asset_id, vagina.revision_id, vagina.export_id) == (
        "anatomy:hra:vagina",
        "teaching-context-r03",
        "teaching",
    )
    assert set(vagina.parts) == {
        "cervix",
        "vagina",
        "rectum",
        "cervicovaginal-junction",
        "bladder-dome",
        "bladder-base",
        "bladder-neck",
    }
    assert ws.bundle(VAS).total_bytes == 1_271_856
    assert ws.bundle(CERVIX).total_bytes == 1_055_764
    delivered = {item.path for item in ws.plan_r2_sync()}
    assert all(source.path not in delivered for source in bindings.inputs)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing-plate", "omit or duplicate a display plate"),
        ("switched-view", "differs from its render receipt"),
        ("switched-original", "native replay pin differs from its receipt"),
        ("wrong-archive", "archived input differs from its owning review"),
        ("missing-pelvic-pin", "export pins differ from the Gallery actions"),
        ("wrong-pelvic-revision", "differs from its selected assessment"),
        ("wrong-pelvic-part", "Unknown Body Systems pelvic selectors"),
        ("wrong-pelvic-stop", "Unknown Body Systems pelvic detail"),
    ],
)
def test_body_systems_rejects_false_reader_bindings(
    monkeypatch: pytest.MonkeyPatch, mutation: str, message: str
) -> None:
    actual = systems._json
    replay = json.loads((REPO / systems.REPLAY_BINDINGS).read_text())
    layers = json.loads((REPO / systems.PELVIC_LAYERS).read_text())
    exports = json.loads((REPO / systems.PELVIC_EXPORTS).read_text())
    pin = exports["reproductive-female-context"]
    layer = layers["reproductive-female-context"]
    if mutation == "missing-plate":
        replay["plates"].pop()
    elif mutation == "switched-view":
        replay["plates"][0]["scene"] = "muscles"
    elif mutation == "switched-original":
        source = next(
            row
            for row in replay["inputs"]
            if row.get("ref", {}).get("asset") == "anatomy:bp3d:skeleton"
        )
        source["ref"]["revision"] = "teaching-economy-r01"
    elif mutation == "wrong-archive":
        scene = replay["scenes"]["urinary"]
        wrong = replay["scenes"]["digestive"]["inputs"][0]
        scene["inputs"][0] = wrong
        replay["inputs"] = [
            row for row in replay["inputs"] if "urinary-junctions.glb" not in row["path"]
        ]
    elif mutation == "missing-pelvic-pin":
        del exports["reproductive-female-context"]
    elif mutation == "wrong-pelvic-revision":
        pin["ref"].update(revision="context-r02", export="reference")
    elif mutation == "wrong-pelvic-part":
        layer["layers"][1]["nodes"].append("VH_F_sacrum")
    elif mutation == "wrong-pelvic-stop":
        pin["system"] = "urinary"

    def read(repo, path):
        if path == systems.REPLAY_BINDINGS:
            return replay
        if path == systems.PELVIC_EXPORTS:
            return exports
        if path == systems.PELVIC_LAYERS:
            return layers
        return actual(repo, path)

    monkeypatch.setattr(systems, "_json", read)
    with pytest.raises(AssetKitError, match=message):
        systems.read_body_systems(REPO)
