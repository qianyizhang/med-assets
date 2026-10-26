from pathlib import Path
import struct,json,numpy as np,hashlib
import argparse
P=Path(__file__).resolve().parent
exec((P/'check_export.py').read_text().split('from scipy.spatial')[0])
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();S=Path(args.source);C=Path(args.candidate);O=Path(args.output)
assert hashlib.sha256(S.read_bytes()).hexdigest()=='8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4'
assert hashlib.sha256(C.read_bytes()).hexdigest()=='c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587'
assert not O.exists();base,f,_=read(S);cand,g,_=read(C)
def world(v):return v[:,[0,2,1]]*np.array([1,-1,1])
base=world(base);cand=world(cand);center=np.array([0,.007,.080]);axis=center-np.array([.001,.007,.111]);axis/=np.linalg.norm(axis);u=np.cross(axis,[0,1,0]);u/=np.linalg.norm(u);w=np.cross(axis,u)
def section(v,faces,t):
 tri=v[faces];d=(tri-center)@axis-t;mask=(d.min(axis=1)<0)&(d.max(axis=1)>0);tri=tri[mask];d=d[mask];area=0.;degrees={};segments=0
 for q,z in zip(tri,d):
  pts=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if z[i]*z[j]<0:pts.append(q[i]+(q[j]-q[i])*(-z[i])/(z[j]-z[i]))
  if len(pts)!=2:continue
  a,b=pts;mid=(a+b)/2;radial=mid-center-axis*np.dot(mid-center,axis)
  if np.linalg.norm(radial)>.012:continue
  normal=np.cross(q[1]-q[0],q[2]-q[0]);direction=np.cross(axis,normal)
  if np.dot(b-a,direction)<0:a,b=b,a
  aa=a-center;bb=b-center;area+=(np.dot(aa,u)*np.dot(bb,w)-np.dot(aa,w)*np.dot(bb,u))/2;segments+=1
  for p in (a,b):key=tuple(np.round(p/1e-7).astype(int));degrees[key]=degrees.get(key,0)+1
 return {'area_mm2':abs(area)*1e6,'segments':segments,'non_degree2_endpoints':sum(v!=2 for v in degrees.values()),'closed_section_gate':all(v==2 for v in degrees.values())}
rows=[]
for t in [-.008,-.006,-.004,-.003,-.002,-.001,0,.001,.002,.003,.004]:
 a=section(base,f,t);b=section(cand,g,t);rows.append({'axial_mm':t*1000,'r09':a,'candidate':b,'relative_area_change':b['area_mm2']/a['area_mm2']-1 if a['area_mm2'] else None})
O.write_text(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'axis':axis.tolist(),'center':center.tolist(),'scope':'Planes normal to original parent endpoint tangent; surface sections within12mm radial aperture. Degree2 test at0.1micron coordinate rounding; open cuts excluded from reliable area claim. Closed solid-surface area, NOT lumen/caliber/clinical patency.','rows':rows},indent=2));print(rows)
