import bpy,pathlib,json,hashlib,numpy as np
import argparse,sys
a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--work',required=True);args=a.parse_args(sys.argv[sys.argv.index('--')+1:]);P=pathlib.Path(__file__).resolve().parent;O=pathlib.Path(args.work);source=pathlib.Path(args.source);data=np.load(O/'vertex-invariants.npz');base=data['baseline'];new=data['candidate'];weights=data['weights'];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(source),merge_vertices=True);o=next(x for x in bpy.context.scene.objects if x.type=='MESH');faces=np.array([p.vertices[:] for p in o.data.polygons]);assert faces.shape[1]==3
bn=np.cross(base[faces[:,1]]-base[faces[:,0]],base[faces[:,2]]-base[faces[:,0]]);nn=np.cross(new[faces[:,1]]-new[faces[:,0]],new[faces[:,2]]-new[faces[:,0]]);dots=(bn*nn).sum(axis=1);changed=np.any(weights[faces]>0,axis=1)
def section(v,x):
 tri=v[faces];mask=(tri[:,:,0].min(axis=1)<x)&(tri[:,:,0].max(axis=1)>x);tri=tri[mask];area=0.;count=0
 for q in tri:
  pts=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if (q[i,0]-x)*(q[j,0]-x)<0:pts.append(q[i]+(q[j]-q[i])*(x-q[i,0])/(q[j,0]-q[i,0]))
  if len(pts)==2:
   a,b=pts;n=np.cross(q[1]-q[0],q[2]-q[0]);direction=np.cross(np.array([1.,0,0]),n)
   if np.dot(b-a,direction)<0:a,b=b,a
   area+=(a[1]*b[2]-a[2]*b[1])/2;count+=1
 return abs(area),count
sections=[]
for x in np.linspace(.032,.054,12):
 a,n=section(base,x);b,m=section(new,x);sections.append({'x_m':float(x),'before_area_mm2':a*1e6,'after_area_mm2':b*1e6,'relative_area_change':(b-a)/a,'segment_count_before':n,'segment_count_after':m})
q={'terminal_witnesses':json.load(open(P/'terminal-witnesses.json'))};ts=[]
for row in q['terminal_witnesses']:
 p=np.array(row['authored_recipe_position']);near=np.linalg.norm(base-p,axis=1)<.006;ts.append({'name':row['name'],'vertices_within6mm':int(near.sum()),'all_unchanged':bool(np.array_equal(base[near],new[near]))})
r={'triangles_connectivity_sha256':hashlib.sha256(faces.tobytes()).hexdigest(),'changed_region_triangles':int(changed.sum()),'nonpositive_orientation_dot':int((dots<=0).sum()),'outside_support_vertices':int((weights==0).sum()),'outside_support_exact':bool(np.array_equal(base[weights==0],new[weights==0])),'local_triangle_area_change':float(np.linalg.norm(nn[changed],axis=1).sum()/np.linalg.norm(bn[changed],axis=1).sum()-1),'sections':sections,'section_scope':'Whole mesh x-plane signed area; nearby unmodified thin crossings included equally. Not clinical lumen area.','terminal_neighborhoods':ts}
(O/'local-geometry-check.json').write_text(json.dumps(r,indent=2));print(r['local_triangle_area_change'],max(abs(s['relative_area_change']) for s in sections))
