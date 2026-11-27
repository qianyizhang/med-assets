"""Idiomatic pytest suite for AssetKit's 6 bounded contexts."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from assetkit import (
    Adoption,
    Asset,
    AssetKitError,
    AssetRegistry,
    BudgetPolicy,
    BuildSpec,
    Concept,
    ConceptEdge,
    ConceptGraph,
    Consumer,
    CurationStore,
    DeliveryGraph,
    Export,
    Part,
    Pin,
    Provenance,
    Qualification,
    Requirement,
    Review,
    Revision,
    Selection,
    ShowAssetResult,
    UnknownTargetResult,
    Workspace,
    inspect_mesh,
    plan_build,
    run_build,
    sync_manifest,
    verify,
)
from assetkit.cli import app


def _make_minimal_glb(node_name: str = "LiverMesh", triangles: int = 2) -> bytes:
    """Construct a valid minimal GLB v2 binary with 1 mesh and known triangle count."""
    doc = {
        "asset": {"version": "2.0"},
        "nodes": [{"name": node_name, "mesh": 0}],
        "meshes": [{"primitives": [{"mode": 4, "indices": 0}]}],
        "accessors": [{"count": triangles * 3, "componentType": 5123, "type": "SCALAR"}],
    }
    json_bytes = json.dumps(doc).encode("utf-8")
    json_bytes += b" " * ((4 - (len(json_bytes) % 4)) % 4)
    total_len = 12 + 8 + len(json_bytes)
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    chunk_header = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    return header + chunk_header + json_bytes


class _FakeRunner:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.commands: list[tuple[str, ...]] = []

    def run(self, repo: Path, spec: BuildSpec) -> tuple[int, str, str]:
        self.commands.append(spec.command)
        for out in spec.expected_outputs:
            target = repo / out
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.payload)
        return 0, "built ok", ""


def test_vocab_polyhierarchy_and_cycle_rejection() -> None:
    graph = ConceptGraph(
        concepts=(
            Concept(id="skeletal-system", label="Skeletal system"),
            Concept(id="vertebral-column", label="Vertebral column"),
            Concept(id="L3-vertebra", label="L3 vertebra"),
            Concept(id="bone-marrow", label="Bone marrow"),
            Concept(id="blood-cell", label="Blood cell"),
            Concept(id="immune-response", label="Immune response"),
        ),
        edges=(
            ConceptEdge(subject="vertebral-column", predicate="part_of", object="skeletal-system"),
            ConceptEdge(subject="L3-vertebra", predicate="part_of", object="vertebral-column"),
            ConceptEdge(subject="bone-marrow", predicate="located_in", object="L3-vertebra"),
            ConceptEdge(subject="bone-marrow", predicate="produces", object="blood-cell"),
            ConceptEdge(
                subject="bone-marrow", predicate="participates_in", object="immune-response"
            ),
        ),
    )
    graph.validate()
    assert graph.ancestors("L3-vertebra") == {"vertebral-column", "skeletal-system"}
    assert graph.expand(("skeletal-system",)) == {
        "skeletal-system",
        "vertebral-column",
        "L3-vertebra",
    }
    assert len(graph.related("bone-marrow", "produces")) == 1

    cyclic = ConceptGraph(
        concepts=(Concept(id="a", label="A"), Concept(id="b", label="B")),
        edges=(
            ConceptEdge(subject="a", predicate="part_of", object="b"),
            ConceptEdge(subject="b", predicate="part_of", object="a"),
        ),
    )
    with pytest.raises(AssetKitError, match="Cycle"):
        cyclic.validate()


def test_hybrid_registry_delivery_bundle_and_resolution() -> None:
    liver = Asset(
        id="liver-s1233",
        title="Liver (s1233 + pathology layers)",
        kind="model",
        owner_dir="models/liver",
        concepts=("liver",),
        revisions=(
            Revision(
                id="r03",
                status="active",
                provenance=Provenance(
                    source="TotalSegmentator",
                    subject="s1233",
                    license="CC-BY-4.0",
                    registration="native",
                ),
                exports=(
                    Export(
                        id="surface",
                        path="models/liver/exports/r03/liver-surface.glb",
                        format="glb",
                        bytes=300_000,
                        triangles=12_000,
                        parts=(
                            Part(
                                id="outer-surface",
                                label="Liver exterior",
                                selectors=("liver",),
                                concepts=("liver",),
                                bytes=300_000,
                            ),
                        ),
                    ),
                    Export(
                        id="lesion-overlay",
                        path="models/liver/exports/r03/liver-lesion-01.glb",
                        format="glb",
                        variant="focal-lesion",
                        bytes=80_000,
                        triangles=2_500,
                        parts=(
                            Part(
                                id="focal-lesion",
                                label="Hyperechoic focal lesion",
                                selectors=("focal-lesion",),
                                concepts=("focal-lesion",),
                                bytes=80_000,
                                provenance=Provenance(
                                    source="authored-pathology-v1",
                                    subject="synthetic",
                                    registration="illustrative",
                                    limits=("Illustrative mass placement for ultrasound",),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    vocab = ConceptGraph(
        concepts=(
            Concept(id="liver", label="Liver"),
            Concept(id="focal-lesion", label="Focal lesion"),
        )
    )
    registry = AssetRegistry(assets=(liver,))
    delivery = DeliveryGraph(
        consumers=(
            Consumer(
                id="us:abdomen:focal-lesion",
                title="Abdominal focal lesion sweep",
                kind="ultrasound-sweep",
                owner_path="experiments/ultrasound-sweep/consumer.json",
                requirements=(
                    Requirement(
                        id="req-liver",
                        description="Liver parenchyma",
                        status="satisfied",
                        concepts=("liver",),
                        subject="s1233",
                    ),
                    Requirement(
                        id="req-lesion",
                        description="Focal lesion overlay",
                        status="satisfied",
                        concepts=("focal-lesion",),
                        variant="focal-lesion",
                    ),
                    Requirement(
                        id="req-caval",
                        description="Hepatic vein IVC junction",
                        status="open-gap",
                        concepts=("hepatic-vein",),
                        subject="s1233",
                    ),
                ),
                pins=(
                    Pin(
                        asset_id="liver-s1233",
                        revision_id="r03",
                        export_id="surface",
                        requirement_id="req-liver",
                        parts=("outer-surface",),
                        registration="native",
                    ),
                    Pin(
                        asset_id="liver-s1233",
                        revision_id="r03",
                        export_id="lesion-overlay",
                        requirement_id="req-lesion",
                        parts=("focal-lesion",),
                        registration="illustrative",
                    ),
                ),
            ),
        )
    )
    curation = CurationStore()
    assert registry.validate(vocab) == []
    assert delivery.validate(registry) == []

    bundle = delivery.bundle_for("us:abdomen:focal-lesion", registry)
    assert len(bundle.items) == 2
    assert bundle.total_bytes == 380_000
    assert len(bundle.open_gaps) == 1
    assert len(delivery.open_gaps("us:")) == 1

    resolved = delivery.resolve("us:abdomen:focal-lesion", registry, vocab, curation, "req-lesion")
    cand = resolved.requirements[0].concept_candidates[0]
    assert cand.registration == "illustrative"
    assert cand.subject == "synthetic"
    assert cand.qualified is False


def test_delivery_economy_detects_bloat_and_low_utilization() -> None:
    bloated = Asset(
        id="liver-monolith",
        title="Liver Monolith",
        kind="model",
        owner_dir="models/liver",
        revisions=(
            Revision(
                id="r01",
                status="active",
                exports=(
                    Export(
                        id="everything",
                        path="models/liver/everything.glb",
                        format="glb",
                        bytes=5_000_000,
                        triangles=180_000,
                        parts=(
                            Part(id="outer", label="Outer", bytes=500_000),
                            Part(id="portal", label="Portal", bytes=1_500_000),
                            Part(id="hepatic", label="Hepatic", bytes=1_500_000),
                            Part(id="biliary", label="Biliary", bytes=1_500_000),
                        ),
                    ),
                ),
            ),
        ),
    )
    registry = AssetRegistry(assets=(bloated,))
    delivery = DeliveryGraph(
        consumers=(
            Consumer(
                id="body-systems:liver-overview",
                title="Body Systems Liver Overview",
                kind="lesson-stop",
                owner_path="lessons/body-systems/consumer.json",
                pins=(
                    Pin(
                        asset_id="liver-monolith",
                        revision_id="r01",
                        export_id="everything",
                        parts=("outer",),
                    ),
                ),
            ),
        )
    )
    report = delivery.economy(registry, BudgetPolicy())
    m = report.consumer_metrics[0]
    assert m.loads == 1
    assert m.part_utilization == 0.25
    assert m.byte_utilization == 0.1
    assert "low-part-utilization" in m.budget_flags
    assert "low-byte-utilization" in m.budget_flags
    actions = {r.action for r in report.recommendations}
    assert {"split-export", "over-budget"} <= actions


def test_build_runner_and_sync_manifest_end_to_end(tmp_path: Path) -> None:
    (tmp_path / "models/liver/recipes").mkdir(parents=True)
    (tmp_path / "models/liver/recipes/build.py").write_text("import bpy\n", encoding="utf-8")
    (tmp_path / "models/liver/assets.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "assets": [
                    {
                        "id": "liver",
                        "title": "Liver",
                        "kind": "model",
                        "revisions": [
                            {
                                "id": "r03",
                                "status": "provisional",
                                "recipe": "recipes/build.py",
                                "exports": [{"id": "mesh", "path": "exports/r03/liver.glb"}],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    ws = Workspace.load(tmp_path, include_legacy_adapters=False)
    spec = plan_build(tmp_path, ws.registry, "liver", "r03")
    assert spec.command[0] == "blender"

    dry = run_build(tmp_path, spec, apply=False)
    assert dry.status == "planned"

    glb_bytes = _make_minimal_glb("Liver_Outer", triangles=16)
    runner = _FakeRunner(glb_bytes)
    built = run_build(tmp_path, spec, apply=True, runner=runner)
    assert built.status == "built"
    assert built.verified_outputs[0].triangles == 16

    # A recipe may exit normally without writing the declared output.
    no_output = spec.model_copy(
        update={"command": (sys.executable, "-c", "pass"), "expected_outputs": ("missing.glb",)}
    )
    incomplete = run_build(tmp_path, no_output, apply=True)
    assert incomplete.status == "failed"
    assert incomplete.verified_outputs[0].status == "missing"

    diff = sync_manifest(tmp_path, "models/liver/assets.json", apply=True)
    assert diff.applied is True
    assert len(diff.updated_exports) == 1

    reloaded = Workspace.load(tmp_path, include_legacy_adapters=False)
    exp = reloaded.registry.assets[0].revisions[0].exports[0]
    assert exp.sha256 == hashlib.sha256(glb_bytes).hexdigest()
    assert exp.triangles == 16
    assert exp.storage_status == "verified"


def test_blobs_lfs_glb_and_curation_projections(tmp_path: Path) -> None:
    (tmp_path / "models/joints/exports").mkdir(parents=True)
    glb_bytes = _make_minimal_glb("Humerus.r", triangles=12)
    (tmp_path / "models/joints/exports/elbow.glb").write_bytes(glb_bytes)
    knee_sha = "a" * 64
    (tmp_path / "models/joints/exports/knee.glb").write_bytes(
        f"version https://git-lfs.github.com/spec/v1\noid sha256:{knee_sha}\nsize 4096\n".encode()
    )
    stats = inspect_mesh(tmp_path, "models/joints/exports/elbow.glb")
    assert stats is not None
    assert stats.triangles == 12
    assert verify(tmp_path, "models/joints/exports/knee.glb", knee_sha, 4096).status == (
        "pointer-match"
    )

    liver_sha = "b" * 64
    registry = AssetRegistry(
        assets=(
            Asset(
                id="liver",
                title="Liver",
                kind="model",
                owner_dir="models/liver",
                revisions=(
                    Revision(
                        id="r02",
                        status="active",
                        exports=(
                            Export(
                                id="mesh",
                                path="models/liver/liver.glb",
                                format="glb",
                                sha256=liver_sha,
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    delivery = DeliveryGraph(
        consumers=(
            Consumer(
                id="lesson:digestive",
                title="Digestive",
                kind="lesson-stop",
                owner_path="lessons/digestive/consumer.json",
                pins=(Pin(asset_id="liver", revision_id="r02", export_id="mesh"),),
            ),
        )
    )
    review_only = CurationStore(
        reviews=(
            Review(
                id="rev-1",
                export_path="models/liver/liver.glb",
                task_id="t1",
                task="Locate liver",
                status="accepted",
                owner_path="reviews/r1.json",
                sha256=liver_sha,
            ),
        ),
        selections=(
            Selection(
                id="sel-1",
                kind="teaching-default",
                export_path="models/liver/liver.glb",
                owner_path="docs/selections.json",
            ),
        ),
    )
    # Missing digest never matches; accepted assessment alone is evidence, not qualification.
    assert review_only.qualification_for("models/liver/liver.glb", None).statuses == ()
    assert review_only.qualification_for("models/liver/liver.glb", liver_sha).statuses == (
        "accepted",
    )
    assert review_only.qualification_for("models/liver/liver.glb", liver_sha).qualified is False

    curation = CurationStore(
        reviews=review_only.reviews,
        selections=review_only.selections,
        qualifications=(
            Qualification(
                id="qual-1",
                asset_id="liver",
                revision_id="r02",
                scope="task",
                decision="qualified",
                owner_path="models/liver/asset.record.json",
                export_path="models/liver/liver.glb",
                sha256=liver_sha,
                task_id="t1",
            ),
        ),
    )
    imp = delivery.impact("liver", registry, curation)
    assert imp.found is True
    assert len(imp.consumers) == 1
    assert len(imp.reviews) == 1
    assert len(imp.qualifications) == 1
    assert len(imp.selections) == 1

    gallery = curation.compile_gallery(registry, delivery)
    exp_out = gallery.assets[0].revisions[0].exports[0]
    assert exp_out.qualified is True
    assert exp_out.review_statuses == ("accepted",)
    assert exp_out.qualification_decisions == ("qualified",)
    r2_items = curation.plan_r2_sync(registry, delivery)
    assert [i.path for i in r2_items] == ["models/liver/liver.glb"]


def test_cardiac_atlas_parity_and_unknown_target() -> None:
    repo = Path(__file__).resolve().parents[3]
    ws = Workspace.load(repo)

    # show(), impact(), and compile_gallery() agree on owner-declared Cardiac Atlas identity.
    shown = ws.show("anatomy:heart:cardiac-atlas")
    assert isinstance(shown, ShowAssetResult)
    assert shown.found is True
    assert shown.asset.id == "anatomy:heart:cardiac-atlas"
    assert shown.asset.source_manifest == "heart/Cardiac_Atlas_Animated/asset.record.json"
    assert len(shown.revisions) == 1
    rev = shown.revisions[0]
    assert rev.id == "shared-source-r01"
    assert rev.status == "provisional"
    # Unset None fields are omitted from serialized dicts (no null noise).
    assert "recipe" not in rev.to_dict()
    assert "spatial" not in rev.provenance.to_dict()

    export_paths = {e.path for e in rev.exports}
    assert export_paths == {
        "heart/Cardiac_Atlas_Animated/exports/shared-source-r01/cardiac-static-ed.glb",
        "heart/Cardiac_Atlas_Animated/exports/shared-source-r01/ventricular-wall-motion.glb",
    }
    for exp in rev.exports:
        assert exp.qualification.qualified is False
        assert exp.qualification.statuses == ("accepted",)
        assert exp.qualification.adoption_statuses == ("provisional",)
        assert exp.parts[0].provenance is not None
        assert exp.parts[0].provenance.spatial is not None
        assert exp.parts[0].provenance.spatial.source_frame == (
            "Cardiac_Atlas_Animated_Source.blend/native"
        )

    assert len(shown.tasks) == 2
    for task in shown.tasks:
        assert task.adoption_status == "provisional"
        assert task.qualified is False
        assert len(task.assessments) == 1
        assert task.assessments[0].status == "accepted"

    for task in shown.tasks:
        effect = ws.impact(task.export_path)
        assert [use.use_id for use in effect.adoptions] == [task.use_id]
        assert {r.export_path for r in effect.reviews} == {task.export_path}

    imp = ws.impact("anatomy:heart:cardiac-atlas")
    assert imp.found is True
    assert imp.matched_assets == ("anatomy:heart:cardiac-atlas",)
    assert set(imp.matched_export_paths) == export_paths
    assert len(imp.adoptions) == 2
    assert len(imp.reviews) == 2
    assert len(imp.selections) == 2
    assert {s.review_id for s in imp.selections} == {r.id for r in imp.reviews}

    gallery = ws.compile_gallery()
    cardiac_entries = [a for a in gallery.assets if a.owner_dir == "heart/Cardiac_Atlas_Animated"]
    assert len(cardiac_entries) == 1
    assert cardiac_entries[0].id == "anatomy:heart:cardiac-atlas"
    gallery_exports = cardiac_entries[0].revisions[0].exports
    assert {e.path for e in gallery_exports} == export_paths
    assert all(e.qualified is False for e in gallery_exports)
    assert all(e.review_statuses == ("accepted",) for e in gallery_exports)
    assert all(e.adoption_statuses == ("provisional",) for e in gallery_exports)

    found = ws.find("cardiac-atlas")
    assert any(a.id == "anatomy:heart:cardiac-atlas" for a in found.assets)

    # Unknown target returns explicit unknown-target result.
    unknown_show = ws.show("anatomy:heart:does-not-exist")
    assert isinstance(unknown_show, UnknownTargetResult)
    assert unknown_show.to_dict() == {
        "target": "anatomy:heart:does-not-exist",
        "found": False,
        "status": "unknown-target",
    }
    unknown_imp = ws.impact("anatomy:heart:does-not-exist")
    assert unknown_imp.found is False
    assert unknown_imp.status == "unknown-target"
    assert unknown_imp.matched_export_paths == ()


def test_typer_cli_pilot_validate_and_error_exit() -> None:
    pilot = Path(__file__).resolve().parents[1] / "pilot"
    runner = CliRunner()
    res = runner.invoke(app, ["--repo", str(pilot), "--native-only", "validate"])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["status"] == "ok"
    assert payload["counts"]["assets"] == 2

    shown = runner.invoke(app, ["--repo", str(pilot), "--native-only", "show", "liver-s1233"])
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)["found"] is True

    found = runner.invoke(app, ["--repo", str(pilot), "--native-only", "find", "liver"])
    assert found.exit_code == 0, found.output
    assert len(json.loads(found.output)["assets"]) >= 1

    bad = runner.invoke(app, ["--repo", str(pilot), "--native-only", "bundle", "nonexistent"])
    assert bad.exit_code == 2


def test_qualification_is_bound_to_digest_owner_and_use() -> None:
    path, digest = "shared.glb", "a" * 64
    use = Adoption(
        use_id="a",
        consumer_id="lesson-a",
        asset_id="heart",
        revision_id="r1",
        export_path=path,
        owner_path="record",
        status="qualified",
        sha256=digest,
        requirement_ids=("locate",),
        part_ids=("arch",),
    )
    decision = Qualification(
        id="q",
        asset_id="heart",
        revision_id="r1",
        owner_path="record",
        scope="teaching",
        decision="qualified",
        export_path=path,
        sha256=digest,
        use_id="a",
        part_ids=("arch",),
    )
    curation = CurationStore(qualifications=(decision,), adoptions=(use,))

    def check(store, consumer="lesson-a", **updates):
        args = dict(
            asset_id="heart",
            revision_id="r1",
            task_id="locate",
            part_id="arch",
            consumer_id=consumer,
        )
        return store.qualification_for(path, digest, **(args | updates)).qualified

    assert check(curation)
    assert not check(curation, consumer="lesson-b")
    assert not check(curation, revision_id="r2")
    assert not check(curation, task_id="animate")
    assert not check(curation, part_id="wall")
    absent = CurationStore(
        qualifications=(decision.model_copy(update={"sha256": None}),), adoptions=(use,)
    )
    assert not check(absent)


def test_economy_and_bundle_agree_on_repeated_export() -> None:
    ws = Workspace.load(
        Path(__file__).resolve().parents[1] / "pilot", include_legacy_adapters=False
    )
    sweep = next(c for c in ws.delivery.consumers if c.kind == "ultrasound-sweep")
    vessels = sweep.pins[1]
    graph = DeliveryGraph(
        consumers=(
            sweep.model_copy(
                update={
                    "pins": (
                        vessels.model_copy(update={"parts": ()}),
                        vessels.model_copy(update={"parts": ("portal-vein",)}),
                    )
                }
            ),
        )
    )
    bundle = graph.bundle_for(sweep.id, ws.registry)
    economy = graph.economy(ws.registry)
    metric = economy.consumer_metrics[0]
    assert bundle.total_bytes == metric.total_bytes == 680000
    assert metric.loads == 1
    assert metric.byte_utilization == metric.part_utilization == 1
    assert json.loads(economy.to_json()) == economy.to_dict()


def test_build_cli_returns_failure_receipt(tmp_path: Path) -> None:
    manifest = {
        "assets": [
            {
                "id": "demo",
                "revisions": [
                    {
                        "id": "r1",
                        "recipe": "build.py",
                        "exports": [{"id": "mesh", "path": "mesh.glb"}],
                    }
                ],
            }
        ]
    }
    (tmp_path / "assets.json").write_text(json.dumps(manifest))
    recipe = tmp_path / "build.py"
    runner = CliRunner()
    for code in (0, 3):
        recipe.write_text(f"raise SystemExit({code})")
        result = runner.invoke(app, ["--repo", str(tmp_path), "build", "demo", "r1", "--apply"])
        assert result.exit_code == 1
        receipt = json.loads(result.output)
        assert receipt["status"] == "failed"
        assert receipt["returncode"] == code
