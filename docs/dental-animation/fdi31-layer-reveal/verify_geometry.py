"""Compare decoded imported mesh vertices/topology, not only whole-file identity."""
import bpy,hashlib,json,sys,struct,pathlib
from mathutils import Vector
source,scene,out=sys.argv[sys.argv.index('--')+1:]
def signatures():
 d={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH': continue
  v=b''.join(struct.pack('<3f',*x.co) for x in o.data.vertices)
  f=b''.join(struct.pack('<I',len(p.vertices))+struct.pack('<'+'I'*len(p.vertices),*p.vertices) for p in o.data.polygons)
  d[o.name.split('/')[-1]]={'vertex_count':len(o.data.vertices),'face_count':len(o.data.polygons),'vertices_sha256':hashlib.sha256(v).hexdigest(),'topology_sha256':hashlib.sha256(f).hexdigest()}
 return d
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(scene).resolve()));a=signatures()
locs=[tuple(o.location) for o in bpy.context.scene.objects if o.type=='MESH'];reset=max((Vector(l)-Vector(locs[0])).length for l in locs)==0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(source).resolve()));b=signatures()
r={'geometry_identical':a==b,'relative_source_reset_exact':reset,'source_sha256':hashlib.sha256(pathlib.Path(source).read_bytes()).hexdigest(),'mesh_signatures':a,'clinical_validation':False,'physiological_motion':False}
pathlib.Path(out).write_text(json.dumps(r,indent=2));assert r['geometry_identical'] and reset;print(json.dumps(r))
