import json,tempfile,unittest
from pathlib import Path
from med_assets.governance import GovernanceError,build_catalog,find,show
from med_assets.governance_migration import apply_backfill_plan,create_backfill_plan,hydrate_lfs

class GovernanceTests(unittest.TestCase):
    def fixture(self,root):
        (root/"models/liver").mkdir(parents=True);(root/"models/liver/README.md").write_text("# Liver\\n")
        (root/"models/liver/liver.glb").write_bytes(b"glb")
        (root/"lessons/body-systems").mkdir(parents=True)
        (root/"lessons/body-systems/reviewed-stops.json").write_text(json.dumps({"reviewer":"reviewer","date":"2026-11-22",
          "stops":[{"system":"digestive","detail":"digestive-liver","action":"Locate liver.","observation":"Visible.","status":"passed"}]}))
        (root/"docs/gallery/use-cases").mkdir(parents=True)
        (root/"docs/gallery/use-cases/ultrasound-anatomy.md").write_text(
          "# Ultrasound\\n| Scenario | Coverage |\\n| --- | --- |\\n| [Abdominal survey](#abdomen) | Locate liver and biliary anatomy. |\\n")
    def test_scan_keeps_package_and_consumers_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);catalog=build_catalog(root)
            self.assertEqual(len(catalog.packages),1);self.assertEqual(catalog.packages[0].record_status,"unregistered")
            self.assertEqual(len(catalog.consumers),2);self.assertEqual(find(catalog,"liver")["packages"][0]["path"],"models/liver")
            self.assertEqual(show(catalog,"body-systems:digestive:digestive-liver")["domain"],"body-systems")
    def test_backfill_requires_explicit_approval_and_starts_provisional(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);plan=create_backfill_plan(root);proposal=plan["proposals"][0]
            self.assertEqual(proposal["decision"],"defer");proposal.update(decision="accept",assetId="anatomy:liver:hra-female")
            path=root/"backfill.json";path.write_text(json.dumps(plan))
            applied=apply_backfill_plan(root,path);self.assertEqual(applied,["models/liver/asset.record.json"])
            record=json.loads((root/applied[0]).read_text());self.assertEqual(record["status"],"provisional")
    def test_backfill_rejects_stale_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);plan=create_backfill_plan(root)
            plan["proposals"][0].update(decision="accept",assetId="anatomy:liver:hra-female")
            path=root/"backfill.json";path.write_text(json.dumps(plan));(root/"models/liver/README.md").write_text("# Changed\\n")
            with self.assertRaises(GovernanceError): apply_backfill_plan(root,path)
    def test_hydration_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            result=hydrate_lfs(Path(directory),["models/liver/liver.glb"])
            self.assertEqual(result["status"],"planned");self.assertIn("--include",result["command"])
if __name__=="__main__": unittest.main()
