import bpy,pathlib,json,hashlib,math,argparse,sys
parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);D=args.output
if D.exists():raise FileExistsError('Use a fresh evidence directory')
D.mkdir(parents=True)

for path,sha in [(args.source,'84d3f9559dac7bf175514194554d8ca5929f1d9d2666fae1bbc6b09512b4fca8'),(args.candidate,'3f4becca8672deb66267eac23e173ab62b75ac9e2c63510aecc7cd23f6a84272')]:
 if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Unexpected source/candidate identity')
results={}
for label,p in [('original',args.source),('updated',args.candidate)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p));r={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  mesh=o.data;mesh.calc_loop_triangles();coords=[tuple(o.matrix_world@v.co) for v in mesh.vertices]
  r[o.name]={'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'bbox':[[min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]],'finite':all(math.isfinite(x) for v in coords for x in v),'geometrySha256':hashlib.sha256(repr((coords,[tuple(t.vertices) for t in mesh.loop_triangles],[tuple(p.normal) for p in mesh.polygons])).encode()).hexdigest(),'matrix':list(sum((list(row) for row in o.matrix_world),[]))}
 results[label]=r
for n in results['original']:
 if n not in ['Fetal head','Forehead and face'] and results['original'][n]!=results['updated'][n]:raise ValueError('Changed unrelated imported mesh: '+n)
if not all(x['finite'] for x in results['updated'].values()):raise ValueError('Non-finite imported coordinates')
results['unrelated_meshes_exact_after_independent_import']=22
(D/'reimport-checks.json').write_text(json.dumps(results,indent=2))
print('PASS 22 unrelated reimported mesh/normal/matrix identities; all finite')
