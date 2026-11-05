"""Pinned HRA GLB readers for this single editorial-window study."""

import hashlib
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.glb import decode, encode

SOURCE_SHA = '7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd'

EDITED = {'Yao_capsule_of_lymph_node', 'Yao_medulla_of_lymph_node', 'Yao_blood_vasculature'}

def sha(data):
    return hashlib.sha256(data).hexdigest()


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    if 'sparse' in a or a.get('normalized'):
        raise ValueError('Unsupported source accessor')
    size, fmt = {5123:(2,'H'), 5125:(4,'I'), 5126:(4,'f')}[a['componentType']]
    count = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
    b = doc['bufferViews'][a['bufferView']]
    start = b.get('byteOffset',0)+a.get('byteOffset',0)
    stride = b.get('byteStride',size*count)
    return [struct.unpack_from('<'+fmt*count,binary,start+i*stride) for i in range(a['count'])]

def world_blender(v):
    # The pinned source has no node transforms. Blender glTF import maps Y-up to Z-up.
    return (v[0],-v[2],v[1])

def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def load(path):
    return decode(Path(path).read_bytes())


def write_glb(path, doc, binary):
    with path.open('xb') as stream:
        stream.write(encode(doc, binary))
