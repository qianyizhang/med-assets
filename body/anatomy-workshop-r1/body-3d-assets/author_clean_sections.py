exec(open(__file__.replace('author_clean_sections.py','refine_and_preview.py')).read().split('for ma in bpy.data.materials:')[0])
from mathutils.geometry import tessellate_polygon
sources={o['source_file'][:-5]:o for o in bpy.data.objects if 'source_file' in o and o.get('view_role')=='surface'}
for id in ['kidney_left','kidney_right','stomach']:
 for ob in list(objects[id]):
  if ob.get('view_role')!='surface':objects[id].remove(ob);bpy.data.objects.remove(ob,do_unlink=True)

def closed_back_section(id,outline,c,front,depth,ma,inner_ma):
 # Explicit authored teaching cup with a continuous backing; no fragile source Boolean.
 N=len(outline);center=Vector((c.x,c.z));inner=[center+(p-center)*.79 for p in outline];back=front+depth;vs=[]
 for ring,y in [(outline,front),(inner,front),(outline,back+.003),(inner,back)]:vs.extend((p.x,y,p.y) for p in ring)
 fs=[];mi=[]
 for k in range(N):
  q=(k+1)%N
  fs.extend([(k,q,N+q,N+k),(k,2*N+k,2*N+q,q),(N+k,N+q,3*N+q,3*N+k)]);mi.extend([0,0,1])
 # Tessellate nonconvex backing polygons; continuous mucosa/cortex backing is intentional.
 for start,reverse,matidx in [(2*N,True,0),(3*N,False,1)]:
  poly=[Vector(vs[start+i]) for i in range(N)];lookup={tuple(p):start+i for i,p in enumerate(poly)}
  for tri in tessellate_polygon([poly]):
   f=[start+p if isinstance(p,int) else lookup[tuple(p)] for p in tri];fs.append(tuple(reversed(f)) if reverse else tuple(f));mi.append(matidx)
 ob=mesh(id+' | authored closed-back teaching section',vs,fs,id,id+'_cutaway','cutaway','schematic teaching section; not a slice of the source segmentation',ma);ob.data.materials.append(inner_ma)
 for p,idx in zip(ob.data.polygons,mi):p.material_index=idx;p.use_smooth=False
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 bpy.context.view_layer.objects.active=ob;be=ob.modifiers.new('Rounded teaching-section rim','BEVEL');be.width=.0005;be.segments=3;be.limit_method='ANGLE';be.angle_limit=.6;bpy.ops.object.modifier_apply(modifier=be.name)
 ob['clinical_color']=list(ma.get('clinical_color',(.7,.3,.3)));return inner,back
def tube(name,pts,radius,id,aid,ma,role='detail',radii=None):
 # Explicit transported-ring sweep prevents folded short Bezier tube geometry.
 pts=[Vector(p) for p in pts];centers=[];rr=[]
 for j in range(len(pts)-1):
  count=max(2,int((pts[j+1]-pts[j]).length/.001))
  for k in range(count):
   t=k/count;centers.append(pts[j].lerp(pts[j+1],t));rr.append(radius*((radii[j]*(1-t)+radii[j+1]*t) if radii else 1))
 centers.append(pts[-1]);rr.append(radius*(radii[-1] if radii else 1));vs=[];fs=[];N=20
 for j,c in enumerate(centers):
  tangent=(centers[min(j+1,len(centers)-1)]-centers[max(0,j-1)]).normalized();ref=Vector((0,1,0))
  if abs(tangent.dot(ref))>.95:ref=Vector((1,0,0))
  a=tangent.cross(ref).normalized();b=tangent.cross(a).normalized()
  for k in range(N):angle=k/N*math.tau;vs.append(tuple(c+rr[j]*(a*math.cos(angle)+b*math.sin(angle))))
 for j in range(len(centers)-1):
  for k in range(N):q=(k+1)%N;fs.append((j*N+k,j*N+q,(j+1)*N+q,(j+1)*N+k))
 fs.append(tuple(reversed(range(N))));fs.append(tuple((len(centers)-1)*N+k for k in range(N)))
 ob=mesh(name,vs,fs,id,aid,role,'schematic',ma);bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(ob.data);bm.free();return ob
cortex=bpy.data.materials['Renal cortex'];med=bpy.data.materials['Renal medullary pyramids'];collect=bpy.data.materials['Renal collecting system']
med.node_tree.nodes['CLINICAL'].inputs['Base Color'].default_value=(.55,.13,.10,1);med['clinical_color']=[.55,.13,.10]
for id in ['kidney_left','kidney_right']:
 lo,hi,c,dim=bounds(sources[id]);side=1 if id.endswith('left') else -1;rx=dim.x*.46;rz=dim.z*.46;front=c.y-dim.y*.12
 outline=[]
 for i in range(160):
  a=i/160*math.tau;wrapped=(a-math.pi+math.pi)%math.tau-math.pi;x=rx*(math.cos(a)+.35*math.exp(-(wrapped/.58)**2));outline.append(Vector((c.x+side*x,c.z+rz*math.sin(a))))
 inner,back=closed_back_section(id,outline,c,front,.004,cortex,cortex)
 pelvis=Vector((c.x-side*rx*.29,front+.001,c.z-.004));upper=pelvis+Vector((side*.006,0,.010));lower=pelvis+Vector((side*.005,0,-.010));exit=pelvis+Vector((-side*.009,0,-.017))
 for j in range(7):
  a=math.radians(-75+j*25);base=Vector((c.x+side*rx*.59*math.cos(a),front+.001,c.z+rz*.66*math.sin(a)));tip=Vector((c.x-side*rx*.22,front+.001,c.z+.010*math.sin(a)));direction=(base-tip).normalized();perp=Vector((-direction.z,0,direction.x));r=.0037
  v=[tip,base+perp*r,base-perp*r];vs=[tuple(p) for p in v]+[tuple(p+Vector((0,.003,0))) for p in v];fs=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
  ob=mesh(id+' medullary pyramid section '+str(j+1),vs,fs,id,id+'_pyramid_'+str(j+1),'detail','schematic cross-section through a representative pyramid',med)
  for p in ob.data.polygons:p.use_smooth=False
  join=upper if j>=4 else lower if j<=2 else pelvis
  tube(id+' minor calyx '+str(j+1),[tip+Vector((-side*.001,-.001,0)),tip.lerp(join,.55)+Vector((0,-.001,0)),join],.0011,id,id+'_calyx_'+str(j+1),collect,radii=[1.55,.8,.85])
 tube(id+' upper major calyx',[upper,pelvis+Vector((side*.001,0,.004)),pelvis],.0016,id,id+'_major_calyx_upper',collect)
 tube(id+' lower major calyx',[lower,pelvis,exit],.0016,id,id+'_major_calyx_lower',collect)
 tube(id+' renal pelvis funnel',[pelvis+Vector((side*.002,0,.006)),pelvis,exit],.0023,id,id+'_pelvis',collect,radii=[1.0,1.35,.7])
 tube(id+' single ureter origin',[exit,exit+Vector((-side*.004,.002,-.014)),exit+Vector((-side*.005,.003,-.025))],.0018,id,id+'_ureter_origin',collect)
# Authored gastric teaching cup: broad fundus, lesser-curvature indentation and pyloric-side extension.
id='stomach';lo,hi,c,dim=bounds(sources[id]);rx=dim.x*.47;rz=dim.z*.46;front=c.y-dim.y*.20;outline=[]
for i in range(192):
 a=i/192*math.tau;medial=((a-math.pi+math.pi)%math.tau-math.pi);x=rx*(math.cos(a)+.32*math.exp(-(medial/.60)**2));z=rz*math.sin(a);x+=.12*rx*math.sin(a);outline.append(Vector((c.x+x,c.z+z)))
inner,back=closed_back_section(id,outline,c,front,.010,mats[id],bpy.data.materials['Gastric mucosa and rugae'])
def inside2(x,z,poly):
 hit=False;j=len(poly)-1
 for i in range(len(poly)):
  a,b=poly[i],poly[j]
  if (a.y>z)!=(b.y>z) and x<(b.x-a.x)*(z-a.y)/(b.y-a.y)+a.x:hit=not hit
  j=i
 return hit
count=0
for j in range(11):
 pts=[];x=c.x+rx*(-.62+j*.12)
 def flush():
  global pts,count
  if len(pts)>5:
   count+=1;tube('Gastric mucosal fold '+str(count),pts,.0008,id,'gastric_ruga_'+str(count),bpy.data.materials['Gastric mucosa and rugae'])
  pts=[]
 for k in range(65):
  z=c.z+rz*(-.70+k*.022);xx=x+.0015*math.sin(k*.35+j)+.0006*math.sin(k*.8)
  if inside2(xx,z,inner) and inside2(xx+.0018,z,inner) and inside2(xx-.0018,z,inner):pts.append(Vector((xx,back-.00035,z)))
  else:flush()
 flush()
for id in ['kidney_left','kidney_right','stomach']:
 specs[id]['cutawaySourceKind']='schematic';specs[id]['notes'].append('Section view substitutes an explicitly authored closed-back teaching diagram. It is not a registered slice or internal segmentation of this source organ.')
 for ob in objects[id]:
  if len(ob.data.materials) and 'clinical_color' in ob.data.materials[0]:ob['clinical_color']=ob.data.materials[0]['clinical_color']
json.dump(manifest,open(D/'manifest.json','w'),ensure_ascii=False,indent=2);json.dump({id:[o.name for o in obs] for id,obs in objects.items()},open(R/'object_map.json','w'),indent=2)
for ma in list(bpy.data.materials):
 if 'baked portable PBR' in ma.name:bpy.data.materials.remove(ma,do_unlink=True)
for im in list(bpy.data.images):
 if ' 1K' in im.name:bpy.data.images.remove(im,do_unlink=True)
ctrl['cutaway']=0;ctrl['material_mode']=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/'Anatomy_Workshop.blend'),compress=True)
for id in ['kidney_left']:
 for key,col in collections.items():col.hide_render=(key!=id)
 ctrl['cutaway']=1;ctrl['material_mode']=1;bpy.context.view_layer.update();lo,hi,c,dim=bounds(sources[id]);cam=bpy.data.objects['CAM · organ closeup'];cam.location=c+Vector((.007,-.6,.010));aim(cam,c);cam.data.ortho_scale=max(dim.x,dim.z)*1.32;s.camera=cam;s.render.resolution_x=s.render.resolution_y=1200;s.cycles.samples=96;s.render.filepath=str(D/'renders'/('07_kidney_teaching_section.png' if id=='kidney_left' else '08_stomach_teaching_section.png'));bpy.ops.render.render(write_still=True)
print('AUTHORED SECTIONS COMPLETE',flush=True)
