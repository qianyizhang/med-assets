"""Self-contained test suite for AssetKit."""

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
    BudgetPolicy,
    Catalog,
    Concept,
    ConceptEdge,
    ConceptGraph,
    Consumer,
    Export,
    Part,
    Pin,
    Provenance,
    Requirement,
    Review,
    Revision,
    Selection,
    analyze_economy,
    check_artifact,
    impact,
    inspect_glb,
    load_catalog,
    resolve,
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


class AssetKitTests(unittest.TestCase):
    def test_polyhierarchical_concept_graph_and_cycle_rejection(self) -> None:
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
        self.assertEqual(graph.descendants("skeletal-system"), {"vertebral-column", "L3-vertebra"})

        cyclic = ConceptGraph(
            concepts=(Concept("a", "A"), Concept("b", "B")),
            edges=(
                ConceptEdge("a", "part_of", "b"),
                ConceptEdge("b", "part_of", "a"),
            ),
        )
        with self.assertRaisesRegex(AssetKitError, "Cycle"):
            cyclic.validate()

    def test_hybrid_asset_per_part_provenance_and_foreign_overlay(self) -> None:
        """One liver asset can combine s1233 native anatomy with a foreign illustrative lesion."""
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
                                        limits=(
                                            "Illustrative mass placement for ultrasound teaching",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        catalog = Catalog(
            repository="/tmp/repo",
            concepts=ConceptGraph(
                concepts=(Concept("liver", "Liver"), Concept("focal-lesion", "Focal lesion")),
            ),
            assets=(liver,),
            consumers=(
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
            ),
        )
        self.assertEqual(catalog.validate(), [])
        resolved = resolve(catalog, "us:abdomen:focal-lesion", "req-lesion")
        cand = resolved["requirements"][0]["conceptCandidates"][0]
        self.assertEqual(cand["registration"], "illustrative")
        self.assertEqual(cand["subject"], "synthetic")
        self.assertFalse(cand["qualified"])

    def test_economy_detects_bloat_low_utilization_and_load_fanout(self) -> None:
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
        overview_consumer = Consumer(
            id="body-systems:liver-overview",
            title="Body Systems Liver Overview",
            kind="lesson-stop",
            owner_path="lessons/body-systems/consumer.json",
            pins=(Pin("liver-monolith", "r01", "everything", parts=("outer",)),),
        )
        catalog = Catalog(repository="/tmp/repo", assets=(bloated,), consumers=(overview_consumer,))
        report = analyze_economy(catalog, BudgetPolicy())

        m = report.consumer_metrics[0]
        self.assertEqual(m.loads, 1)
        self.assertEqual(m.part_utilization, 0.25)
        self.assertEqual(m.byte_utilization, 0.1)
        self.assertIn("low-part-utilization", m.budget_flags)
        self.assertIn("low-byte-utilization", m.budget_flags)
        actions = {r.action for r in report.recommendations}
        self.assertIn("split-export", actions)
        self.assertIn("over-budget", actions)

    def test_native_workspace_multi_asset_dir_glb_and_lfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 1 directory ("models/joints") declaring 2 independent assets
            (root / "models/joints/exports").mkdir(parents=True)
            glb_bytes = _make_minimal_glb("Humerus.r", triangles=12)
            glb_sha = hashlib.sha256(glb_bytes).hexdigest()
            (root / "models/joints/exports/elbow.glb").write_bytes(glb_bytes)

            knee_sha = "a" * 64
            (root / "models/joints/exports/knee.glb").write_bytes(
                f"version https://git-lfs.github.com/spec/v1\noid sha256:{knee_sha}\nsize 4096\n".encode()
            )
            (root / "models/joints/assets.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "assets": [
                            {
                                "id": "elbow",
                                "title": "Elbow",
                                "kind": "model",
                                "revisions": [
                                    {
                                        "id": "r02",
                                        "status": "active",
                                        "exports": [
                                            {
                                                "id": "mesh",
                                                "path": "exports/elbow.glb",
                                                "sha256": glb_sha,
                                                "bytes": len(glb_bytes),
                                                "parts": [
                                                    {"id": "humerus", "selector": "Humerus.r"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "knee",
                                "title": "Knee",
                                "kind": "model",
                                "revisions": [
                                    {
                                        "id": "r01",
                                        "status": "active",
                                        "exports": [
                                            {
                                                "id": "mesh",
                                                "path": "exports/knee.glb",
                                                "sha256": knee_sha,
                                                "bytes": 4096,
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            stats = inspect_glb(root / "models/joints/exports/elbow.glb")
            self.assertIsNotNone(stats)
            assert stats is not None
            self.assertEqual(stats.triangles, 12)
            self.assertEqual(stats.node_triangles["Humerus.r"], 12)

            lfs_chk = check_artifact(root, "models/joints/exports/knee.glb", knee_sha, 4096)
            self.assertEqual(lfs_chk.status, "pointer-match")

            cat = load_catalog(root, include_legacy_adapters=False, inspect_glbs=True)
            self.assertEqual(cat.validate(), [])
            self.assertEqual(len(cat.assets), 2)
            elbow = next(a for a in cat.assets if a.id == "elbow")
            self.assertEqual(elbow.revisions[0].exports[0].triangles, 12)
            self.assertEqual(elbow.revisions[0].exports[0].parts[0].triangles, 12)
            knee = next(a for a in cat.assets if a.id == "knee")
            self.assertEqual(knee.revisions[0].exports[0].storage_status, "pointer-match")

    def test_impact_traces_consumers_reviews_and_selections(self) -> None:
        cat = Catalog(
            repository="/tmp/repo",
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
                            exports=(Export("mesh", "models/liver/liver.glb", "glb"),),
                        ),
                    ),
                ),
            ),
            consumers=(
                Consumer(
                    id="lesson:digestive",
                    title="Digestive",
                    kind="lesson-stop",
                    owner_path="lessons/digestive/consumer.json",
                    pins=(Pin("liver", "r02", "mesh"),),
                ),
            ),
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
                    "sel-1", "teaching-default", "models/liver/liver.glb", "docs/selections.json"
                ),
            ),
        )
        res = impact(cat, "liver")
        self.assertEqual(len(res["consumers"]), 1)
        self.assertEqual(len(res["reviews"]), 1)
        self.assertEqual(len(res["selections"]), 1)


if __name__ == "__main__":
    unittest.main()
