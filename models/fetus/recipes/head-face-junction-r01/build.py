"""Bounded authored-ellipsoid head/face union; append-only GLB preserves other payloads."""
import json,struct,math,hashlib,pathlib,argparse
D=pathlib.Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();source=args.source;output=args.output
if output.exists() or output.with_suffix('.build.json').exists():raise FileExistsError('Refusing to overwrite retained candidate or receipt: '+str(output))
b=source.read_bytes()
if hashlib.sha256(b).hexdigest()!='84d3f9559dac7bf175514194554d8ca5929f1d9d2666fae1bbc6b09512b4fca8':raise ValueError('Exact original fetal source SHA256 required')
L=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+L]);off=20+L;raw=bytearray(b[off+8:off+8+struct.unpack_from('<I',b,off)[0]])
c0=j['nodes'][0]['translation'];c1=j['nodes'][1]['translation'];d=[c1[i]-c0[i] for i in range(3)];a=(.034,.036,.029);f=(.021,.026,.015);K=.004
# Radial smooth union around the source ellipsoid intersection only.
def radius(u):
 r=1/math.sqrt(sum((u[i]/a[i])**2 for i in range(3)))
 A=sum((u[i]/f[i])**2 for i in range(3));B=-2*sum(u[i]*d[i]/f[i]**2 for i in range(3));C=sum((d[i]/f[i])**2 for i in range(3))-1;disc=B*B-4*A*C
 if disc<=0:return r
 q=(-B+math.sqrt(disc))/(2*A)
 if q<=0:return r
 h=max(K-abs(r-q),0)/K
 return max(r,q)+h*h*K/4
N=80;M=56;verts=[]
for t in range(M+1):
 theta=math.pi*t/M
 for k in range(N):
  phi=math.tau*k/N;u=(math.sin(theta)*math.cos(phi),math.cos(theta),math.sin(theta)*math.sin(phi));r=radius(u);verts.append(tuple(v*r for v in u))
faces=[]
for t in range(M):
 for k in range(N):
  x=t*N+k;y=t*N+(k+1)%N;z=(t+1)*N+k;w=(t+1)*N+(k+1)%N
  if t>0:faces.append((x,z,y))
  if t<M-1:faces.append((y,z,w))
# Ensure outward winding, then area-weighted smooth normals.
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
norm=[[0.,0.,0.] for _ in verts]
for fi,face in enumerate(faces):
 p,q,r=[verts[x] for x in face];n=cross([q[i]-p[i] for i in range(3)],[r[i]-p[i] for i in range(3)])
 if sum(n[i]*p[i] for i in range(3))<0:face=(face[0],face[2],face[1]);faces[fi]=face;n=tuple(-x for x in n)
 for v in face:
  for i in range(3):norm[v][i]+=n[i]
for i,n in enumerate(norm):
 if sum(x*x for x in n)<1e-30:n[:]=[0.,1. if verts[i][1]>0 else -1.,0.]
 s=math.sqrt(sum(x*x for x in n));norm[i]=[x/s for x in n]
def access(data,fmt,typ,component,target,bounds=False):
 while len(raw)%4:raw.append(0)
 start=len(raw);flat=[x for row in data for x in row];raw.extend(struct.pack('<'+fmt*len(flat),*flat));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw)-start,'target':target});ac={'bufferView':vi,'componentType':component,'count':len(data),'type':typ}
 if bounds:ac.update(min=[min(x[i] for x in data) for i in range(3)],max=[max(x[i] for x in data) for i in range(3)])
 ai=len(j['accessors']);j['accessors'].append(ac);return ai
pa=access(verts,'f','VEC3',5126,34962,True);na=access(norm,'f','VEC3',5126,34962);ia=access([(x,) for row in faces for x in row],'H','SCALAR',5123,34963)
j['meshes'].append({'name':'Head-face junction blend v1','primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'indices':ia,'material':0}]});j['nodes'][0]['mesh']=len(j['meshes'])-1;j['nodes'][1].pop('mesh');j['buffers'][0]['byteLength']=len(raw)
s=json.dumps(j,separators=(',',':')).encode();s+=b' '*((-len(s))%4);raw+=b'\0'*((-len(raw))%4);out=struct.pack('<III',0x46546c67,2,12+8+len(s)+8+len(raw))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(raw),0x004e4942)+raw
output.write_bytes(out)
output.with_suffix('.build.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(b).hexdigest(),'candidateSha256':hashlib.sha256(out).hexdigest(),'sourceBytes':len(b),'candidateBytes':len(out),'headVertices':len(verts),'headTriangles':len(faces),'blendWidth_m':K,'maximumSmoothUnionRadialAddition_m':K/4,'method':'Source ellipsoid radial smooth union; unchanged source transforms; appended mesh buffers; old inaccessible head/face payload retained for exact other-buffer preservation','anatomicalClaim':False},indent=2))
print(output.with_suffix('.build.json').read_text())
