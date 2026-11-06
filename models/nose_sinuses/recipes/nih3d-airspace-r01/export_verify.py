import bpy,pathlib,json,numpy as np,hashlib,argparse,sys
from mathutils import Vector
from mathutils.kdtree import KDTree
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--record',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);S=pathlib.Path(a.source);C=pathlib.Path(a.candidate);O=pathlib.Path(a.out);r=json.load(open(a.record));assert hashlib.sha256(S.read_bytes()).hexdigest()==r['source_sha256']=='9c9d980edd1bb2d576376c0c486a3e45db65188c6ede72f3b2e1a56a1f7f9ba7','Source hash mismatch';assert hashlib.sha256(C.read_bytes()).hexdigest()==r['output_sha256'],'Candidate hash mismatch';O.mkdir(parents=True,exist_ok=False)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.wm.stl_import(filepath=str(S));o=bpy.context.object;x=np.array([v.co[:] for v in o.data.vertices]);f=np.array([p.vertices[:] for p in o.data.polygons]);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(C),merge_vertices=True);o=next(o for o in bpy.context.scene.objects if o.type=='MESH');y=np.array([o.matrix_world@v.co for v in o.data.vertices]);g=np.array([p.vertices[:] for p in o.data.polygons]);inv=y/r['display_scale']+np.array(r['source_center']);kd=KDTree(len(x))
for i,p in enumerate(x):kd.insert(p,i)
kd.balance();maps=[kd.find(p) for p in inv];ix=np.array([k[1] for k in maps]);dist=np.array([k[2] for k in maps])
def canonical(a):
 o=np.argmin(a,axis=1);v=np.take_along_axis(a,(o[:,None]+np.arange(3))%3,axis=1);return v[np.lexsort(v.T[::-1])]
out={'candidate_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'source_vertices':len(x),'export_vertices':len(y),'unique_bijection':len(np.unique(ix))==len(x)==len(y),'inverse_transform_max_error_nativeunits':float(dist.max()),'inverse_transform_max_error_fraction_longestextent':float(dist.max()/np.ptp(x,axis=0).max()),'oriented_triangles_preserved_after_mapping':bool(np.array_equal(canonical(f),canonical(ix[g]))),'units':'Unknown native STL units; no mm assertion','scope':'Source surface preserved within floatingpoint conversion. Source selfintersections remain; not a repair.'};(O/'export-preservation.json').write_text(json.dumps(out,indent=2));print(out)

# Recheck the4 previously detected non-shared-vertex source pairs after inverse conversion.
def hit(p,q,t):
 d=q-p;e1=t[1]-t[0];e2=t[2]-t[0];h=np.cross(d,e2);det=np.dot(e1,h)
 if abs(det)<1e-12:return False
 invdet=1/det;ss=p-t[0];uu=invdet*np.dot(ss,h);qq=np.cross(ss,e1);vv=invdet*np.dot(d,qq);aa=invdet*np.dot(e2,qq)
 return min(uu,vv,aa)>=-1e-8 and uu+vv<=1+1e-8 and aa<=1+1e-8
assert out['unique_bijection'] and out['oriented_triangles_preserved_after_mapping']
assert out['inverse_transform_max_error_fraction_longestextent']<1e-6,'Unexpected conversion displacement'
back=np.empty_like(inv);back[ix]=inv;rows=[]
for aa,bb in [(123870,123873),(160472,160475),(165396,166833),(165396,166832)]:
 A=back[f[aa]];B=back[f[bb]];n=sum(hit(s[i],s[(i+1)%3],t) for s,t in [(A,B),(B,A)] for i in range(3));rows.append({'source_triangle_pair':[aa,bb],'fresh_export_segment_triangle_hits':int(n)})
(O/'retained-defects.json').write_text(json.dumps({'rows':rows,'scope':'Only4known source pairs rechecked; not exhaustive intersection search or repair. Native units.'},indent=2));assert all(x['fresh_export_segment_triangle_hits']>0 for x in rows),'Source defect preservation requires investigation'
