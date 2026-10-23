"""Read-only exact container/scope check; not a render or anatomy test."""
from pathlib import Path
import hashlib,json,struct
r=Path(__file__).resolve().parents[2]
p=r/'models/tongue_authored_study/exports/authored-p11/tongue-authored-hra-hybrid-p11.glb'
b=p.read_bytes();assert len(b)==4983044 and hashlib.sha256(b).hexdigest()=='efabd58b235b72682f067113cf079e3f70fbaceac47062f2b937f09540c1ee1a'
assert b[:4]==b'glTF';n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);assert len(g['meshes'])==4 and not g.get('animations')
assert all('uri' not in x for x in g.get('buffers',[]))
assert all('uri' not in x for x in g.get('images',[]))
assert all(not any(k in x for k in ['matrix','translation','rotation','scale']) for x in g['nodes'])
print('Exact hash, four provenance meshes, embedded resources, identity nodes and no animation verified. No runtime/anatomy pass.')
