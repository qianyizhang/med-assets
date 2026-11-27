import hashlib,json,tempfile,unittest
from pathlib import Path
from med_assets.governance import GovernanceError,build_catalog,find,show,ultrasound_gap_requirements
from med_assets.governance_migration import apply_backfill_plan,create_backfill_plan,hydrate_lfs
from med_assets.domain import Concept,ConceptRelation,GovernanceGraph,RelationType

class GovernanceTests(unittest.TestCase):
    def fixture(self,root):
        (root/"models/liver").mkdir(parents=True);(root/"models/liver/README.md").write_text("# Liver\n")
        (root/"models/liver/liver.glb").write_bytes(b"glb")
        (root/"lessons/body-systems").mkdir(parents=True)
        (root/"lessons/body-systems/reviewed-stops.json").write_text(json.dumps({"reviewer":"reviewer","date":"2026-11-22",
          "stops":[{"system":"digestive","detail":"digestive-liver","action":"Locate liver.","observation":"Visible.","status":"passed"}]}))
        (root/"docs/gallery/use-cases").mkdir(parents=True)
        (root/"docs/gallery/use-cases/ultrasound-anatomy.md").write_text(
          "# Ultrasound\n| Scenario | Coverage |\n| --- | --- |\n| [Abdominal survey](#abdomen) | Locate liver and biliary anatomy. |\n| [AAA screening](#abdomen) | Follow the aorta through the bifurcation. |\n")
        (root/"experiments/ultrasound-sweep/cases/organs").mkdir(parents=True)
        (root/"experiments/ultrasound-sweep/cases/organs/cases.json").write_text(json.dumps([
          {"id":"abdomen-survey","family":"abdomen","title":"Abdominal survey","summary":"Survey the abdomen.",
           "views":[{"title":"Liver","caption":"Locate liver."},{"title":"Portal vein","caption":"Trace portal vein."}]}]))
        (root/"experiments/ultrasound-sweep").mkdir(parents=True,exist_ok=True)
        (root/"experiments/ultrasound-sweep/abdomen-tracks.json").write_text(json.dumps({
          "sweeps":[{"id":"liver","title":"Liver sweep","parts":["liver"],"landmarks":["hepatic-vein"]}]}))
    def test_scan_keeps_package_and_consumers_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);catalog=build_catalog(root)
            self.assertEqual(len(catalog.packages),2);self.assertEqual(next(x for x in catalog.packages if x.path=="models/liver").record_status,"unregistered")
            self.assertEqual(len(catalog.consumers),7);self.assertEqual(find(catalog,"liver")["packages"][0]["path"],"models/liver")
            self.assertEqual(show(catalog,"body-systems:digestive:digestive-liver")["domain"],"body-systems")
            self.assertEqual(show(catalog,"ultrasound:case-view:organs:abdomen-survey:2")["title"],"Abdominal survey · Portal vein")
            self.assertEqual(show(catalog,"ultrasound:sweep:abdomen-tracks:liver")["domain"],"ultrasound-anatomy")
    def test_backfill_requires_explicit_approval_and_starts_provisional(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);plan=create_backfill_plan(root);proposal=plan["proposals"][0]
            self.assertEqual(proposal["decision"],"defer");proposal.update(decision="accept",assetId="anatomy:liver:hra-female")
            path=root/"backfill.json";path.write_text(json.dumps(plan))
            applied=apply_backfill_plan(root,path);self.assertEqual(applied,["models/liver/asset.record.json"])
            record=json.loads((root/applied[0]).read_text());self.assertEqual(record["status"],"provisional")
            self.assertEqual(apply_backfill_plan(root,path),[])
    def test_ultrasound_geometry_gaps_are_parsed_without_nested_helper_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/"experiments/ultrasound-sweep/development/assets-abdomen.js"
            path.parent.mkdir(parents=True)
            path.write_text(
              'const gap = (asset, part, label, reason) => ({ part, label, reason });\\n'
              'const rebuild = (...args) => ({ ...gap(...args), status: "rebuild" });\\n'
              'const liverGap = gap(asset, "hepatic-vein", "Hepatic vein", "No traced vessel");\\n'
              'const lesionGap = rebuild(asset, "focal-lesion", "Focal lesion", "No case-specific lesion geometry");\\n'
              'const lymphGap = missingPart("lymph", "Lymph node", "cervical-node", "Cervical node", "No regional registration");\\n')
            rows=ultrasound_gap_requirements(root)
            self.assertEqual(len(rows),3)
            self.assertEqual({row.evidence["part"] for row in rows},
                {"hepatic-vein","focal-lesion","cervical-node"})
            self.assertEqual({row.status for row in rows},{"missing-required","rebuild-required"})
    def test_package_manifest_resolves_declared_payload_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            payload=b"hydrated model bytes";digest=hashlib.sha256(payload).hexdigest()
            (root/"models/liver/liver.glb").write_bytes(payload)
            remote=b"remote LFS payload";remote_digest=hashlib.sha256(remote).hexdigest()
            pointer=(b"version https://git-lfs.github.com/spec/v1\\n"
                + b"oid sha256:"+remote_digest.encode()+b"\\nsize "
                + str(len(remote)).encode()+b"\\n")
            (root/"models/liver/remote.glb").write_bytes(pointer)
            (root/"models/liver/package-manifest.json").write_text(json.dumps([
                {"file":"liver.glb","bytes":len(payload),"sha256":digest},
                {"file":"remote.glb","bytes":len(remote),"sha256":remote_digest}]))
            package=next(x for x in build_catalog(root).packages if x.path=="models/liver")
            self.assertEqual({x.path:x.verification for x in package.artifacts},
                {"models/liver/liver.glb":"verified","models/liver/remote.glb":"pointer-match"})
            self.assertEqual(package.manifests,("models/liver/package-manifest.json",))
    def test_backfill_rejects_stale_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);plan=create_backfill_plan(root)
            plan["proposals"][0].update(decision="accept",assetId="anatomy:liver:hra-female")
            path=root/"backfill.json";path.write_text(json.dumps(plan));(root/"models/liver/README.md").write_text("# Changed\n")
            with self.assertRaises(GovernanceError): apply_backfill_plan(root,path)
    def test_concept_graph_supports_polyhierarchy_but_rejects_cycles(self):
        concepts=(Concept("liver","Liver"),Concept("metabolism","Metabolism"),Concept("digestive","Digestive system"))
        graph=GovernanceGraph(concepts,(
            ConceptRelation("liver",RelationType.PART_OF,"digestive"),
            ConceptRelation("liver",RelationType.PARTICIPATES_IN,"metabolism")))
        graph.validate()
        cyclic=GovernanceGraph(concepts,(
            ConceptRelation("liver",RelationType.PART_OF,"digestive"),
            ConceptRelation("digestive",RelationType.PART_OF,"liver")))
        with self.assertRaisesRegex(ValueError,"Cycle"):
            cyclic.validate()
    def test_hydration_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            result=hydrate_lfs(Path(directory),["models/liver/liver.glb"])
            self.assertEqual(result["status"],"planned");self.assertIn("--include",result["command"])
if __name__=="__main__": unittest.main()
