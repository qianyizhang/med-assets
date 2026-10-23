"""Blender read-only exact-coordinate edge audit. Run --python this.py -- INPUT.glb OUTPUT.json.
The output must not exist. Closed incidence does not establish anatomical validity.
"""
import bpy,pathlib,json,hashlib,collections,sys
args=sys.argv[sys.argv.index('--')+1:]
if len(args)!=2: raise SystemExit('Expected INPUT.glb OUTPUT.json')
p=pathlib.Path(args[0]).resolve(); dest=pathlib.Path(args[1]).resolve()
if dest.exists(): raise SystemExit('Refusing to overwrite existing evidence')
if p.suffix.lower()!='.glb': raise SystemExit('Expected GLB input')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(p));rows=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 coords=[tuple(v.co) for v in ob.data.vertices];lookup={};remap=[]
 for c in coords:lookup.setdefault(c,len(lookup));remap.append(lookup[c])
 edges=collections.Counter();collapsed=0
 for f in ob.data.polygons:
  ids=[remap[x] for x in f.vertices];collapsed+=len(set(ids))<3
  for i,a in enumerate(ids):edges[tuple(sorted((a,ids[(i+1)%len(ids)])))]+=1
 rows.append({'id':ob.get('source_file_id',ob.name),'originalVertices':len(coords),'exactUniqueCoordinates':len(lookup),'duplicateCoordinates':len(coords)-len(lookup),'faces':len(ob.data.polygons),'collapsedFacesAfterExactRemap':collapsed,'boundaryEdges':sum(v==1 for v in edges.values()),'nonTwoIncidentEdges':sum(v!=2 for v in edges.values())})
record={'method':'Read-only explicit float-tuple equality remap; per-object edge incidence; no positional movement. Not BMesh remove_doubles(dist=0).','glbSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'objects':rows}
dest.parent.mkdir(parents=True,exist_ok=True)
with dest.open('x') as f: json.dump(record,f,indent=2)
print(json.dumps({'glbSha256':record['glbSha256'],'objects':len(rows),'boundaryEdges':sum(r['boundaryEdges'] for r in rows),'nonTwoIncidentEdges':sum(r['nonTwoIncidentEdges'] for r in rows)}))
