"""CPU capture-format checks; no browser launch or rendering claim."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ci'))
import glb_runtime_probe as glb
import webgl_probe as webgl
sys.path.pop(0)


def xwd(order=0, **changes):
    """A padded two-row TrueColor image with a window name and color table."""
    fields = dict(header=104, version=7, fmt=2, depth=24, width=2, height=2,
                  offset=0, order=order, bpp=32, stride=12, visual=4,
                  red=0xff0000, green=0xff00, blue=0xff, ncolors=1)
    fields.update(changes)
    header = [0] * 25
    for index, name in {0:'header', 1:'version', 2:'fmt', 3:'depth', 4:'width',
                        5:'height', 6:'offset', 7:'order', 11:'bpp', 12:'stride',
                        13:'visual', 14:'red', 15:'green', 16:'blue', 19:'ncolors'}.items():
        header[index] = fields[name]
    endian = 'little' if order == 0 else 'big'
    rows = ((0x1acc4d, 0xcc33b3), (0x000000, 0xffffff))
    pixels = b''.join(b''.join(p.to_bytes(4, endian) for p in row) + b'pad!' for row in rows)
    return struct.pack('>25I', *header) + b'win\0' + bytes(12) + pixels


class RuntimeCaptureTests(unittest.TestCase):
    def test_both_byte_orders_padding_and_triangle_counts(self):
        rgb = bytes((26, 204, 77, 204, 51, 179, 0, 0, 0, 255, 255, 255))
        for order in (0, 1):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(glb.decode_xwd(xwd(order)), (2, 2, rgb))
                target = Path(directory) / 'display.png'
                result = webgl.xwd_to_png(xwd(order), target)
                self.assertEqual(result['triangleColorPixels'], {'webgl2':1, 'webgl':1})
                self.assertEqual((result['width'], result['height']), (2, 2))
                self.assertEqual(target.read_bytes(), glb.png(2, 2, rgb))
                self.assertEqual(result['sha256'], hashlib.sha256(target.read_bytes()).hexdigest())

    def test_png_is_rgb_with_unfiltered_rows_and_valid_chunks(self):
        rgb = bytes((1, 2, 3, 4, 5, 6))
        encoded = glb.png(1, 2, rgb)
        self.assertEqual(encoded[:8], b'\x89PNG\r\n\x1a\n')
        chunks = []
        offset = 8
        while offset < len(encoded):
            length, kind = struct.unpack_from('>I4s', encoded, offset)
            payload = encoded[offset + 8:offset + 8 + length]
            crc, = struct.unpack_from('>I', encoded, offset + 8 + length)
            self.assertEqual(crc, zlib.crc32(kind + payload) & 0xffffffff)
            chunks.append((kind, payload))
            offset += 12 + length
        self.assertEqual([kind for kind, _ in chunks], [b'IHDR', b'IDAT', b'IEND'])
        self.assertEqual(chunks[0][1], struct.pack('>2I5B', 1, 2, 8, 2, 0, 0, 0))
        self.assertEqual(zlib.decompress(chunks[1][1]), b'\0\1\2\3\0\4\5\6')
        self.assertEqual(chunks[2][1], b'')

    def test_malformed_capture_rejected_before_writing(self):
        invalid = [xwd()[:99], xwd()[:-1]]
        invalid += [xwd(**{field:value}) for field, value in (
            ('header', 99), ('header', 4097), ('version', 8), ('fmt', 1),
            ('depth', 32), ('width', 0), ('width', 4097), ('height', 0),
            ('height', 4097), ('offset', 1), ('order', 2), ('bpp', 24),
            ('stride', 7), ('stride', 32769), ('visual', 3), ('red', 0xff),
            ('green', 0xff0000), ('blue', 0xff00), ('ncolors', 65537))]
        for index, data in enumerate(invalid):
            with self.subTest(case=index), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'display.png'
                with self.assertRaises(ValueError):
                    glb.decode_xwd(data)
                with self.assertRaises(ValueError):
                    webgl.xwd_to_png(data, target)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
