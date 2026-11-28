"""Candidate Gallery compiler and native reverse reader acceptance."""

from __future__ import annotations

import importlib.util
import json
import mimetypes
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

import pytest
from med_assets.teaching import CurrentTeaching

from assetkit import AssetKitError, Workspace
from assetkit import gallery as gate

REPO = Path(__file__).resolve().parents[3]
SITE = REPO / "sites/anatomy-gallery"
LIVER = "models/liver/exports/teaching-economy-r02/liver.glb"
LIVER_SOURCE = "models/liver/exports/hra-female-v1.10-r02/liver.glb"
LIVER_ROUTE = "library/liver/teaching-economy-r02"
TERMINAL = "lessons/one-breath/terminal-study-r02/terminal-airspaces.glb"
DENTAL_TOOL = "dental-review/cotton-tweezers-r04/cotton-tweezers.glb"
FITTED_HEART = "body/3d/assets/motion/heart_animated_clinical.glb"


def _read(path: Path):
    return json.loads(path.read_text())


def test_gallery_admission_indexes_exact_catalog_routes_without_runtime_weight() -> None:
    workspace = Workspace.load(REPO, include_legacy_adapters=False)
    admission = gate.read_library_admission(REPO, workspace.registry)
    current = CurrentTeaching(REPO)
    assert all(admission.paths[selection.path].ref for selection, _ in current.selected())
    for path, kind in (
        (LIVER_SOURCE, "replay-only"),
        (DENTAL_TOOL, "external"),
        (FITTED_HEART, "unavailable"),
    ):
        disposition = admission.paths[path].disposition
        assert disposition and disposition.kind == kind

    readers = {
        reader.consumer_id
        for reader in workspace.impact("anatomy:hra:liver@r02:teaching-economy").consumers
    }
    assert readers == {f"gallery:candidate:{LIVER_ROUTE}"}
    assert workspace.impact(LIVER_SOURCE).status == "unknown-target"
    reader_id = "gallery:candidate:library/terminal-airspaces-r02"
    readers = workspace.impact(TERMINAL).consumers
    assert [(r.consumer_id, r.pins[0].record) for r in readers] == [
        (reader_id, "lessons/one-breath/terminal-study-r02/asset.record.json")
    ]
    catalog = [row for row in workspace.delivery.consumers if row.owner_path == gate.ADMISSION]
    assert len(catalog) == len(
        {reader.route for row in admission.paths.values() if row.ref for reader in row.readers}
    )
    assert all(pin.stage == "catalog" for row in catalog for pin in row.pins)
    assert all(workspace.bundle(row.id).total_bytes == 0 for row in catalog)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("remove", "Missing Gallery Library admission"),
        ("ref", "Gallery package ref differs"),
        ("historical", "requires an exact package ref"),
        ("replay", "differs from its package source"),
        ("external", "external delivery differs"),
        ("unavailable", "identity or availability differs"),
        ("selection", "differs from its maintained task"),
    ],
)
def test_gallery_compiler_gate_rejects_false_claims(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    path = REPO / gate.ADMISSION
    document = _read(path)
    paths = document["paths"]
    files = [
        {
            "path": item,
            "reader": reader,
            "sha256": row["sha256"],
            "bytes": row["bytes"],
            "unavailable": row.get("unavailable"),
        }
        for item, row in paths.items()
        for reader in row["readers"]
    ]
    selections = [
        {
            **assessment.row["export"],
            "taskId": selection.task_id,
            "familyId": selection.family_id,
            "collection": selection.collection,
        }
        for selection, assessment in CurrentTeaching(REPO).selected()
    ]
    if mutation == "remove":
        del paths[LIVER]
    elif mutation == "ref":
        paths[LIVER]["ref"] = paths[TERMINAL]["ref"]
    elif mutation == "historical":
        paths[LIVER]["disposition"] = paths[LIVER_SOURCE]["disposition"]
        del paths[LIVER]["ref"]
    elif mutation == "replay":
        paths[LIVER_SOURCE]["disposition"]["evidence"] = "models/diaphragm/asset.record.json"
    elif mutation == "external":
        paths[DENTAL_TOOL]["disposition"]["evidence"] = path.relative_to(REPO).as_posix()
    elif mutation == "unavailable":
        next(file for file in files if file["path"] == FITTED_HEART)["unavailable"] = None
    elif mutation == "selection":
        next(row for row in selections if row["path"] == LIVER)["taskId"] = (
            "terminal-airspace-study"
        )
    original = gate._document
    monkeypatch.setattr(
        gate,
        "_document",
        lambda repo, name: document if name == gate.ADMISSION else original(repo, name),
    )
    compiled = gate.CompiledLibrary.model_validate({"files": files, "selections": selections})
    with pytest.raises(AssetKitError, match=message):
        gate.check_compiled_library(REPO, compiled)


def _stage_compiler_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    tools = SITE / "tools"
    monkeypatch.syspath_prepend(str(REPO))
    monkeypatch.syspath_prepend(str(tools))
    spec = importlib.util.spec_from_file_location("gallery_runtime", tools / "gallery_runtime.py")
    assert spec is not None and spec.loader is not None
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)

    def pointer_safe_campaign(repo: Path, _index: Path) -> list[dict]:
        # The review store verifies declared LFS identities in shallow CI. The normal
        # bootstrap additionally verifies hydrated image bytes before writing these URLs.
        current = CurrentTeaching(repo)
        campaign = []
        for accepted in current.gallery():
            row = {**accepted.row, **accepted.attribution, "taskId": accepted.task_id}
            row["views"] = [
                {
                    **view,
                    "mediaType": mimetypes.guess_type(view["path"])[0],
                    "url": f"/review-evidence/{view['sha256']}/{quote(Path(view['path']).name)}",
                }
                for view in row["views"]
            ]
            if selection := current.selections.get(row["export"]["path"]):
                maintained = {
                    "collection": selection.collection,
                    "family": selection.family,
                    "familyId": selection.family_id,
                    "taskId": selection.task_id,
                }
                if selection.shared_owner:
                    maintained.update(label=selection.label, sharedOwner=selection.shared_owner)
                row["maintained"] = maintained
            campaign.append(row)
        return campaign

    monkeypatch.setattr(runtime, "prepare_campaign_reviews", pointer_safe_campaign)
    project = tmp_path / "project"
    content = project / "src/content"
    shutil.copytree(SITE / "app/src/content", content)
    runtime.prepare_library_inputs(
        REPO,
        content / "assets/delivery-index.json",
        content / "gallery/teaching-inputs",
    )
    return project


def test_real_compiler_requires_fresh_admission_and_plans_new_revision_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = shutil.which("node")
    if not node or not shutil.which("uv"):
        pytest.skip("Candidate compiler needs Node 24 and uv")
    project = _stage_compiler_inputs(tmp_path, monkeypatch)
    content = project / "src/content/gallery"
    command = [
        node,
        str(SITE / "tools/compile_library.mjs"),
        str(project),
        "candidate",
        "test",
        "--offline",
    ]

    def compile_candidate(*args: str):
        return subprocess.run([*command, *args], cwd=REPO, capture_output=True, text=True)

    before = (REPO / gate.ADMISSION).read_bytes()
    result = compile_candidate()
    assert result.returncode == 0, result.stderr
    compiled = content / "selected-library.json"
    previous = compiled.read_bytes()
    current = _read(compiled)
    liver = next(row for row in current["rows"] if row["id"] == "liver")
    assert liver["recommended"] == LIVER_ROUTE
    assert any(
        item["path"] == FITTED_HEART and item["unavailable"]
        for row in current["rows"]
        for version in row["history"]
        for item in version["exports"]
    )

    editions = content / "library-editions.json"
    declarations = _read(editions)
    new_route = "library/liver/refreshed-edition"
    declarations[LIVER] = new_route
    editions.write_text(json.dumps(declarations))
    result = compile_candidate()
    assert result.returncode != 0
    assert "Compiled Gallery Library reader routes or roles differ" in result.stderr
    assert compiled.read_bytes() == previous

    result = compile_candidate(str(content / "teaching-inputs"))
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    prior_paths = json.loads(before)["paths"]
    assert plan["paths"][LIVER]["ref"] == prior_paths[LIVER]["ref"]
    assert {reader["route"] for reader in plan["paths"][LIVER]["readers"]} == {new_route}
    assert plan["paths"][LIVER_SOURCE]["disposition"] == prior_paths[LIVER_SOURCE]["disposition"]
    assert (REPO / gate.ADMISSION).read_bytes() == before
    assert compiled.read_bytes() == previous

    packages = content / "library-packages.json"
    declarations = _read(packages)
    row = next(item for item in declarations["packages"] if item["id"] == "liver")
    next(item for item in row["media"] if item["path"] == LIVER_SOURCE)["bytes"] += 1
    packages.write_text(json.dumps(declarations))
    result = compile_candidate(str(content / "teaching-inputs"))
    assert result.returncode != 0
    assert LIVER_SOURCE in result.stderr
    assert compiled.read_bytes() == previous
