"""Tests for controlled asset lifecycle operations."""
import hashlib, json, tempfile, unittest
from pathlib import Path
from med_assets.governance import GovernanceError, build_catalog
from med_assets.governance_lifecycle import create_lifecycle_plan, apply_lifecycle_plan
from med_assets.governance_resolution import resolve_detailed

class LifecycleTests(unittest.TestCase):
    def fixture(self, root):
        package=root/"models"/"fixture"; package.mkdir(parents=True)
        (package/"README.md").write_text("# Fixture\n")
        payload=b"fixture geometry"; (package/"fixture.glb").write_bytes(payload)
        digest=hashlib.sha256(payload).hexdigest()
        record={"schemaVersion":1,"assetId":"fixture:asset","title":"Fixture","kind":"anatomy",
            "status":"provisional","owner":"models/fixture",
            "concepts":[{"conceptId":"organ","label":"Organ"}],
            "sources":[{"sourceId":"source:fixture","rights":"owner-declared"}],
            "parts":[{"partId":"organ","label":"Organ","selectors":["fixture.glb"]}],
            "revisions":[{"revisionId":"r1","status":"provisional","partIds":["organ"],
                "exports":[{"path":"models/fixture/fixture.glb","sha256":digest,"bytes":len(payload)}],"qualifications":[]}],
            "artifacts":[],"exports":[],"uses":[],"retirement":None,"unresolved":[]}
        (package/"asset.record.json").write_text(json.dumps(record,indent=2)+"\n")
        lesson=root/"lessons"/"demo"; lesson.mkdir(parents=True)
        (lesson/"lesson.json").write_text(json.dumps({"title":"Fixture","question":"Inspect organ","model":"models/fixture/fixture.glb"}))
        return package

    def payload(self, root, value):
        path=root/"payload.json"; path.write_text(json.dumps(value)); return path

    def plan_apply(self, root, action, payload):
        path=root/f"{action}.plan.json"
        path.write_text(json.dumps(create_lifecycle_plan(root,"fixture:asset",action,self.payload(root,payload))))
        return path

    def test_resolution_exposes_exact_revision_export_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            result=resolve_detailed(build_catalog(root),"lesson:demo")
            candidate=result["exactExportCandidates"][0]
            maintenance=candidate["maintenance"]
            self.assertEqual(maintenance["recordStatus"],"provisional")
            revision=maintenance["revisionCandidates"][0]
            self.assertEqual(revision["revisionId"],"r1")
            self.assertEqual(revision["partId"],"organ")
            self.assertEqual(revision["geometryDigest"],hashlib.sha256(b"fixture geometry").hexdigest())
            self.assertEqual(maintenance["sourceDeclarations"][0]["sourceId"],"source:fixture")

    def test_refine_can_disposition_only_explicit_unresolved_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); package=self.fixture(root)
            record_path=package/"asset.record.json"
            record=json.loads(record_path.read_text())
            issue="No exact source selector."
            record["unresolved"]=[issue]
            record_path.write_text(json.dumps(record,indent=2)+"\n")
            plan=self.plan_apply(root,"refine",{"resolveUnresolved":[issue],
                "addUnresolved":["Rights review pending"]})
            apply_lifecycle_plan(root,plan)
            updated=json.loads(record_path.read_text())
            self.assertEqual(updated["unresolved"],["Rights review pending"])

    def test_qualify_promote_and_idempotent_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            evidence=b"reviewed anatomy and runtime"
            (root/"review.json").write_bytes(evidence)
            q={"qualificationId":"q1","scope":"anatomy-and-runtime","reviewer":"owner",
                "assessedAt":"2026-11-27","decision":"qualified","evidence":[{"path":"review.json","sha256":hashlib.sha256(evidence).hexdigest()}]}
            plan=self.plan_apply(root,"qualify",{"revisionId":"r1","qualification":q})
            self.assertEqual(apply_lifecycle_plan(root,plan)["status"],"applied")
            self.assertEqual(apply_lifecycle_plan(root,plan)["status"],"already-applied")
            plan=self.plan_apply(root,"promote",{"revisionId":"r1"})
            apply_lifecycle_plan(root,plan)
            self.assertEqual(next(x for x in build_catalog(root).packages if x.candidate_id=="fixture:asset").record_status,"confirmed")

    def test_adopt_pins_exact_export_and_starts_provisional(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            use={"useId":"use:organ","consumerId":"lesson:demo","revisionId":"r1",
                "exportPath":"models/fixture/fixture.glb","sha256":hashlib.sha256(b"fixture geometry").hexdigest(),
                "bytes":len(b"fixture geometry"),"partIds":["organ"],"requirementIds":["req:organ"]}
            plan=self.plan_apply(root,"adopt",{"use":use}); apply_lifecycle_plan(root,plan)
            record=json.loads((root/"models/fixture/asset.record.json").read_text())
            self.assertEqual(record["uses"][0]["status"],"provisional")
            evidence=b"consumer-specific review"; (root/"consumer-review.json").write_bytes(evidence)
            q={"qualificationId":"use-q1","scope":"ultrasound-liver-task","reviewer":"owner",
                "assessedAt":"2026-11-27","decision":"qualified",
                "evidence":[{"path":"consumer-review.json","sha256":hashlib.sha256(evidence).hexdigest()}]}
            plan=self.plan_apply(root,"qualify",{"useId":"use:organ","qualification":q})
            apply_lifecycle_plan(root,plan)
            record=json.loads((root/"models/fixture/asset.record.json").read_text())
            self.assertEqual(record["uses"][0]["status"],"qualified")
            plan=self.plan_apply(root,"retire",{"reason":"consumer moved","recordedAt":"2026-11-27",
                "readerDisposition":{"lesson:demo":"migrated"}})
            apply_lifecycle_plan(root,plan)
            record=json.loads((root/"models/fixture/asset.record.json").read_text())
            self.assertEqual(record["retirement"]["readerDisposition"]["lesson:demo"],"migrated")

    def test_retire_archive_and_keep_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); package=self.fixture(root)
            plan=self.plan_apply(root,"retire",{"reason":"superseded","recordedAt":"2026-11-27","readerDisposition":{"lesson:demo":"migrated"}})
            apply_lifecycle_plan(root,plan)
            plan=self.plan_apply(root,"archive",{"archivedAt":"2026-11-27","archiveLocation":"records/fixture"})
            apply_lifecycle_plan(root,plan)
            self.assertTrue((package/"fixture.glb").is_file())
            record=json.loads((package/"asset.record.json").read_text())
            self.assertEqual(record["retirement"]["archive"]["location"],"records/fixture")

    def test_stale_and_tampered_plans_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); package=self.fixture(root)
            plan=self.plan_apply(root,"deprecate",{})
            data=json.loads(plan.read_text()); data["after"]["status"]="retired"; plan.write_text(json.dumps(data))
            with self.assertRaisesRegex(GovernanceError,"after-state"): apply_lifecycle_plan(root,plan)
            data=json.loads(plan.read_text()); data["after"]["status"]="deprecated"; plan.write_text(json.dumps(data))
            (package/"README.md").write_text("# changed\n")
            with self.assertRaisesRegex(GovernanceError,"inputs changed"): apply_lifecycle_plan(root,plan)

if __name__=="__main__": unittest.main()
