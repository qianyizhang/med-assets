"""Author educational respiratory GLB targets while preserving source geometry/materials.
Coordinates: GLTF metres, +Y superior, +Z anterior. Not patient motion data.
"""
import json,struct,math,pathlib
import numpy as np
ROOT=pathlib.Path('/workspace/scratch/57dbce61b79b/anatomy-site/dist/body/3d/assets')
OUT=ROOT/'motion';OUT.mkdir(exist_ok=True)
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);pos=20+n; n2=struct.unpack_from('<I',b,pos)[0];return d,bytearray(b[pos+8:pos+8+n2])
def write(p,d,b):
 while len(b)%4:b+=b'\0'
 d['buffers']=[{'byteLength':len(b)}];s=json.dumps(d,separators=(',',':')).encode();s+=b' ' *((-len(s))%4)
 p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b)
def acc(d,b,data,typ):
 a=np.asarray(data,dtype='<f4'); a=a.reshape(-1,{'SCALAR':1,'VEC3':3}[typ]);
 while len(b)%4:b+=b'\0'
 v=len(d.setdefault('bufferViews',[]));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':a.nbytes});b+=a.tobytes();i=len(d.setdefault('accessors',[]));d['accessors'].append({'bufferView':v,'componentType':5126,'count':len(a),'type':typ,'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()});return i
def positions(d,b,i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];o=v.get('byteOffset',0)+a.get('byteOffset',0);return np.ndarray((a['count'],3),'<f4',buffer=b,offset=o,strides=(v.get('byteStride',12),4)).copy()
def motion(d,b,id):
 times=np.linspace(0,4,81);phase=times/4
 # Inspiration 40%, expiration 60%, smooth endpoints, 15 illustrative breaths/min.
 w=np.where(phase<=.4,(1-np.cos(np.pi*phase/.4))/2,(1+np.cos(np.pi*(phase-.4)/.6))/2)
 ti=acc(d,b,times,'SCALAR');ani={'name':'Illustrative breathing · 4 seconds','samplers':[],'channels':[]}
 def channel(node,path,values,typ):
  si=len(ani['samplers']);ani['samplers'].append({'input':ti,'output':acc(d,b,values,typ),'interpolation':'LINEAR'});ani['channels'].append({'sampler':si,'target':{'node':node,'path':path}})
 for ni,node in enumerate(d['nodes']):
  if 'mesh' not in node:continue
  if id.startswith('lung') or id=='diaphragm':
   mesh=d['meshes'][node['mesh']]
   for p in mesh['primitives']:
    xyz=positions(d,b,p['attributes']['POSITION']);delta=np.zeros_like(xyz)
    if id.startswith('lung'):
     # Same field across lobes, zero at superior apex; no global object scale.
     q=np.clip((.19-xyz[:,1])/.27,0,1); q=q*q*(3-2*q)
     delta[:,1]=-.018*q;delta[:,0]=xyz[:,0]*.075*q;delta[:,2]=(xyz[:,2]+.025)*.09*q
    else:
     r=np.clip((xyz[:,0]/.155)**2+((xyz[:,2]+.012)/.087)**2,0,1)
     delta[:,1]=-.018*(1-r)**.55-.003
    p['targets']=[{'POSITION':acc(d,b,delta,'VEC3')}]
   mesh['weights']=[0];mesh.setdefault('extras',{})['targetNames']=['Inspiration'];channel(ni,'weights',w,'SCALAR')
  else:
   amplitude={'liver':.008,'stomach':.006,'spleen':.006,'kidney_left':.004,'kidney_right':.004,'pancreas':.003,'gallbladder':.008,'heart':.002}.get(id,0)
   if amplitude:channel(ni,'translation',np.array(node.get('translation',[0,0,0]))+np.column_stack([w*0,-amplitude*w,w*0]),'VEC3')
 if ani['channels']:d['animations']=[ani]
 d.setdefault('extras',{})['motion_note']='Authored educational respiratory deformation; not measured motion, CFD, or validated physiology.'
 return len(ani['channels'])
ids=['lung_left','lung_right','liver','stomach','spleen','kidney_left','kidney_right','pancreas','gallbladder','heart']
report={}
for id in ids:
 d,b=read(ROOT/'meshes'/f'{id}.glb');report[id]=motion(d,b,id);write(OUT/f'{id}_breathing.glb',d,b)
# Authored elliptical double dome, right dome slightly higher. Open surface, explicitly schematic.
v=[];f=[];n=64;rings=18
for j in range(rings+1):
 r=j/rings
 for i in range(n):
  a=2*math.pi*i/n;x=.155*r*math.cos(a);z=-.012+.087*r*math.sin(a);y=-.075+.043*(1-r*r)+.006*max(0,-x/.155)*(1-r*r)
  v.append([x,y,z])
for j in range(rings):
 for i in range(n):
  a=j*n+i;c=j*n+(i+1)%n;b1=(j+1)*n+i;dd=(j+1)*n+(i+1)%n;f += [a,b1,c,c,b1,dd]
d={'asset':{'version':'2.0','generator':'Educational breathing authoring script'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'Authored schematic diaphragm','mesh':0,'extras':{'view_role':'surface','educational_only':True}}],'meshes':[{'primitives':[]}],'materials':[{'name':'Schematic diaphragm','pbrMetallicRoughness':{'baseColorFactor':[.63,.38,.28,.65],'roughnessFactor':.7},'alphaMode':'BLEND','doubleSided':True}]};b=bytearray();pi=acc(d,b,v,'VEC3');arr=np.array(f,dtype='<u4');vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':arr.nbytes});b+=arr.tobytes();ii=len(d['accessors']);d['accessors'].append({'bufferView':vi,'componentType':5125,'count':len(f),'type':'SCALAR'});norm=np.zeros((len(v),3),dtype=np.float32)
for ia,ib,ic in np.array(f).reshape(-1,3):
 nv=np.cross(np.array(v[ib])-v[ia],np.array(v[ic])-v[ia]);norm[ia]+=nv;norm[ib]+=nv;norm[ic]+=nv
lens=np.linalg.norm(norm,axis=1);norm[lens>0]/=lens[lens>0,None];norm[lens==0]=[0,1,0]
ni=acc(d,b,norm,'VEC3');d['meshes'][0]['primitives']=[{'attributes':{'POSITION':pi,'NORMAL':ni},'indices':ii,'material':0}];report['diaphragm']=motion(d,b,'diaphragm');write(OUT/'diaphragm_breathing.glb',d,b)
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(report)
