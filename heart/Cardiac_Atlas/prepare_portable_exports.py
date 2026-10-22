import os,json,struct,math,hashlib
import numpy as np
R=os.path.dirname(os.path.abspath(__file__))
# Explicit glTF metre conversion is required: Blender 4.3 exporter retains BU.
for name in ('Cardiac_Atlas_Clinical_Full_ED.glb','Cardiac_Atlas_Clinical_Cutaway_ED.glb','Cardiac_Walls_Baked_PBR_ED.glb'):
 path=R+'/exports/'+name;raw=open(path,'rb').read();offset=12;chunks=[]
 while offset<len(raw):
  ln,typ=struct.unpack_from('<II',raw,offset);chunks.append((typ,raw[offset+8:offset+8+ln]));offset+=8+ln
 d=json.loads(chunks[0][1]);d.setdefault('asset',{})['extras']={'units':'metres at scene world level','reference_phase':'frame 1 end-diastole','RAS_mm_from_GLTF_world':[[-1000,0,0,0],[0,0,1000,0],[0,1000,0,0],[0,0,0,1]],'clinical_status':'procedural educational idealization; not clinically validated','native_BU_mm':25}
 for scene in d['scenes']:
  if len(scene['nodes'])==1 and d['nodes'][scene['nodes'][0]].get('name')=='UNITS • 25 mm per native BU':continue
  idx=len(d['nodes']);d['nodes'].append({'name':'UNITS • 25 mm per native BU','scale':[.025,.025,.025],'children':scene['nodes']});scene['nodes']=[idx]
 js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);chunks[0]=(0x4e4f534a,js)
 body=b''.join(struct.pack('<II',len(data),typ)+data for typ,data in chunks);out=struct.pack('<III',0x46546c67,2,12+len(body))+body;open(path,'wb').write(out)
# Individual closed reference meshes in standard binary STL, RAS millimetres.
folder=R+'/exports/STL_RAS_mm';os.makedirs(folder,exist_ok=True)
d=json.load(open(R+'/exports/anatomy_meshes.json'))
for m in d['meshes']:
 v=np.array(m['vertices_BU'],dtype=np.float64)*np.array([-25,-25,25]);faces=np.array(m['triangles']);tri=v[faces];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);den=np.linalg.norm(norm,axis=1);norm/=np.where(den>0,den,1)[:,None]
 p=folder+'/'+m['anatomy_id']+'.stl'
 with open(p,'wb') as f:
  header=('Cardiac Atlas | RAS millimetres | ED frame 1 | '+m['anatomy_id']).encode()[:80];f.write(header.ljust(80,b' '));f.write(struct.pack('<I',len(faces)))
  for n,t in zip(norm,tri):f.write(struct.pack('<12fH',*(list(n)+t.ravel().tolist()),0))
manifest={'GLB':{'units':'metres at scene world level','axes':'+X patient left,+Y superior,+Z anterior','RAS_mm_from_GLTF_world':[[-1000,0,0,0],[0,0,1000,0],[0,1000,0,0],[0,0,0,1]],'materials':'simplified standard clinical PBR colors','animation':'static frame1 ED; use .blend for full animation and 3 procedural material sets'},'STL':{'units':'millimetres','axes':'RAS: +X right,+Y anterior,+Z superior','phase':'ED frame1','files':'STL_RAS_mm/*.stl','warning':'STL has no standardized units metadata; set mm on import. Separate overlapping anatomical regions use label priority described in geometry_spec.json.'},'JSON':{'units':'25mm perBU','axes':'Blender native +Xleft,+Yposterior,+Zsuperior'},'sha256':{}}
for name in ('Cardiac_Atlas_Clinical_Full_ED.glb','Cardiac_Atlas_Clinical_Cutaway_ED.glb','anatomy_meshes.json','anatomy_details.json'):
 manifest['sha256'][name]=hashlib.sha256(open(R+'/exports/'+name,'rb').read()).hexdigest()
json.dump(manifest,open(R+'/exports/EXPORT_CONTRACT.json','w'),indent=2)
print('Portable exports prepared')
