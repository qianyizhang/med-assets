"""Payload-free source/camera guard; no rendering or anatomical inference."""
import hashlib
import json
import struct
from pathlib import Path
SOURCE_SHA = '4e2637cf6c844aef85ab77c2c1049d4e7647348a13c34d784795b98825f7c8c7'
CAMERA_SHA = '671e6c4db4791e76cef0960f0f3c85864f9a37ed2b73ac1636f93854d9bde064'
LABELS = [('gastric surface of spleen', 'FMA:15837'), ('diaphragmatic surface of spleen', 'FMA:15828'), ('colic surface of spleen', 'FMA:15838'), ('hilum of spleen', 'UBERON:0001248'), ('renal surface of spleen', 'FMA:15839')]

def verify_source(raw, expected_sha=SOURCE_SHA):
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Wrong exact source GLB')
    if len(raw) < 20 or raw[:4] != b'glTF' or struct.unpack_from('<I', raw, 4)[0] != 2 or struct.unpack_from('<I', raw, 8)[0] != len(raw):
        raise ValueError('Malformed GLB envelope')
    n, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A or n % 4 or 20+n > len(raw):
        raise ValueError('Malformed GLB JSON chunk')
    data = json.loads(raw[20:20+n])
    labels = [(x.get('extras', {}).get('label'), x.get('extras', {}).get('ontologyid')) for x in data['nodes'] if 'mesh' in x]
    if labels != LABELS:
        raise ValueError('Wrong source annotations')
    return data

def verify_camera(raw):
    if hashlib.sha256(raw).hexdigest() != CAMERA_SHA:
        raise ValueError('Wrong camera contract')

def require_new_output(path):
    if Path(path).exists():
        raise ValueError('Output must not exist; preserve previous drafts')
