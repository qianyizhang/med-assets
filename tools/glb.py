"""Strict GLB 2 JSON/BIN containers; asset and accessor policies belong to callers."""
import json
import struct

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def decode(data):
    """Read exactly one aligned JSON chunk followed by one aligned BIN chunk."""
    if len(data) < 28 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError('Invalid GLB 2 header or unresolved payload')
    json_size, kind = struct.unpack_from('<II', data, 12)
    if kind != JSON_CHUNK or json_size % 4 or 28 + json_size > len(data):
        raise ValueError('Invalid GLB JSON chunk')
    cursor = 20 + json_size
    binary_size, kind = struct.unpack_from('<II', data, cursor)
    if kind != BIN_CHUNK or binary_size % 4 or cursor + 8 + binary_size != len(data):
        raise ValueError('Expected exactly one aligned GLB BIN chunk')
    try:
        document = json.loads(data[20:cursor].decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid UTF-8 GLB JSON') from error
    if not isinstance(document, dict):
        raise ValueError('GLB JSON must be an object')
    return document, data[cursor + 8:]


def encode(document, binary, *, pad_binary=True):
    """Encode compact UTF-8 JSON; retain BIN bytes, optionally adding zero padding."""
    if not isinstance(document, dict):
        raise ValueError('GLB JSON must be an object')
    if not pad_binary and len(binary) % 4:
        raise ValueError('Unaligned buffer')
    text = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    text += b' ' * (-len(text) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(text) + len(binary))
            + struct.pack('<II', len(text), JSON_CHUNK) + text
            + struct.pack('<II', len(binary), BIN_CHUNK) + binary)
