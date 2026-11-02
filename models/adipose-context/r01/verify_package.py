"""Check pinned bytes and every delivered GLB primitive; not anatomy/runtime QA."""
from pathlib import Path
import hashlib,json,math,struct
if not __debug__:
 raise SystemExit("Optimized Python is not supported; assertions must remain enabled")
ROOT=Path(__file__).resolve().parent

def verify_glb(path):
 b=path.read_bytes()
 assert len(b)>=20 and b[:4]==b'glTF'
 assert struct.unpack_from('<II',b,4)==(2,len(b))
 chunks={};offset=12
 while offset<len(b):
  n,t=struct.unpack_from('<II',b,offset);offset+=8
  assert offset+n<=len(b) and n%4==0
  assert t not in chunks
  chunks[t]=b[offset:offset+n];offset+=n
 assert offset==len(b)
 j=json.loads(chunks[0x4E4F534A]);buf=chunks[0x004E4942]
 assert j['buffers'][0]['byteLength']<=len(buf)
 def accessor(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
  assert v.get('buffer',0)==0 and 'sparse' not in a
  widths={'SCALAR':1,'VEC3':3};formats={5123:'H',5125:'I',5126:'f'}
  width=widths[a['type']];fmt='<'+formats[a['componentType']]*width
  size=struct.calcsize(fmt);stride=v.get('byteStride',size);off=v.get('byteOffset',0)+a.get('byteOffset',0)
  assert stride>=size
  assert off+max(0,a['count']-1)*stride+size<=v.get('byteOffset',0)+v['byteLength']<=len(buf)
  return [struct.unpack_from(fmt,buf,off+k*stride) for k in range(a['count'])]
 triangles=0;count=0
 for mesh in j['meshes']:
  for p in mesh['primitives']:
   assert p.get('mode',4)==4
   pts=accessor(p['attributes']['POSITION'])
   assert all(math.isfinite(x) for q in pts for x in q)
   idx=[x[0] for x in accessor(p['indices'])]
   assert len(idx)%3==0 and all(0<=i<len(pts) for i in idx)
   triangles+=len(idx)//3;count+=1
 print(path.name, count,'primitives',triangles,'triangles: passed')
 assert count==4 and triangles==1760

REQUIRED={'geometry-verification.json', 'independent-review.json', 'comparison-zh.png', 'README.md', 'plate.py', 'comparison-en.png', 'verify_geometry.py', 'build-receipt.json', 'verify_package.py', 'replay-verification.json', 'build.py', 'selected-source-pads.glb', 'prepare_replay.py'}
rows=json.loads((ROOT/'package-manifest.json').read_text())
assert isinstance(rows,list) and len(rows)==len(REQUIRED)
assert {r['file'] for r in rows}==REQUIRED
for row in rows:
 rel=Path(row['file']);assert not rel.is_absolute() and '..' not in rel.parts
 p=ROOT/rel;assert not p.is_symlink() and p.resolve().is_relative_to(ROOT)
 b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['file']
for name in ['selected-source-pads.glb']:verify_glb(ROOT/name)
print('All pinned package bytes passed. Clinical/anatomical/live runtime not assessed.')
