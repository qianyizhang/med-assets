"""Self-contained unit test suite for AssetKit's 6 bounded contexts."""

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from assetkit import (
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
    Requirement,
    Review,
    Revision,
    Selection,
    Workspace,
    inspect_mesh,
    plan_build,
    run_build,
    sync_manifest,
    verify,
)


def _make_minimal_glb(node_name: str = "LiverMesh", triangles: int = 2) -> bytes:
    """Construct a valid minimal GLB v2 binary with 1 mesh and known triangle count."""
    doc = {
        "asset": {"version": "2.0"},
        "nodes": [{"name": node_name, "mesh": 0}],
        "meshes": [{"primitives": [{"mode": 4, "indices": 0}]}],
        "accessors": [{"count": triangles * 3, "componentType": 5123, "type": "SCALAR"}],
    }
    json_bytes = json.dumps(doc).encode("utf-8")
    pad = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b" " * pad
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


class AssetKitTests(unittest.TestCase):
    def test_vocab_polyhierarchy_and_cycle_rejection(self) -> None:
        graph = ConceptGraph(
            concepts=(
                Concept("skeletal-system", "Skeletal system"),
                Concept("vertebral-column", "Vertebral column"),
                Concept("L3-vertebra", "L3 vertebra"),
                Concept("bone-marrow", "Bone marrow"),
                Concept("blood-cell", "Blood cell"),
                Concept("immune-response", "Immune response"),
            ),
            edges=(
                ConceptEdge("vertebral-column", "part_of", "skeletal-system"),
                ConceptEdge("L3-vertebra", "part_of", "vertebral-column"),
                ConceptEdge("bone-marrow", "located_in", "L3-vertebra"),
                ConceptEdge("bone-marrow", "produces", "blood-cell"),
                ConceptEdge("bone-marrow", "participates_in", "immune-response"),
            ),
        )
        graph.validate()
        self.assertEqual(graph.ancestors("L3-vertebra"), {"vertebral-column", "skeletal-system"})
        self.assertEqual(
            graph.expand(("skeletal-system",)),
            {"skeletal-system", "vertebral-column", "L3-vertebra"},
        )
        self.assertEqual(len(graph.related("bone-marrow", "produces")), 1)

        cyclic = ConceptGraph(
            concepts=(Concept("a", "A"), Concept("b", "B")),
            edges=(ConceptEdge("a", "part_of", "b"), ConceptEdge("b", "part_of", "a")),
        )
        with self.assertRaisesRegex(AssetKitError, "Cycle"):
            cyclic.validate()

    def test_hybrid_registry_delivery_bundle_and_resolution(self) -> None:
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
                                    "outer-surface",
                                    "Liver exterior",
                                    ("liver",),
                                    ("liver",),
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
                                    "focal-lesion",
                                    "Hyperechoic focal lesion",
                                    ("focal-lesion",),
                                    ("focal-lesion",),
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
            concepts=(Concept("liver", "Liver"), Concept("focal-lesion", "Focal lesion"))
        )
        registry = AssetRegistry((liver,))
        delivery = DeliveryGraph(
            (
                Consumer(
                    id="us:abdomen:focal-lesion",
                    title="Abdominal focal lesion sweep",
                    kind="ultrasound-sweep",
                    owner_path="experiments/ultrasound-sweep/consumer.json",
                    requirements=(
                        Requirement(
                            "req-liver",
                            "Liver parenchyma",
                            "satisfied",
                            ("liver",),
                            subject="s1233",
                        ),
                        Requirement(
                            "req-lesion",
                            "Focal lesion overlay",
                            "satisfied",
                            ("focal-lesion",),
                            variant="focal-lesion",
                        ),
                        Requirement(
                            "req-caval",
                            "Hepatic vein IVC junction",
                            "open-gap",
                            ("hepatic-vein",),
                            subject="s1233",
                        ),
                    ),
                    pins=(
                        Pin(
                            "liver-s1233",
                            "r03",
                            "surface",
                            "req-liver",
                            ("outer-surface",),
                            registration="native",
                        ),
                        Pin(
                            "liver-s1233",
                            "r03",
                            "lesion-overlay",
                            "req-lesion",
                            ("focal-lesion",),
                            registration="illustrative",
                        ),
                    ),
                ),
            )
        )
        curation = CurationStore()
        self.assertEqual(registry.validate(vocab), [])
        self.assertEqual(delivery.validate(registry), [])

        bundle = delivery.bundle_for("us:abdomen:focal-lesion", registry)
        self.assertEqual(len(bundle.items), 2)
        self.assertEqual(bundle.total_bytes, 380_000)
        self.assertEqual(len(bundle.open_gaps), 1)
        self.assertEqual(len(delivery.open_gaps("us:")), 1)

        resolved = delivery.resolve(
            "us:abdomen:focal-lesion", registry, vocab, curation, "req-lesion"
        )
        cand = resolved["requirements"][0]["conceptCandidates"][0]
        self.assertEqual(cand["registration"], "illustrative")
        self.assertEqual(cand["subject"], "synthetic")
        self.assertFalse(cand["qualified"])

    def test_delivery_economy_detects_bloat_and_low_utilization(self) -> None:
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
                                Part("outer", "Outer", bytes=500_000),
                                Part("portal", "Portal", bytes=1_500_000),
                                Part("hepatic", "Hepatic", bytes=1_500_000),
                                Part("biliary", "Biliary", bytes=1_500_000),
                            ),
                        ),
                    ),
                ),
            ),
        )
        registry = AssetRegistry((bloated,))
        delivery = DeliveryGraph(
            (
                Consumer(
                    id="body-systems:liver-overview",
                    title="Body Systems Liver Overview",
                    kind="lesson-stop",
                    owner_path="lessons/body-systems/consumer.json",
                    pins=(Pin("liver-monolith", "r01", "everything", parts=("outer",)),),
                ),
            )
        )
        report = delivery.economy(registry, BudgetPolicy())
        m = report.consumer_metrics[0]
        self.assertEqual(m.loads, 1)
        self.assertEqual(m.part_utilization, 0.25)
        self.assertEqual(m.byte_utilization, 0.1)
        self.assertIn("low-part-utilization", m.budget_flags)
        self.assertIn("low-byte-utilization", m.budget_flags)
        actions = {r.action for r in report.recommendations}
        self.assertIn("split-export", actions)
        self.assertIn("over-budget", actions)

    def test_build_runner_and_sync_manifest_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "models/liver/recipes").mkdir(parents=True)
            (root / "models/liver/recipes/build.py").write_text("import bpy\n", encoding="utf-8")
            (root / "models/liver/assets.json").write_text(
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
                                        "exports": [
                                            {"id": "mesh", "path": "exports/r03/liver.glb"}
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ws = Workspace.load(root, include_legacy_adapters=False)
            spec = plan_build(root, ws.registry, "liver", "r03")
            self.assertEqual(spec.command[0], "blender")

            # Dry-run defaults to planned without running subprocess
            dry = run_build(root, spec, apply=False)
            self.assertEqual(dry.status, "planned")

            # Execute via fake runner seam and verify rebuilt GLB
            glb_bytes = _make_minimal_glb("Liver_Outer", triangles=16)
            runner = _FakeRunner(glb_bytes)
            built = run_build(root, spec, apply=True, runner=runner)
            self.assertEqual(built.status, "built")
            self.assertEqual(built.verified_outputs[0]["triangles"], 16)

            # Sync manifest updates sha256, bytes, and triangles
            diff = sync_manifest(root, "models/liver/assets.json", apply=True)
            self.assertTrue(diff.applied)
            self.assertEqual(len(diff.updated_exports), 1)
            reloaded = Workspace.load(root, include_legacy_adapters=False)
            exp = reloaded.registry.assets[0].revisions[0].exports[0]
            self.assertEqual(exp.sha256, hashlib.sha256(glb_bytes).hexdigest())
            self.assertEqual(exp.triangles, 16)
            self.assertEqual(exp.storage_status, "verified")

    def test_blobs_lfs_glb_and_curation_projections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "models/joints/exports").mkdir(parents=True)
            glb_bytes = _make_minimal_glb("Humerus.r", triangles=12)
            (root / "models/joints/exports/elbow.glb").write_bytes(glb_bytes)
            knee_sha = "a" * 64
            (root / "models/joints/exports/knee.glb").write_bytes(
                f"version https://git-lfs.github.com/spec/v1\noid sha256:{knee_sha}\nsize 4096\n".encode()
            )
            stats = inspect_mesh(root, "models/joints/exports/elbow.glb")
            assert stats is not None
            self.assertEqual(stats.triangles, 12)
            self.assertEqual(
                verify(root, "models/joints/exports/knee.glb", knee_sha, 4096).status,
                "pointer-match",
            )

        registry = AssetRegistry(
            (
                Asset(
                    id="liver",
                    title="Liver",
                    kind="model",
                    owner_dir="models/liver",
                    revisions=(
                        Revision(
                            id="r02",
                            status="active",
                            exports=(Export("mesh", "models/liver/liver.glb", "glb"),),
                        ),
                    ),
                ),
            )
        )
        delivery = DeliveryGraph(
            (
                Consumer(
                    id="lesson:digestive",
                    title="Digestive",
                    kind="lesson-stop",
                    owner_path="lessons/digestive/consumer.json",
                    pins=(Pin("liver", "r02", "mesh"),),
                ),
            )
        )
        curation = CurationStore(
            reviews=(
                Review(
                    "rev-1",
                    "models/liver/liver.glb",
                    "t1",
                    "Locate liver",
                    "accepted",
                    "reviews/r1.json",
                ),
            ),
            selections=(
                Selection(
                    "sel-1",
                    "teaching-default",
                    "models/liver/liver.glb",
                    "docs/selections.json",
                ),
            ),
        )
        imp = delivery.impact("liver", registry, curation)
        self.assertEqual(len(imp["consumers"]), 1)
        self.assertEqual(len(imp["reviews"]), 1)
        self.assertEqual(len(imp["selections"]), 1)

        gallery = curation.compile_gallery(registry, delivery)
        self.assertTrue(gallery["assets"][0]["revisions"][0]["exports"][0]["qualified"])
        r2_items = curation.plan_r2_sync(registry, delivery)
        self.assertEqual([i["path"] for i in r2_items], ["models/liver/liver.glb"])


if __name__ == "__main__":
    unittest.main()
