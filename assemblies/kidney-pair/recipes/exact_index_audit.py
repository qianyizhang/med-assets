#!/usr/bin/env python3
"""One-off raw-GLB evidence extraction; no imports into Blender or geometry edits.
Usage: python kidney-exact-index-audit.py SOURCE.glb CANDIDATE.glb > NEW_REPORT.json
"""
import collections,hashlib,json,struct,sys
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def audit(name):
 p=Path(name);raw=p.read_bytes();assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
 chunks={};o=12
 while o<len(raw):
  n,k=struct.unpack_from('<II',raw,o);chunks[k]=raw[o+8:o+8+n];o+=8+n
 g=json.loads(chunks[0x4e4f534a]);b=chunks[0x004e4942]
 def accessor(i):
  a=g['accessors'][i];assert 'sparse' not in a;v=g['bufferViews'][a['bufferView']];fmt='<'+{5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]*{'SCALAR':1,'VEC3':3}[a['type']];size=struct.calcsize(fmt);stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0)
  return [struct.unpack_from(fmt,b,start+k*stride) for k in range(a['count'])]
 rows=[];total=0
 for mi,m in enumerate(g['meshes']):
  for pi,p in enumerate(m['primitives']):
   assert p.get('mode',4)==4;pos=accessor(p['attributes']['POSITION']);idx=[x[0] for x in accessor(p['indices'])];assert len(idx)%3==0;total+=len(idx)//3
   hits=[];edges=collections.Counter();edges_without=collections.Counter()
   for j in range(0,len(idx),3):
    ids=idx[j:j+3];coords=[pos[i] for i in ids];collapsed=len(set(coords))<3
    if collapsed:hits.append({'triangleOrdinalZeroBased':j//3,'indexStreamOffsetZeroBased':j,'indices':ids,'positions':coords,'distinctIndexCount':len(set(ids)),'distinctExactPositionCount':len(set(coords))})
    for k in range(3):
     edge=tuple(sorted([coords[k],coords[(k+1)%3]]));edges[edge]+=1
     if not collapsed:edges_without[edge]+=1
   if hits:rows.append({'meshIndex':mi,'meshName':m.get('name'),'primitiveIndex':pi,'positionAccessor':p['attributes']['POSITION'],'indexAccessor':p['indices'],'positionRows':len(pos),'uniqueExactPositions':len(set(pos)),'indexedTriangles':len(idx)//3,'collapsedTriangles':hits,'boundaryEdgesIncludingCollapsed':sum(v==1 for v in edges.values()),'overusedEdgesIncludingCollapsed':sum(v>2 for v in edges.values()),'overusedEdgesExcludingCollapsed':sum(v>2 for v in edges_without.values())})
 return {'fileName':Path(name).name,'sha256':sha(raw),'binSha256':sha(b),'binBytes':len(b),'indexedTriangles':total,'collapsedTriangleCount':sum(len(x['collapsedTriangles']) for x in rows),'affectedPrimitives':rows}
s,c=map(audit,sys.argv[1:3]);assert s['binSha256']==c['binSha256'];assert s['affectedPrimitives']==c['affectedPrimitives']
print(json.dumps({'scope':'Read-only exact-index/position-tuple diagnostic on supplied left kidney GLBs only. No geometry change, Blender reimport, epsilon weld, clinical or runtime conclusion.','definition':'A triangle is collapsed when fewer than 3 distinct decoded float32 POSITION tuples remain for its 3 indexed corners, using exact equality. Different indices at exactly equal coordinates count as one position. This is not an epsilon-based near-degeneracy test.','scriptSha256':sha(Path(__file__).read_bytes()),'pythonVersion':sys.version,'source':s,'candidate':c,'geometryPreservationEvidence':'BIN chunks and affected-primitive details identical.','gateEffect':'None. Existing scoped visual approval and pass-with-limitations technical status can coexist with inherited topology warnings; anatomy/runtime not inferred.'},indent=2))
