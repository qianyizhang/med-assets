import json
from pathlib import Path
import tempfile
import unittest

from tools.verify_recipe_dependencies import owner_configs, verify_graph


class RecipeDependenciesTest(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_follows_blender_subprocess_to_adjacent_recipe(self):
        self.write("models/example/replay.py", '''
import subprocess
subprocess.run(["blender", "--python", str(HERE / "export.py")])
''')
        self.write("models/example/export.py", "runpy.run_path(str(ROOT / 'reviews' / 'old.py'))")
        with self.assertRaisesRegex(ValueError, "export.py depends on historical"):
            verify_graph(self.root, ["models/example/replay.py"])

    def test_rejects_a_site_path_in_json_config(self):
        self.write("lessons/example/views.json", json.dumps({"camera": "../../sites/old/pose.json"}))
        with self.assertRaisesRegex(ValueError, "views.json depends on historical or site"):
            verify_graph(self.root, ["lessons/example/views.json"])

    def test_checks_lfs_declarations_without_hydration(self):
        self.write("models/example/build.py", "config = Path(__file__).with_name('inputs.json')")
        self.write("models/example/member.glb",
                   "version https://git-lfs.github.com/spec/v1\noid sha256:" + "a" * 64 + "\nsize 300\n")
        config = {"source": {"path": "models/example/member.glb", "sha256": "a" * 64, "bytes": 300}}
        self.write("models/example/inputs.json", json.dumps(config))
        checked = verify_graph(self.root, ["models/example/build.py"])
        self.assertIn("models/example/member.glb", checked)
        config["source"]["bytes"] = 301
        self.write("models/example/inputs.json", json.dumps(config))
        with self.assertRaisesRegex(ValueError, "stale input or output identity"):
            verify_graph(self.root, ["models/example/build.py"])


    def test_missing_owner_config_fails_documented_rebuild(self):
        for area in ("models", "assemblies", "body", "heart", "lessons"):
            (self.root / area).mkdir()
        self.write("models/example/exports/r01/README.md",
                   "python3.12 tools/rebuild_asset.py models/example/recipes/r01.json .artifacts/example")
        with self.assertRaisesRegex(ValueError, "Missing recipes:.*models/example/recipes/r01.json"):
            owner_configs(self.root)
