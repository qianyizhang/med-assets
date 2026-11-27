import hashlib,json,tempfile,unittest
from pathlib import Path
from med_assets.governance import Catalog,Consumer,GovernanceError,build_catalog,find,show,resolve,ultrasound_gap_requirements
from med_assets.governance_migration import apply_backfill_plan,create_backfill_plan,hydrate_lfs
from med_assets.domain import Concept,ConceptRelation,GovernanceGraph,RelationType

class GovernanceTests(unittest.TestCase):
    def fixture(self,root):
        (root/"models/liver").mkdir(parents=True);(root/"models/liver/README.md").write_text("# Liver\n")
        (root/"models/liver/liver.glb").write_bytes(b"glb")
        (root/"lessons/body-systems").mkdir(parents=True)
        (root/"lessons/body-systems/reviewed-stops.json").write_text(json.dumps({"reviewer":"reviewer","date":"2026-11-22",
          "stops":[{"system":"digestive","detail":"digestive-liver","action":"Locate liver.","observation":"Visible.","status":"passed"}]}))
        (root/"lessons/body-systems/display").mkdir(parents=True)
        (root/"lessons/body-systems/display/index.json").write_text(json.dumps([
          {"id":"digestive","name":"Digestive","function":"Locate digestive organs.","detail":"Find the liver.",
           "limit":"External localization only.","sources":[["Liver package","models/liver/README.md"]],
           "plates":[{"id":"digestive-liver","kind":"assembly","title":"Digestive assembly","frames":[],"legend":[]},
                     {"id":"digestive-liver","kind":"detail","title":"Liver detail","frames":[],"legend":[]}]}]))
        (root/"docs/gallery/use-cases").mkdir(parents=True)
        (root/"docs/gallery/use-cases/ultrasound-anatomy.md").write_text(
          "# Ultrasound\n| Scenario | Coverage |\n| --- | --- |\n| [Abdominal survey](#abdomen) | Locate liver and biliary anatomy. |\n| [AAA screening](#abdomen) | Follow the aorta through the bifurcation. |\n")
        (root/"experiments/ultrasound-sweep/cases/organs").mkdir(parents=True)
        (root/"experiments/ultrasound-sweep/cases/organs/cases.json").write_text(json.dumps([
          {"id":"abdomen-survey","family":"abdomen","title":"Abdominal survey","summary":"Survey the abdomen.",
           "views":[{"title":"Liver","caption":"Locate liver.","referenceIds":["hepatic-vein","missing-vessel"]},{"title":"Portal vein","caption":"Trace portal vein."}]}]))
        (root/"experiments/ultrasound-sweep").mkdir(parents=True,exist_ok=True)
        (root/"experiments/ultrasound-sweep/abdomen-tracks.json").write_text(json.dumps({
          "common":{"case":"s1233"},
          "sweeps":[{"id":"liver","title":"Liver sweep","parts":["liver"],"landmarks":["hepatic-vein"]}]}))
        research=root/"experiments/ultrasound-sweep/research"
        (research/"references").mkdir(parents=True)
        reference_payload=b"acquired hepatic vein reference"
        (research/"references/hepatic-vein.webp").write_bytes(reference_payload)
        (research/"normal-landmarks.json").write_text(json.dumps({"hepatic-vein":{
          "path":"references/hepatic-vein.webp","title":"Hepatic vein below the diaphragm",
          "license":"CC BY 4.0","licenseUrl":"https://creativecommons.org/licenses/by/4.0/",
          "sha256":hashlib.sha256(reference_payload).hexdigest(),
          "sourceSha256":"a"*64,"sourceMedia":"https://example.invalid/source.jpg",
          "note":"Separate acquired subject; qualitative reference only."}}))
        delivery=root/"body/anatomy-workshop-r1/body-3d-delivery"
        delivery.mkdir(parents=True)
        (root/"body/anatomy-workshop-r1/README.md").write_text("# Anatomy Workshop\\n")
        mesh=delivery/"meshes/liver.glb";mesh.parent.mkdir(parents=True)
        payload=b"workshop liver mesh";mesh.write_bytes(payload)
        asset={"id":"liver","name":{"en":"Liver","zh":"肝脏"},"file":"meshes/liver.glb",
            "group":"digestive","sourceKind":"segmented","provenance":"s1233 segmentation derivative",
            "license":"CC BY 4.0","sourceCase":"s1233","status":"ready",
            "bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),
            "nodes":[{"name":"Liver | source surface","anatomy_id":"liver_surface","view_role":"surface","derivation":"source-derived"}]}
        (delivery/"manifest.json").write_text(json.dumps({
          "version":"2026-11-27-r1",
          "coordinates":{"units":"metres","axes":{"x":"patient left","y":"superior","z":"anterior"},
            "RASmm_to_scene":[[-0.001,0,0,0],[0,0,0.001,-0.43],[0,0.001,0,-0.155],[0,0,0,1]]},
          "assets":[asset]}))
    def test_scan_keeps_package_and_consumers_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);catalog=build_catalog(root)
            self.assertEqual(len(catalog.packages),3);self.assertEqual(next(x for x in catalog.packages if x.path=="models/liver").record_status,"unregistered")
            self.assertEqual(len([x for x in catalog.consumers if x.domain=='body-systems']),3);self.assertEqual(find(catalog,"liver")["packages"][0]["path"],"models/liver")
            self.assertEqual(show(catalog,"body-systems:digestive:digestive-liver")["domain"],"body-systems")
            stop=show(catalog,"body-systems:digestive:digestive-liver")
            self.assertEqual(stop["evidence"]["displayStatus"],"exact-display-detail")
            self.assertEqual(show(catalog,"body-systems:assembly:digestive")["type"],"consumer-requirement")
            self.assertEqual(show(catalog,"body-systems:plate:digestive:digestive-liver")["type"],"consumer-requirement")
            self.assertEqual(show(catalog,"ultrasound:case-view:organs:abdomen-survey:2")["title"],"Abdominal survey · Portal vein")
            self.assertEqual(show(catalog,"ultrasound:sweep:abdomen-tracks:liver")["domain"],"ultrasound-anatomy")
            reference=show(catalog,"ultrasound:reference:normal-landmarks:hepatic-vein")
            self.assertEqual(reference["evidence"]["verification"],"verified")
            chapter=show(catalog,"ultrasound:case-view:organs:abdomen-survey:1")
            self.assertEqual([x["status"] for x in chapter["evidence"]["referenceBindings"]],["resolved","missing"])
            self.assertEqual(show(catalog,"ultrasound:reference-requirement:missing-vessel")["kind"],"reference-requirement")
            self.assertEqual(len(resolve(catalog,"ultrasound:case-view:organs:abdomen-survey:1")["relatedReferences"]),2)
            self.assertTrue(find(catalog,"missing-vessel")["consumers"])
            resolved=resolve(catalog,"ultrasound:sweep:abdomen-tracks:liver")
            self.assertEqual(resolved["parts"][0]["status"],"exact-binding-candidate")
            self.assertEqual(resolved["parts"][0]["exactCandidates"][0]["partId"],"liver")
            self.assertEqual(resolved["parts"][0]["exactCandidates"][0]["sourceCase"],"s1233")
    def test_backfill_requires_explicit_approval_and_starts_provisional(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);plan=create_backfill_plan(root)
            proposal=next(row for row in plan["proposals"] if row["packagePath"]=="body/anatomy-workshop-r1")
            self.assertEqual(proposal["decision"],"defer")
            proposal.update(decision="accept",assetId="anatomy:workshop:s1233")
            path=root/"backfill.json";path.write_text(json.dumps(plan))
            applied=apply_backfill_plan(root,path)
            self.assertEqual(applied,["body/anatomy-workshop-r1/asset.record.json"])
            record=json.loads((root/applied[0]).read_text());self.assertEqual(record["status"],"provisional")
            self.assertIn("liver",{part["partId"] for part in record["parts"]})
            self.assertIn("s1233",{source["subjectCase"] for source in record["sources"]})
            self.assertIn("body/anatomy-workshop-r1/body-3d-delivery/meshes/liver.glb",
                {artifact["path"] for artifact in record["artifacts"]})
            self.assertIn("body/anatomy-workshop-r1/body-3d-delivery/meshes/liver.glb",
                {export["path"] for export in record["exports"]})
            self.assertTrue(record["unresolved"])
            self.assertEqual(apply_backfill_plan(root,path),[])
    def test_resolver_uses_explicit_package_sources_and_exact_assessment_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);catalog=build_catalog(root)
            body=resolve(catalog,"body-systems:digestive:digestive-liver")
            self.assertEqual(body["referencedPackages"][0]["packagePath"],"models/liver")
            payload=(root/"models/liver/liver.glb").read_bytes()
            export={"path":"models/liver/liver.glb","sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload)}
            assessment=Consumer("teaching-assessment:fixture","teaching-assessments","accepted-assessment",
                "Fixture · liver","Locate the liver.","accepted","reviews/fixture.json",
                {"export":export,"artifactPins":[export]})
            catalog=Catalog(catalog.repository,catalog.packages,(assessment,),catalog.source_hashes)
            resolved=resolve(catalog,"teaching-assessment:fixture")
            self.assertEqual(resolved["status"],"exact-export-candidate")
            self.assertEqual(resolved["exactExportCandidates"][0]["exportPath"],"models/liver/liver.glb")

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
            pointer=(b"version https://git-lfs.github.com/spec/v1\n"
                + b"oid sha256:"+remote_digest.encode()+b"\nsize "
                + str(len(remote)).encode()+b"\n")
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
