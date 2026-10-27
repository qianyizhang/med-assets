"""Pinned HRA GLB readers for this single editorial-window study."""

import hashlib

import json

from pathlib import Path

import struct

SOURCE_SHA = '7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd'

EDITED = {'Yao_capsule_of_lymph_node', 'Yao_medulla_of_lymph_node', 'Yao_blood_vasculature'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    data = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    if (magic, version, length) != (0x46546c67, 2, len(data)):
        raise ValueError('Invalid GLB header')
    n, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4e4f534a:
        raise ValueError('Missing JSON')
    doc = json.loads(data[20:20+n])
    off = 20+n
    size, kind = struct.unpack_from('<II', data, off)
    if kind != 0x004e4942 or off+8+size != len(data):
        raise ValueError('Expected one BIN chunk')
    return doc, data[off+8:off+8+size]

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

def write_glb(path, doc, binary):
    text=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
    text+=b' '*((-len(text))%4)
    binary+=b'\0'*((-len(binary))%4)
    data=struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))
    data+=struct.pack('<II',len(text),0x4e4f534a)+text
    data+=struct.pack('<II',len(binary),0x004e4942)+binary
    with path.open('xb') as f:
        f.write(data)
