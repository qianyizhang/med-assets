"""Container boundaries shared by asset recipes; no geometry or anatomy claim."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.glb import decode, encode


def container(json_bytes=b'{}  ', binary=b'abcd', *, kinds=(0x4E4F534A, 0x004E4942)):
    body = (struct.pack('<II', len(json_bytes), kinds[0]) + json_bytes
            + struct.pack('<II', len(binary), kinds[1]) + binary)
    return struct.pack('<4sII', b'glTF', 2, 12 + len(body)) + body


class GLBTests(unittest.TestCase):
    def test_read_independent_container_and_empty_binary(self):
        self.assertEqual(decode(container()), ({}, b'abcd'))
        self.assertEqual(decode(container(binary=b'')), ({}, b''))

    def test_utf8_roundtrip_preserves_binary_and_document(self):
        document = {'name': '眼 · ovary', 'extras': {'purpose': 'fixture'}}
        binary = bytearray(b'\xff\x00\x12\x80')
        raw = encode(document, binary)
        self.assertIn('眼'.encode(), raw)
        self.assertEqual(decode(raw), (document, bytes(binary)))
        self.assertEqual(binary, bytearray(b'\xff\x00\x12\x80'))
        self.assertEqual(encode(*decode(raw)), raw)

    def test_encoding_matches_fixed_container(self):
        self.assertEqual(encode({}, b'abcd'), container())
        self.assertEqual(encode({}, b''), container(binary=b''))

    def test_padding_is_explicit_and_does_not_modify_input(self):
        payload = bytearray(b'abc')
        self.assertEqual(decode(encode({}, payload)), ({}, b'abc\0'))
        self.assertEqual(payload, b'abc')
        with self.assertRaisesRegex(ValueError, 'Unaligned buffer'):
            encode({}, payload, pad_binary=False)
        self.assertEqual(encode({}, b'abcd', pad_binary=False), container())

    def test_rejects_every_truncation_and_wrong_declared_length(self):
        raw = container()
        for length in range(len(raw)):
            with self.subTest(length=length), self.assertRaises(ValueError):
                decode(raw[:length])
        for length in (0, len(raw) - 1, len(raw) + 1, 0xFFFFFFFF):
            bad = raw[:8] + struct.pack('<I', length) + raw[12:]
            with self.subTest(declared=length), self.assertRaises(ValueError):
                decode(bad)

    def test_rejects_chunk_order_types_alignment_and_trailing_data(self):
        for raw in (
            container(kinds=(0x004E4942, 0x4E4F534A)),
            container(kinds=(0x4E4F534A, 0x4E4F534A)),
            container(kinds=(0x4E4F534A, 7)),
            container(json_bytes=b'{} '),
            container(binary=b'abc'),
            container() + b'extra',
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw)
        raw = container() + struct.pack('<II', 0, 7)
        raw = raw[:8] + struct.pack('<I', len(raw)) + raw[12:]
        with self.assertRaises(ValueError):
            decode(raw)

    def test_rejects_out_of_bounds_chunk_sizes_before_unpacking(self):
        raw = container()
        for offset in (12, 24):
            bad = raw[:offset] + struct.pack('<I', 0xFFFFFFFC) + raw[offset + 4:]
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                decode(bad)

    def test_rejects_invalid_utf8_json_and_nonobject_json(self):
        for text in (b'\xff\xff\xff\xff', b'nope', b'[]  ', b'null', b'"a" ', b''):
            with self.subTest(text=text), self.assertRaises(ValueError):
                decode(container(json_bytes=text))
        with self.assertRaises(ValueError):
            encode([], b'')

    def test_rejects_wrong_header_and_lfs_pointer(self):
        raw = container()
        for value in (b'version https://git-lfs.github.com/spec/v1\n', b'',
                      b'nope' + raw[4:], raw[:4] + struct.pack('<I', 1) + raw[8:]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode(value)

    def test_leaves_buffer_and_accessor_policy_to_asset(self):
        document = {'buffers': [{'uri': 'source.bin', 'byteLength': 4}]}
        self.assertEqual(decode(encode(document, b'')), (document, b''))
