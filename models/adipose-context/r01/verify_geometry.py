import bpy, json, hashlib, math
from pathlib import Path
R=Path(__file__).resolve().parent; SRC=R/'source/Network_Systems_Draft.blend'
def sig():
 out={}
 for o in bpy.data.objects:
  if not o.name.startswith(('Abdominal subcutaneous pad','Flank pad')):continue
  mesh=o.data; mesh.calc_loop_triangles();vs=[tuple(round(float(x),6) for x in (o.matrix_world@v.co)) for v in mesh.vertices]
  out[o.name]={'vertices':sorted(set(vs)),'triangles':sorted(tuple(sorted(vs[i] for i in t.vertices)) for t in mesh.loop_triangles)}
 return out
bpy.ops.wm.open_mainfile(filepath=str(SRC));a=sig();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'selected-source-pads.glb'));b=sig();assert a==b
receipt={'status':'passed','comparison':'Exact equality of canonical world-space triangle multisets, quantized to 1e-6 m; unique vertex coordinates also compared. GLB seam duplicates ignored, connectivity retained.','source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((R/'selected-source-pads.glb').read_bytes()).hexdigest(),'objects':{k:{'unique_vertices':len(v['vertices']),'triangles':len(v['triangles'])}for k,v in a.items()},'finite':all(math.isfinite(x) for v in b.values() for p in v['vertices'] for x in p)}
assert receipt['finite'];(R/'geometry-verification.json').write_text(json.dumps(receipt,indent=2));print('GEOMETRY_PASS')
