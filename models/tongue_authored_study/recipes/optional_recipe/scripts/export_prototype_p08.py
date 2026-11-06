import pathlib,json,struct,hashlib,numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
D=pathlib.Path(__file__).resolve().parents[1];z=np.load(D/'reviews/prototype-p07-upper-selection.npz');x=z['positions'];f=z['faces'];oi=z['originalFaceIDs'];original=z['isOriginal'];group=z['sourceFaceGroup'];loops=[z[k] for k in sorted(z.files) if k.startswith('loop')];verts=x.tolist();faces=f.tolist();provenance=np.where(original,np.where(group>=3,1,0),2).tolist();sourceFaceIDs=oi.tolist();boundaryDirected=set(map(tuple,np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]).tolist()));author_params={'bottomPlaneY0':.682,'bottomPlaneZSlope':.18,'bottomPlaneZOrigin':-.005,'radialRings':48,'interiorBoundarySmoothingSigmaM':.006,'seamFairingBandM':.003,'fairingIterations':300,'fairingStep':.2,'interiorBoundarySmoothingFullAtRadians':.45,'method':'Connected loft from geometry-derived external-dorsal silhouette to an authored tilted inferior plane; rounded section via cosine radial / sine vertical interpolation. Existing inward-return walls are removed, not overlaid. Qualitative reference-informed design, not measured anatomy.'}
center=x[loops[0]][:,[0,2]].mean(axis=0)
# Area centroid less biased by dense triangulation along one side.
p=x[loops[0]][:,[0,2]];q=np.roll(p,-1,axis=0);cross=p[:,0]*q[:,1]-q[:,0]*p[:,1];center=((p+q)*cross[:,None]).sum(0)/(3*cross.sum())
def B(z):return author_params['bottomPlaneY0']+author_params['bottomPlaneZSlope']*(z-author_params['bottomPlaneZOrigin'])
for li,loop0 in enumerate(loops):
 loop=loop0.copy()
 # New patch follows reversed existing edge orientation.
 if (int(loop[0]),int(loop[1])) in boundaryDirected:loop=loop[::-1]
 n=len(loop)
 if li==0:
  b=x[loop].copy();previous=loop.copy()
  # Smooth irregular silhouette data progressively inside the authored patch only.
  lens=np.linalg.norm(np.roll(b,-1,axis=0)-b,axis=1);t=np.r_[0,np.cumsum(lens)];spl=CubicSpline(t,np.vstack([b,b[0]]),bc_type='periodic');tt=np.linspace(0,t[-1],2048,endpoint=False);dense=spl(tt);smooth=gaussian_filter1d(dense,sigma=0.006/t[-1]*2048,axis=0,mode='wrap');smoothspl=CubicSpline(np.r_[tt,t[-1]],np.vstack([smooth,smooth[0]]),bc_type='periodic');bs=smoothspl(t[:-1])
  for k in range(1,author_params['radialRings']):
   theta=(np.pi/2)*k/author_params['radialRings'];c=np.cos(theta);s=np.sin(theta);q=min(theta/.45,1);q=q*q*(3-2*q);bc=(1-q)*b+q*bs;new=bc.copy();new[:,[0,2]]=center+(bc[:,[0,2]]-center)*c;new[:,1]=B(new[:,2])+(bc[:,1]-B(bc[:,2]))*(1-s);ids=np.arange(len(verts),len(verts)+n);verts.extend(new.tolist())
   for j in range(n):
    j2=(j+1)%n;faces.extend([[int(previous[j]),int(previous[j2]),int(ids[j2])],[int(previous[j]),int(ids[j2]),int(ids[j])]]);provenance.extend([3,3]);sourceFaceIDs.extend([-1,-1])
   previous=ids
  ci=len(verts);verts.append([center[0],B(center[1]),center[1]])
  for j in range(n):faces.append([int(previous[j]),int(previous[(j+1)%n]),ci]);provenance.append(3);sourceFaceIDs.append(-1)
 else:
  # Ear clipping in best-fit plane respects concave boundary; no center fan.
  vv=x[loop];u,sv,vt=np.linalg.svd(vv-vv.mean(0),full_matrices=False);uv=(vv-vv.mean(0))@vt[:2].T
  cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
  sign=np.sign(sum(cross(uv[j],uv[(j+1)%n]) for j in range(n)))
  remaining=list(range(n));patch=[]
  while len(remaining)>3:
   found=False
   for jj in range(len(remaining)):
    a=remaining[(jj-1)%len(remaining)];b=remaining[jj];c=remaining[(jj+1)%len(remaining)];aa,bb,cc=uv[[a,b,c]]
    if sign*cross(bb-aa,cc-bb)<=1e-16:continue
    contains=False
    for k in remaining:
     if k in (a,b,c):continue
     pt=uv[k]
     if min(sign*cross(bb-aa,pt-aa),sign*cross(cc-bb,pt-bb),sign*cross(aa-cc,pt-cc))>=-1e-16:contains=True;break
    if contains:continue
    patch.append([int(loop[a]),int(loop[b]),int(loop[c])]);remaining.pop(jj);found=True;break
   if not found:raise RuntimeError('No valid ear for small boundary loop '+str(li))
  patch.append([int(loop[k]) for k in remaining]);faces.extend(patch);provenance.extend([2]*len(patch));sourceFaceIDs.extend([-1]*len(patch))

x=np.array(verts,dtype=np.float32);f=np.array(faces,dtype=np.uint32);prov=np.array(provenance,dtype=np.uint8);sf=np.array(sourceFaceIDs,dtype=np.int32)
# Fair actual geometry across the join. Any original source triangle moved is reclassified AUTHORED.
xBefore=x.copy();edges=np.unique(np.sort(np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);ee=np.vstack([edges,edges[:,::-1]]);adj=coo_matrix((np.ones(len(ee)),(ee[:,0],ee[:,1])),shape=(len(x),len(x))).tocsr();rawdegree=np.asarray(adj.sum(1)).ravel();degree=np.maximum(rawdegree,1);dist=cKDTree(x[loops[0]]).query(x)[0];weight=np.maximum(1-dist/.003,0)**2;bodyVertices=np.unique(f[prov==3]);weight[bodyVertices]=np.maximum(weight[bodyVertices],.6);papillaVertices=np.unique(f[prov==1]);weight[papillaVertices]=0;weight[rawdegree==0]=0;xx=x.astype(np.float64)
for _ in range(300):xx+=.2*weight[:,None]*((adj@xx)/degree[:,None]-xx)
x=xx.astype(np.float32);moved=np.any(x!=xBefore,axis=1);changedSourceFaces=(prov<2)&np.any(moved[f],axis=1);prov[changedSourceFaces]=2
(D/'reviews/prototype-p08-fairing.json').write_text(json.dumps({'method':'300 iterations positive-weight uniform Laplacian, step .2, 3.0 mm source seam band with quadratic falloff; all authored body vertices weight >=.6; original papilla vertices anchored. Actual geometry smoothing, not normals-only. All source triangles with moved vertices relabeled authored.','movedVertices':int(moved.sum()),'sourceTrianglesReclassifiedAuthored':int(changedSourceFaces.sum()),'maxDisplacementM':float(np.linalg.norm(x-xBefore,axis=1).max()),'papillaVertexDisplacementMaxM':float(np.linalg.norm(x[papillaVertices]-xBefore[papillaVertices],axis=1).max())},indent=2))

# Exact float32 coordinate merge only; no tolerance weld or surface movement.
x,inv=np.unique(x,axis=0,return_inverse=True);f=inv[f].astype(np.uint32);a=x[f[:,1]].astype(np.float64)-x[f[:,0]];b=x[f[:,2]].astype(np.float64)-x[f[:,0]];fn=np.cross(a,b);area=np.linalg.norm(fn,axis=1);valid=area>1e-16;removed=int((~valid).sum());f=f[valid];prov=prov[valid];sf=sf[valid];fn=fn[valid];norm=np.zeros(x.shape,dtype=np.float64)
for j in range(3):np.add.at(norm,f[:,j],fn)
norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-20);norm=norm.astype(np.float32)
name='tongue-authored-hra-hybrid-p08';out=D/'models'/f'{name}.glb';g={'asset':{'version':'2.0','generator':'Source-aware authored illustrative tongue prototype','extras':{'status':'prototype — not accepted','provenance':'HRA mouth-female v1.0 external dorsal region + newly authored inferior body, seam transitions and small closure patches','sourceSHA256':'a76dc3c882994ff1515f30f9047872a634a6cdf9275e1eec7b4aa9ba13633d12','sourceRawSHA256':'bd8e24e9d52b49719c6a1cafa1f54fc40c1d3f811b9d32df78d5c20ebb78c197','sourceLicense':'CC BY 4.0 — Heidi Schlehlein / HRA-HuBMAP; derivative attribution required','nativeFrame':'Source numeric positions, Y-up metre coordinate convention, original origin; no registration or object transform','warning':'AUTHORED educational external-body approximation; not patient-specific, source-exact, clinically validated, or complete internal anatomy. No oral floor, frenulum, extrinsic attachments, vessels, nerves or internal muscles.'}},'scene':0,'scenes':[{'name':'Authored gross anatomy — isolated tongue illustration','nodes':[0]}],'nodes':[{'name':'AUTHORED tongue illustration — HRA-derived external dorsum','children':[]}],'meshes':[],'materials':[],'accessors':[],'bufferViews':[]};buf=bytearray()
def accessor(a,typ,comp,target):
 a=np.ascontiguousarray(a);start=len(buf);buf.extend(a.tobytes());buf.extend(b'\0'*((-len(buf))%4));v=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':a.nbytes,'target':target});ac={'bufferView':v,'componentType':comp,'count':len(a),'type':typ}
 if typ=='VEC3' and comp==5126:ac['min']=a.min(0).astype(float).tolist();ac['max']=a.max(0).astype(float).tolist()
 i=len(g['accessors']);g['accessors'].append(ac);return i
names=['HRA-derived external dorsal surface — original triangles','HRA-derived papilla surface patches — original triangles','AUTHORED seam transitions and small closure patches','AUTHORED body and ventral surface'];colors=[(.53,.20,.27,1),(.55,.22,.28,1),(.53,.20,.27,1),(.53,.20,.27,1)];counts=[]
for k,nn in enumerate(names):
 fk=f[prov==k];used=np.unique(fk);idx=np.full(len(x),-1,dtype=np.int64);idx[used]=np.arange(len(used));local=idx[fk].astype(np.uint32);pa=accessor(x[used],'VEC3',5126,34962);na=accessor(norm[used],'VEC3',5126,34962);ia=accessor(local.ravel(),'SCALAR',5125,34963);g['materials'].append({'name':nn,'pbrMetallicRoughness':{'baseColorFactor':list(colors[k]),'roughnessFactor':.66,'metallicFactor':0},'doubleSided':False});g['meshes'].append({'name':nn,'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'indices':ia,'material':k,'mode':4}],'extras':{'provenanceCategory':k,'originalTrianglePositions':k in [0,1],'normals':'Area-weighted normals recomputed over combined surface; no original-normal byte preservation claim'}});ni=len(g['nodes']);g['nodes'].append({'name':nn,'mesh':k,'extras':{'role':nn}});g['nodes'][0]['children'].append(ni);counts.append({'category':k,'name':nn,'vertices':len(used),'triangles':len(fk)})
g['buffers']=[{'byteLength':len(buf)}];j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw=struct.pack('<4sII',b'glTF',2,28+len(j)+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf;out.write_bytes(raw)
np.savez_compressed(D/'reviews/prototype-p08-face-provenance.npz',positions=x,faces=f,category=prov,sourceCombinedFaceID=sf)
np.savez_compressed(D/'reviews/prototype-p08-source-triangle-selection.npz',retainedOriginalSourceFaceIDs=np.unique(sf[(prov<2)&(sf>=0)]),authoredFromSourceFaceIDs=np.unique(sf[(prov==2)&(sf>=0)]))
e=np.sort(np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,ec=np.unique(e,axis=0,return_counts=True);report={'output':str(out.relative_to(D)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'sourceRawUnmodified':True,'frame':'native source numeric Y-up; no transform','authoringParameters':author_params,'authoringCenterXZ':center.tolist(),'categories':counts,'uniqueVertices':len(np.unique(f)),'triangles':len(f),'exactCoordinateBoundaryEdges':int((ec==1).sum()),'exactCoordinateNonTwoEdges':int((ec!=2).sum()),'removedZeroAreaFaces':removed,'selfIntersection':'not yet tested','visualGate':'pending exact-export render','referenceGate':'authored gross illustrative approximation only; pending comparison','runtimeGate':'unverified','limitations':'No floor/frenulum, internal muscles, complete extrinsic attachment, or patient/specimen-specific claims.'};(D/'reviews/prototype-p08-build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
