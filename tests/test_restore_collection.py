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

    def test_wrong_catalog_totals_fail_before_install(self):
        for totals in ({"payloads": 1}, {"payloadBytes": 3}):
            with self.subTest(totals=totals), self.assertRaisesRegex(ValueError, "count or total size"):
                restore({**self.row, **totals}, self.output, self.archive)
            self.assertFalse(self.output.exists())

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
        with self.assertRaisesRegex(ValueError, "size or SHA-256"):
            self.run_restore()
        self.assertFalse((folder / "a.glb").exists())
        self.assertEqual((folder / "b.glb").read_bytes(), b"edited")

    def test_rejects_changed_zip_and_symlink_destination(self):
        self.output.mkdir()
        (self.output / "sources").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Linked"):
            self.run_restore()
        self.archive.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "size or SHA-256"):
            self.run_restore()

    def test_external_checksums_subset_and_conflicting_member_set(self):
        names = {"films/a.mp4": b"film", "notes.md": b"credit"}
        with ZipFile(self.archive, "w") as archive:
            for key, value in names.items():
                archive.writestr(key, value)
        checks = self.root / "SHA256SUMS"
        checks.write_text("".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in names.items()))
        def identity(path):
            return {"path": path.name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        row = {**identity(self.archive), "file": self.archive.name, "checksumList": identity(checks),
               "payloads": 2, "subsets": {"films": "films"}}
        self.assertEqual(restore(row, self.output, self.archive, subset="films", repo=self.root), 1)
        self.assertFalse((self.output / "notes.md").exists())
        self.assertEqual(restore(row, self.output, self.archive, subset="films", repo=self.root), 0)
        with self.assertRaisesRegex(ValueError, "Unknown collection subset"):
            restore(row, self.output, self.archive, subset="unknown", repo=self.root)
        with ZipFile(self.archive, "a") as archive:
            archive.writestr("unlisted.txt", "extra")
        row.update(identity(self.archive))
        with self.assertRaisesRegex(ValueError, "differ from its member manifest"):
            restore(row, self.output, self.archive, repo=self.root)
        self.assertFalse((self.output / "notes.md").exists())
