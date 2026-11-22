import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "transport/tools"))
from restore_collection import restore


class CollectionRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.output = self.root / "restored"
        buffer = io.BytesIO()
        hashes = {}
        with ZipFile(buffer, "w") as archive:
            for name, data in [("sources/a.glb", b"a"), ("sources/b.glb", b"b")]:
                hashes[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "role": "payload"}
                archive.writestr(name, data)
            archive.writestr("members.json", json.dumps(hashes))
        data = buffer.getvalue()
        self.archive = self.root / "test.zip"
        self.archive.write_bytes(data)
        self.row = {"file": self.archive.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

    def run_restore(self):
        return restore(self.row, self.output, self.archive)

    def test_restore_and_retry(self):
        self.assertEqual(self.run_restore(), 2)
        self.assertEqual((self.output / "sources/a.glb").read_bytes(), b"a")
        self.assertEqual(self.run_restore(), 0)

    def test_download_uses_the_object_library_client(self):
        row = {**self.row, "key": "library/med-assets/collections/test.zip"}
        with patch("restore_collection.build_opener") as opener:
            read = opener.return_value.open
            read.return_value = io.BytesIO(self.archive.read_bytes())
            self.assertEqual(restore(row, self.output), 2)
            request = read.call_args.args[0]
            self.assertEqual(request.get_header("User-agent"), "ObjectLibraryCLI/1.1")
            self.assertEqual(request.full_url, "https://r2-object-library.landy123007.chatgpt.site/download?key=library%2Fmed-assets%2Fcollections%2Ftest.zip")

    def test_conflict_prevents_partial_write(self):
        folder = self.output / "sources"
        folder.mkdir(parents=True)
        (folder / "b.glb").write_bytes(b"edited")
        with self.assertRaisesRegex(ValueError, "Byte identity"):
            self.run_restore()
        self.assertFalse((folder / "a.glb").exists())
        self.assertEqual((folder / "b.glb").read_bytes(), b"edited")

    def test_rejects_changed_zip_and_symlink_destination(self):
        self.output.mkdir()
        (self.output / "sources").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.run_restore()
        self.archive.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Byte identity"):
            self.run_restore()
