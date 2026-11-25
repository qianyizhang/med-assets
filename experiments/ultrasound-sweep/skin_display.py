"""Derive the display-only atlas exterior from the pinned acquisition skin mesh."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

FACE_SELECTION = Path(__file__).parent / 'carotid-survey/skin-display-faces.json'


def exterior_mesh(raw: bytes) -> bytes:
    """Copy only source outer triangles, preserving exact positions and correcting mirrored winding."""
    selection = json.loads(FACE_SELECTION.read_text())
    if hashlib.sha256(raw).hexdigest() != selection['sourcePackedSha256']:
        raise ValueError('Display skin selection does not match this acquisition mesh')
    vertices, faces = struct.unpack_from('<II', raw)
    face_start = 8 + 12 * vertices
    if faces != selection['sourceTriangles'] or len(raw) != face_start + 12 * faces:
        raise ValueError('Unexpected acquisition skin topology')

    elements = []
    stop = 0
    for begin, end, mirrored in selection['faceRanges']:
        if not stop <= begin < end <= faces:
            raise ValueError('Invalid display skin face range')
        offset = face_start + 12 * begin
        triangles = struct.iter_unpack('<III', raw[offset:face_start + 12 * end])
        elements.extend((a, c, b) if mirrored else (a, b, c) for a, b, c in triangles)
        stop = end
    if len(elements) != selection['exteriorTriangles']:
        raise ValueError('Unexpected display skin triangle count')
    used = sorted({index for triangle in elements for index in triangle})
    remap = {index: compact for compact, index in enumerate(used)}
    positions = b''.join(raw[8 + 12 * index:8 + 12 * (index + 1)] for index in used)
    triangles = b''.join(struct.pack('<III', *(remap[index] for index in face)) for face in elements)
    return struct.pack('<II', len(used), len(elements)) + positions + triangles


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('display', type=Path)
    args = parser.parse_args()
    payload = exterior_mesh(args.original.read_bytes())
    with args.display.open('xb') as stream:
        stream.write(payload)
