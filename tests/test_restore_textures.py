import hashlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import glb
import restore_textures


class RestoreTexturesTests(unittest.TestCase):
    def test_restore_checks_all_pins_before_writing_and_never_replaces_edits(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            mesh, directory = root / 'mesh.glb', root / 'textures'
            document = {'images': [{'name': name, 'mimeType': 'image/png', 'bufferView': i}
                                   for i, name in enumerate(('color', 'normal'))],
                        'bufferViews': [{'buffer': 0, 'byteOffset': n, 'byteLength': 4} for n in (0, 4)]}
            mesh.write_bytes(glb.encode(document, b'12345678'))
            pins = {'color.png': hashlib.sha256(b'1234').hexdigest(), 'normal.png': 'wrong'}
            with patch.object(restore_textures, 'texture_sources', return_value={mesh: pins}):
                with self.assertRaisesRegex(ValueError, 'changed texture'):
                    restore_textures.restore('workshop', directory)
                self.assertFalse(directory.exists())
                pins['normal.png'] = hashlib.sha256(b'5678').hexdigest()
                self.assertEqual(restore_textures.restore('workshop', directory), 2)
                self.assertEqual(restore_textures.restore('workshop', directory), 0)
                (directory / 'color.png').unlink()
                (directory / 'normal.png').write_bytes(b'edited')
                with self.assertRaisesRegex(ValueError, 'Existing texture differs'):
                    restore_textures.restore('workshop', directory)
                self.assertFalse((directory / 'color.png').exists())
                self.assertEqual((directory / 'normal.png').read_bytes(), b'edited')
