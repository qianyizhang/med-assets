"""Interrupted multi-record backfill is safely resumable."""
import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from med_assets.governance_migration import create_backfill_plan, apply_backfill_plan, _atomic

class BackfillRecoveryTests(unittest.TestCase):
    def test_interrupted_batch_resumes_without_rewriting_completed_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ("alpha","beta"):
                package=root/"models"/name; package.mkdir(parents=True)
                (package/"README.md").write_text(f"# {name}\n")
                (package/f"{name}.glb").write_bytes((name+" geometry").encode())
            plan=create_backfill_plan(root)
            for index,row in enumerate(plan["proposals"]):
                row["decision"]="accept"; row["assetId"]=f"anatomy:{row['packagePath'].split('/')[-1]}"
            path=root/"backfill.plan.json"; path.write_text(json.dumps(plan))
            original=_atomic; calls={"count":0}
            def interrupted(destination,data):
                calls["count"]+=1
                if calls["count"]==2:
                    raise OSError("simulated process interruption")
                return original(destination,data)
            with patch("med_assets.governance_migration._atomic",side_effect=interrupted):
                with self.assertRaisesRegex(OSError,"interruption"):
                    apply_backfill_plan(root,path)
            first=list(root.glob("models/*/asset.record.json"))
            self.assertEqual(len(first),1)
            completed=first[0].read_bytes()
            applied=apply_backfill_plan(root,path)
            self.assertEqual(len(applied),1)
            self.assertEqual(len(list(root.glob("models/*/asset.record.json"))),2)
            self.assertEqual(first[0].read_bytes(),completed)

if __name__=="__main__": unittest.main()
