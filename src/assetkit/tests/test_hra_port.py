"""Wave 0 acceptance for the real HRA liver package and its existing readers."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from med_assets.teaching import ASSESSMENTS, SELECTIONS, CurrentTeaching
from typer.testing import CliRunner, Result

from assetkit import AssetKitError, Workspace, inspect_mesh, verify
from assetkit.cli import app
from assetkit.registry import ExportRef, VoxelGrid

REPO = Path(__file__).resolve().parents[3]
ASSET = "anatomy:hra:liver"
KEY = f"{ASSET}@r02:teaching-economy"
RECORD = "models/liver/asset.record.json"
RECIPE = "models/liver/recipes/teaching-economy-r02.json"
SOURCE = "models/liver/exports/hra-female-v1.10-r02/liver.glb"
EXPORT = "models/liver/exports/teaching-economy-r02/liver.glb"
REPLAY = "assemblies/liver-spleen/recipes/README.md"
ASSESSMENT_OWNER = "reviews/teaching-assessments/reopen-economy/decisions.json"
DIGEST = "5978654a1e5b8ac608735dde82434e3fe67c1e1883930c4fa1b60d53fe85dd7d"
ASSESSMENT_DIGEST = "e134036837b6e3664a5f3fe10f5ad529261a9414d7022869b118b3ab5f784e54"
SIZE = 595_352
EXPORT_PIN = {"path": EXPORT, "sha256": DIGEST, "bytes": SIZE}
TRIANGLES = 41_470
SELECTORS = (
    "VH_F_capsule_of_the_liver",
    "VH_F_bare_area_of_liver",
    "VH_F_coronary_ligament_of_liver",
    "VH_F_falciform_ligament",
    "VH_F_triangular_ligament_of_liver",
    "VH_F_ligamentum_venosum",
    "VH_F_round_ligament_of_liver",
    "VH_F_hepataduodenal_ligament",
)


def _check_port(repo: Path, key: str = KEY, *, allow_pointer: bool = True) -> Result:
    options = [
        "--repo",
        str(repo),
        "check-port",
        key,
        "--record",
        RECORD,
        "--path",
        EXPORT,
        "--sha256",
        DIGEST,
        "--bytes",
        str(SIZE),
        "--triangles",
        str(TRIANGLES),
    ]
    if allow_pointer:
        options.append("--allow-lfs-pointer")
    for selector in SELECTORS:
        options.extend(("--selector", selector))
    return CliRunner().invoke(app, options)


def test_native_owner_exact_export_and_source_replay_pin() -> None:
    result = CliRunner().invoke(app, ["--repo", str(REPO), "--native-only", "show", KEY])
    assert result.exit_code == 0, result.output
    shown = json.loads(result.output)
    assert shown["found"] is True
    assert shown["asset"]["id"] == ASSET
    assert shown["asset"]["sourceManifest"] == RECORD
    assert shown["asset"]["status"] == "provisional"
    assert not shown["tasks"]
    assert not shown["qualifications"]
    (revision,) = shown["revisions"]
    assert revision["id"] == "r02"
    assert revision["status"] == "provisional"
    assert revision["provenance"]["source"] == SOURCE
    assert revision["provenance"]["subject"] == "HRA female v1.10 reference atlas"
    assert revision["provenance"]["license"] == "CC-BY-4.0"
    assert revision["provenance"]["registration"] == "native"
    assert "s1233" in " ".join(shown["asset"]["unresolved"])
    assert (REPO / "models/liver" / revision["recipe"]) == REPO / RECIPE
    (export,) = revision["exports"]
    assert export["id"] == "teaching-economy"
    assert {field: export[field] for field in EXPORT_PIN} == EXPORT_PIN
    assert export["storageStatus"] in {"verified", "pointer-match"}
    assert export["triangles"] == TRIANGLES
    assert revision["frame"] == export["frame"]
    assert export["frame"]["convention"] == "glb-y-up-m"
    assert export["frame"]["units"] == "m"
    assert export["frame"]["axes"] == ["right-handed", "Y-up"]
    assert {s for part in export["parts"] for s in part["selectors"]} == set(SELECTORS)

    recipe = json.loads((REPO / RECIPE).read_text())
    record = json.loads((REPO / RECORD).read_text())
    (source,) = record["sources"]
    assert {field: source[field] for field in recipe["source"]} == recipe["source"]
    assert recipe["source"]["path"] == SOURCE
    assert recipe["output"] == EXPORT_PIN
    source_identity = verify(REPO, SOURCE, source["sha256"], source["bytes"])
    assert source_identity.status in {"verified", "pointer-match"}
    replay = record["revisions"][0]["recipeEvidence"]
    assert replay["path"] == REPLAY
    assert verify(REPO, REPLAY, replay["sha256"]).status == "verified"

    checked = _check_port(REPO)
    assert checked.exit_code == 0, checked.output
    receipt = json.loads(checked.output)
    assert receipt["found"] is True
    assert receipt["record"] == RECORD
    assert receipt["identity"]["status"] == export["storageStatus"]
    if export["storageStatus"] == "verified":
        assert receipt["mesh"]["triangles"] == TRIANGLES
        assert set(receipt["mesh"]["nodeTriangles"]) == set(SELECTORS)
    else:
        assert "mesh" not in receipt


def test_owned_selection_round_trip_and_s1233_placement_rejection() -> None:
    current = CurrentTeaching(REPO)
    selection, assessment = next((s, a) for s, a in current.selected() if s.path == EXPORT)
    assert selection.task_id == assessment.task_id == "liver"
    assert selection.assessment_sha256 == assessment.sha256 == ASSESSMENT_DIGEST
    assert assessment.owner.relative_to(REPO).as_posix() == ASSESSMENT_OWNER
    assert assessment.row["export"] == EXPORT_PIN
    assert assessment.row["task"] == (
        "Find the posterior bare area relative to the anterior surface of the HRA liver."
    )
    assert assessment.row["target"]["status"] == "passed"

    ws = Workspace.load(REPO)
    impact = ws.impact(KEY)
    assert impact.found
    assert impact.matched_assets == (ASSET,)
    assert impact.matched_export_paths == (EXPORT,)
    assert not impact.consumers
    assert not impact.adoptions
    assert not impact.qualifications
    (indexed_selection,) = impact.selections
    assert indexed_selection.owner_path == SELECTIONS
    assert indexed_selection.export_path == EXPORT
    assert indexed_selection.task_id == selection.task_id
    assert indexed_selection.review_id == assessment.sha256
    (review,) = impact.reviews
    assert review.id == assessment.sha256
    assert review.sha256 == DIGEST

    s1233 = ws.impact("anatomy:s1233:liver-window@r01:liver")
    (sweep,) = s1233.consumers
    assert sweep.consumer_id == "ultrasound:sweep:abdomen-tracks:liver"
    assert sweep.owner_path == "experiments/ultrasound-sweep/abdomen-tracks.json"
    grid_source = json.loads((REPO / "assemblies/workshop-s1233/inputs.json").read_text())
    grid = VoxelGrid.model_validate(
        {field: grid_source[field] for field in ("case", "shape", "rasMmFromVoxel")}
    )
    with pytest.raises(AssetKitError, match="Incompatible coordinate convention"):
        ws.registry.require_voxel_export(
            ExportRef(asset=ASSET, revision="r02", export="teaching-economy"), grid
        )


def test_hydrated_replay_matches_exact_export(tmp_path: Path) -> None:
    recipe = json.loads((REPO / RECIPE).read_text())
    source = recipe["source"]
    identities = (
        verify(REPO, SOURCE, source["sha256"], source["bytes"]),
        verify(REPO, EXPORT, DIGEST, SIZE),
    )
    statuses = {identity.status for identity in identities}
    assert statuses <= {"verified", "pointer-match"}
    if "pointer-match" in statuses:
        pytest.skip("Hydrated HRA GLBs are required for geometry inspection and replay")

    output = tmp_path / "replay"
    result = subprocess.run(
        [sys.executable, "tools/rebuild_asset.py", RECIPE, str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (output / "liver.glb").read_bytes() == (REPO / EXPORT).read_bytes()
    mesh = inspect_mesh(output, "liver.glb")
    assert mesh is not None
    assert mesh.triangles == TRIANGLES
    assert set(mesh.node_triangles) == set(SELECTORS)


@pytest.mark.parametrize("replacement", [{"path": SOURCE}, {"assessmentSha256": "a" * 64}])
def test_owned_register_rejects_wrong_assessment_pin(replacement: dict[str, str]) -> None:
    register = json.loads((REPO / SELECTIONS).read_text())
    catalog = json.loads((REPO / ASSESSMENTS).read_text())
    selected = next(
        row
        for collection in register["collections"]
        for family in collection["families"]
        for row in family["exports"]
        if row["path"] == EXPORT
    )
    selected.update(replacement)
    current = CurrentTeaching(REPO, register=register, catalog=catalog)
    with pytest.raises(ValueError, match="Stale maintained assessment pin"):
        list(current.selected())


def test_checked_in_record_sync_is_already_current() -> None:
    record = REPO / RECORD
    before = record.read_bytes()
    result = CliRunner().invoke(app, ["--repo", str(REPO), "sync", RECORD])
    assert result.exit_code == 0, result.output
    sync = json.loads(result.output)
    assert not sync["applied"]
    assert not sync["updatedExports"]
    assert record.read_bytes() == before


@pytest.fixture
def hra_copy(tmp_path: Path) -> Path:
    shutil.copytree(REPO / "models/liver", tmp_path / "models/liver")
    for relative in (
        REPLAY,
        "sources/datasets/hra/united-female-v1.10/external-source.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    return tmp_path


def test_pointer_corroborates_identity_without_hydrated_acceptance(hra_copy: Path) -> None:
    (hra_copy / EXPORT).write_text(
        f"version https://git-lfs.github.com/spec/v1\noid sha256:{DIGEST}\nsize {SIZE}\n"
    )
    offline = _check_port(hra_copy)
    assert offline.exit_code == 0, offline.output
    receipt = json.loads(offline.output)
    assert receipt["identity"]["status"] == "pointer-match"
    assert "mesh" not in receipt
    hydrated = _check_port(hra_copy, allow_pointer=False)
    assert hydrated.exit_code == 2, hydrated.output
    assert "Hydrated bytes required" in hydrated.output


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("missing-record", "Missing canonical owner record"),
        ("wrong-export", "Native owner does not match"),
        ("wrong-selector", "Missing required selectors"),
        ("missing-payload", "missing"),
        ("changed-payload", "Conflicting SHA-256 or byte count"),
        ("missing-replay", REPLAY),
    ],
)
def test_check_port_rejects_drift(hra_copy: Path, change: str, message: str) -> None:
    record = hra_copy / RECORD
    export = hra_copy / EXPORT
    key = KEY
    if change == "missing-record":
        record.unlink()
    elif change == "wrong-export":
        key = f"{ASSET}@r02:hra-female-v1-10"
    elif change == "wrong-selector":
        changed = json.loads(record.read_text())
        bare_area = next(part for part in changed["parts"] if part["partId"] == "bare-area")
        bare_area["selectors"] = ["Liver"]
        record.write_text(json.dumps(changed))
    elif change == "missing-payload":
        export.unlink()
    elif change == "changed-payload":
        export.write_bytes(b"changed payload")
    elif change == "missing-replay":
        (hra_copy / REPLAY).unlink()

    result = _check_port(hra_copy, key)
    assert result.exit_code == 2, result.output
    assert message in result.output
