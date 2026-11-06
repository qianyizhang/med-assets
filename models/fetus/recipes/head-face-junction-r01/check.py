import json,struct,hashlib,math,pathlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--candidate',type=pathlib.Path,required=True);args=parser.parse_args()
def glb(p):
 b=p.read_bytes();magic,v,total=struct.unpack_from('<III',b);
 if (magic,v,total)!=(0x46546c67,2,len(b)):raise ValueError('Invalid GLB header')
 L=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+L]),b[28+L:]
for file,expected in [(args.source,'84d3f9559dac7bf175514194554d8ca5929f1d9d2666fae1bbc6b09512b4fca8'),(args.candidate,'3f4becca8672deb66267eac23e173ab62b75ac9e2c63510aecc7cd23f6a84272')]:
 if hashlib.sha256(file.read_bytes()).hexdigest()!=expected:raise ValueError('Unexpected artifact identity: '+str(file))
a,ab=glb(args.source);b,bb=glb(args.candidate)
checks={}
def ck(n,v):
 if not v:raise ValueError(n)
 checks[n]=True
ck('all_original_BIN_bytes_exact',bb[:len(ab)]==ab)
ck('22_unrelated_nodes_exact',a['nodes'][2:]==b['nodes'][2:])
ck('all_original_mesh_definitions_exact',a['meshes']==b['meshes'][:-1])
ck('materials_exact',a['materials']==b['materials'])
ck('scene_roots_exact',a['scenes']==b['scenes'])
for i in [0,1]:ck(f'node_{i}_transform_metadata_exact',{k:v for k,v in a['nodes'][i].items() if k!='mesh'}=={k:v for k,v in b['nodes'][i].items() if k!='mesh'})
ck('only_node0_replaced_node1_mesh_removed',b['nodes'][0]['mesh']==24 and 'mesh' not in b['nodes'][1])
def acc(i):
 x=b['accessors'][i];v=b['bufferViews'][x['bufferView']];n={'VEC3':3,'SCALAR':1}[x['type']];fmt={5126:'f',5123:'H'}[x['componentType']];t=struct.unpack_from('<'+fmt*(x['count']*n),bb,v.get('byteOffset',0)+x.get('byteOffset',0));return [t[j:j+n] for j in range(0,len(t),n)]
p=b['meshes'][-1]['primitives'][0];pos=acc(p['attributes']['POSITION']);norm=acc(p['attributes']['NORMAL']);ix=[x[0] for x in acc(p['indices'])]
ck('positions_normals_finite',all(math.isfinite(v) for row in pos+norm for v in row))
ck('normals_unit',all(abs(sum(v*v for v in row)-1)<1e-5 for row in norm))
ck('indices_in_range',min(ix)>=0 and max(ix)<len(pos))
minarea=1
for i in range(0,len(ix),3):
 x,y,z=[pos[k] for k in ix[i:i+3]];u=[y[k]-x[k] for k in range(3)];v=[z[k]-x[k] for k in range(3)];c=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];minarea=min(minarea,math.sqrt(sum(t*t for t in c))/2)
ck('no_zero_area_faces',minarea>1e-12)
# Compare decoded accessor streams for every non-target primitive, exhaustive bytes already checked above.
ck('unrelated_accessors_views_exact',a['accessors']==b['accessors'][:len(a['accessors'])] and a['bufferViews']==b['bufferViews'][:len(a['bufferViews'])])
report={'checks':checks,'passed':len(checks),'minimum_head_triangle_area_m2':minarea,'new_active_head_triangles':len(ix)//3,'limits':['Technical checks only; render review separate','No anatomical/clinical or live runtime acceptance','Original inactive two-head mesh buffers retained, not optimized away']}
print(json.dumps(report,indent=2))
