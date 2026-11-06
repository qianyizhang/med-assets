"""Bounded UFF Tomo1B research-display replay. Not clinical segmentation.

No network requests or raw-volume publication. Supply the pinned public ZIP.
Output is work-directory data; canonical candidate remains immutable.
"""
from pathlib import Path
import argparse, io, json, hashlib, zipfile, gc, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from skimage.measure import marching_cubes
import trimesh, pymeshlab, point_cloud_utils as pcu

ZIP_SHA256='cceeee50561a6d2f925fc8a0e38a33729246c28b267084db32f66c2c0ae29777'
ZIP_MD5='977bc12d30f0ebb725bb04f37fa090f2'
ROI_SHA256='477ceb66bb04e75e5d25944072df640352cbd13a96cf713cc52c887d3f44f049'
MASK_SHA256={'hard_tissue':'4b4fabb87af76c21ea69e25a036495da56503b56cae5f3daf1caba0705bb6c70','enclosed_space_candidate':'2c0e4e40a4fd563a5a87eab748fa611b82351d719d5ad3f6d2d02476e1862555'}
MASTER_SHA256='7b7e58a7c8149538dffdeebf9f6f079ccb47f6be1fc53db93510b80073ad9790'
DISPLAY_SHA256='46694985ff0162a4220d959528847446ffe48b3be41e481f5890429500e2d3b3'
ORIGIN=np.array([4,360,308]);STOP=np.array([1002,688,664]);SPACING_MM=.020002117


def file_hash(path,algorithm='sha256'):
 h=hashlib.new(algorithm)
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()


def save_json(path,value):
 Path(path).write_text(json.dumps(value,indent=2,default=lambda v:v.item())+'\n')


def ingest(source,work):
 if file_hash(source)!=ZIP_SHA256 or file_hash(source,'md5')!=ZIP_MD5:
  raise ValueError('Source ZIP does not match pinned public source')
 with zipfile.ZipFile(source) as z:
  prefix='ds-uct-002_root_canal_strain_tomo1b_10um_8bits/'
  files=[prefix+f'{i:04d}.tiff' for i in range(1,1019)]
  if not all(name in z.namelist() for name in files):raise ValueError('TIFF inventory mismatch')
  header=z.read(prefix+'Header.txt').decode()
  if '20.002117' not in header:raise ValueError('Source spacing header mismatch')
  a=np.empty(tuple(STOP-ORIGIN),dtype=np.uint8)
  for j,i in enumerate(range(ORIGIN[0],STOP[0])):
   im=np.asarray(Image.open(io.BytesIO(z.read(files[i]))))
   if im.shape!=(1024,1004) or im.dtype!=np.uint8:raise ValueError('Source TIFF format mismatch')
   a[j]=im[ORIGIN[1]:STOP[1],ORIGIN[2]:STOP[2]]
  if hashlib.sha256(a.tobytes()).hexdigest()!=ROI_SHA256:raise ValueError('ROI data mismatch')
  np.save(work/'native-roi.npy',a)
 save_json(work/'ingestion.json',{'zip_sha256':ZIP_SHA256,'zip_md5':ZIP_MD5,'roi_array_sha256':ROI_SHA256,'roi_origin_zyx':ORIGIN.tolist(),'roi_shape':list(a.shape),'spacing_mm':SPACING_MM,'source_frame':'column,row,slice; anatomical orientation unknown'})


def extract(work):
 a=np.load(work/'native-roi.npy',mmap_mode='r')
 if hashlib.sha256(a.tobytes()).hexdigest()!=ROI_SHA256:raise ValueError('Unverified ROI')
 lab,n=ndi.label(a>80);counts=np.bincount(lab.ravel());counts[0]=0;hard=lab==np.argmax(counts);del lab
 envelope=np.stack([ndi.binary_fill_holes(s) for s in hard]);void=envelope&~hard;del envelope
 lab,n=ndi.label(void);counts=np.bincount(lab.ravel());counts[0]=0;void=lab==np.argmax(counts);del lab
 masks={'hard_tissue':hard,'enclosed_space_candidate':void}
 for name,mask in masks.items():
  if hashlib.sha256(mask.tobytes()).hexdigest()!=MASK_SHA256[name]:raise ValueError('Mask mismatch: '+name)
 np.savez_compressed(work/'provisional-masks.npz',**masks)
 scene=trimesh.Scene()
 for name,mask in [('hard_tissue_boundary',hard),('enclosed_space_candidate',void)]:
  v,f,_,_=marching_cubes(mask.astype('uint8'),.5,spacing=(SPACING_MM,)*3,allow_degenerate=False)
  v+=ORIGIN*SPACING_MM;v=v[:,[2,1,0]]/1000
  m=trimesh.Trimesh(v,f[:,::-1],process=False)
  m.metadata={'source':'UFF ds-uct-002 Tomo1B','license':'CC-BY-4.0','component':name,'segmentation':'provisional threshold80/largest component; void uses slice hole-fill selection','fdI':None,'units':'metres','source_spacing_mm':SPACING_MM,'source_frame':'x=column,y=row,z=slice; anatomical orientation unknown','clinical_approval':False}
  if (m.area_faces==0).any():raise ValueError('Degenerate extraction')
  scene.add_geometry(m,node_name='uff_tomo1b_'+name,geom_name=name)
 # Reproduce the historical float32 export boundary before outward correction.
 intermediate=trimesh.load(io.BytesIO(scene.export(file_type='glb')),file_type='glb',force='scene',process=False)
 fixed=trimesh.Scene()
 for name,m in intermediate.geometry.items():
  if m.volume<0:m.invert()
  newname='slice_enclosed_space_proxy' if name=='enclosed_space_candidate' else name
  m.metadata['orientation_correction']='Global face reversal to positive signed volume; vertices unchanged; outward closed surface orientation, no anatomy approval'
  m.metadata['component']=newname
  m.metadata['proxy_limit']='All selected void voxels connect to exterior in 3D; slice-based proxy omits the open terminal channel; not a sealed anatomical cavity' if newname=='slice_enclosed_space_proxy' else 'Threshold-selected hard-tissue boundary; not separated enamel/dentin/cementum'
  fixed.add_geometry(m,node_name='uff_tomo1b_'+newname,geom_name=newname)
 target=work/'uff-tomo1b-master.glb';target.write_bytes(fixed.export(file_type='glb'))
 save_json(work/'extraction.json',{'master_sha256':file_hash(target),'expected_master_sha256':MASTER_SHA256,'byte_match':file_hash(target)==MASTER_SHA256,'mask_hashes':MASK_SHA256,'clinical_approval':False})
 if file_hash(target)!=MASTER_SHA256:raise ValueError('Master bytes differ from pinned reference; stop before LOD')
 print('MASTER',file_hash(target),flush=True)

def topology(m):
 f=np.asarray(m.faces);vcount=len(m.vertices)
 e=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]))
 signs=np.where(e[:,0]<e[:,1],1,-1).astype(np.int8)
 lo=e.min(axis=1);hi=e.max(axis=1);del e
 keys=lo*vcount+hi;order=np.argsort(keys);sortedkeys=keys[order]
 unique,starts,counts=np.unique(sortedkeys,return_index=True,return_counts=True)
 sums=np.add.reduceat(signs[order].astype(np.int32),starts)
 boundarykeys=unique[counts==1];boundary=np.column_stack((boundarykeys//vcount,boundarykeys%vcount))
 if len(boundary):
  ids,inv=np.unique(boundary,return_inverse=True)
  bcc=len(trimesh.graph.connected_components(inv.reshape(-1,2),nodes=np.arange(len(ids)),min_len=1))
 else:bcc=0
 return {'euler':int(len(np.unique(f))-len(unique)+len(f)),'boundary_components':bcc,'nonmanifold_edges':int((counts>2).sum()),'watertight':bool(np.all(counts==2)),'winding':bool(np.all(sums[counts==2]==0))}

def split_compact(m):
 f=np.asarray(m.faces);n=len(f);vcount=len(m.vertices)
 e=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]))
 keys=e.min(axis=1)*vcount+e.max(axis=1);del e
 order=np.argsort(keys);sortedkeys=keys[order];starts=np.r_[0,np.flatnonzero(np.diff(sortedkeys))+1];counts=np.diff(np.r_[starts,len(order)])
 both=starts[counts==2];a=order[both]%n;b=order[both+1]%n
 for start,count in zip(starts[counts>2],counts[counts>2]):
  fs=order[start:start+count]%n;a=np.r_[a,np.repeat(fs[0],len(fs)-1)];b=np.r_[b,fs[1:]]
 graph=coo_matrix((np.ones(len(a),dtype=np.int8),(a,b)),shape=(n,n)).tocsr()
 num,labels=connected_components(graph,directed=False)
 del graph,keys,order,sortedkeys,starts,counts,a,b
 groups=np.argsort(labels,kind='stable');cuts=np.r_[0,np.flatnonzero(np.diff(labels[groups]))+1,n];out=[]
 for lo,hi in zip(cuts[:-1],cuts[1:]):
  ff=f[groups[lo:hi]];ids,inv=np.unique(ff,return_inverse=True)
  out.append(trimesh.Trimesh(np.asarray(m.vertices)[ids],inv.reshape(-1,3),process=False))
 return out

def covering_points(m,radius=.04):
 """Centroids of virtual subdivisions, every triangle point within radius (mm)."""
 result=[];maxradius=0.
 for start in range(0,len(m.faces),100000):
  tris=np.asarray(m.vertices)[np.asarray(m.faces)[start:start+100000]]
  while len(tris):
   cen=tris.mean(axis=1);rad=np.linalg.norm(tris-cen[:,None,:],axis=2).max(axis=1);ok=rad<=radius
   if ok.any():result.append(cen[ok]);maxradius=max(maxradius,float(rad[ok].max()))
   bad=tris[~ok]
   if not len(bad):break
   a,b,c=bad[:,0],bad[:,1],bad[:,2];ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
   tris=np.concatenate([np.stack([a,ab,ca],axis=1),np.stack([ab,b,bc],axis=1),np.stack([ca,bc,c],axis=1),np.stack([ab,bc,ca],axis=1)])
 return np.concatenate(result),maxradius

def deviation(a,b,radius):
 pts,cover=covering_points(a,radius);ds=[]
 for start in range(0,len(pts),1000000):
  q=pts[start:start+1000000]
  print("QUERY",start,len(pts),len(b.faces),flush=True)
  # PCU singleton shape is independently known unsafe; use brute-force fallback.
  if len(q)==1:
   _,d,_=trimesh.proximity.closest_point_naive(b,q)
  else:d,_,_=pcu.closest_points_on_mesh(q.astype('float64'),b.vertices.astype('float64'),b.faces.astype('int32'))
  ds.append(np.asarray(d).reshape(-1))
 d=np.concatenate(ds)
 return {'samples':len(d),'sampled_max_mm':float(d.max()),'sampled_p95_mm':float(np.quantile(d,.95)),'covering_radius_mm':cover,'continuous_upper_bound_mm':float(d.max()+cover)}

def build_lod(work):
 source=work/'uff-tomo1b-master.glb';master=trimesh.load(source,force='scene',process=False);scene=trimesh.Scene();rows=[]
 for name,original in master.geometry.items():
  src=original.copy();src.vertices*=1000;islands=split_compact(src);selected=[];ir=[]
  for index,island in enumerate(islands):
   sig=topology(island);chosen=island;attempts=[]
   if len(island.faces)>1000:
    for ratio in [.5,.75]:
     ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(island.vertices,island.faces));ms.apply_filter('meshing_decimation_quadric_edge_collapse',targetfacenum=int(len(island.faces)*ratio),preservetopology=True,preserveboundary=True,preservenormal=True,optimalplacement=False,autoclean=False)
     v=(ms.current_mesh().vertex_matrix()/1000).astype('float32').astype('float64')*1000;f=ms.current_mesh().face_matrix();candidate=trimesh.Trimesh(v,f,process=False);candidate.remove_unreferenced_vertices();del ms
     zero=int((candidate.area_faces==0).sum());bounds=float(np.abs(candidate.bounds-island.bounds).max());same=topology(candidate)==sig
     # Retain source orientation, including internal boundary signs; do not invert islands independently.
     sign_ok=np.sign(candidate.volume)==np.sign(island.volume)
     ok=zero==0 and bounds<=.0100011 and same and sign_ok and np.isfinite(v).all()
     attempts.append({'ratio':ratio,'zero_area':zero,'bounds_error_mm':bounds,'topology_same':same,'signed_volume_sign_preserved':bool(sign_ok),'accepted':bool(ok)})
     if ok:chosen=candidate;break
   selected.append(chosen);ir.append({'island':index,'before_faces':len(island.faces),'after_faces':len(chosen.faces),'attempts':attempts})
  lod=trimesh.util.concatenate(selected)
  radius=.005 if 'proxy' in name else .010
  print('MEASURING',name,len(src.faces),len(lod.faces),len(islands),flush=True)
  
  a=deviation(src,lod,radius);b=deviation(lod,src,radius)
  row={'component':name,'before_faces':len(src.faces),'after_faces':len(lod.faces),'islands_preserved':len(islands),'per_island':ir,'forward':a,'reverse':b,'conservative_bound_with_export_allowance_mm':max(a['continuous_upper_bound_mm'],b['continuous_upper_bound_mm'])+.00001,'source_voxel_mm':.020002117,'bounds_error_mm':float(np.abs(src.bounds-lod.bounds).max()),'global_topology_preserved':topology(src)==topology(lod),'source_signed_volume_mm3':float(src.volume),'lod_signed_volume_mm3':float(lod.volume)}
  lod.vertices/=1000;lod.metadata=original.metadata.copy();lod.metadata['display_lod']='Per-island source-endpoint QEM; no island deletion; no biological anatomy claim';scene.add_geometry(lod,node_name='uff_tomo1b_'+name,geom_name=name);rows.append(row)
  gc.collect()
  print(row['conservative_bound_with_export_allowance_mm'],flush=True)
 b=scene.export(file_type='glb');f=work/'uff-tomo1b-display.glb';f.write_bytes(b)
 report={'master_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'display_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'components':rows,'status':'Local display candidate pending independent review; proxy endpoint remains algorithmic, not anatomy'}
 (work/'lod-report.json').write_text(json.dumps(report,indent=2));print('DONE',len(b),report['display_sha256'],flush=True)

def verify(model,work):
 if file_hash(model)!=DISPLAY_SHA256:raise ValueError('Display bytes differ from pinned candidate')
 s=trimesh.load(model,force='scene',process=False)
 expected={'hard_tissue_boundary','slice_enclosed_space_proxy'}
 if set(s.geometry)!=expected:raise ValueError('Unexpected named geometry')
 rows=[]
 for name,m in s.geometry.items():
  if not np.isfinite(m.vertices).all() or (m.area_faces==0).any() or m.volume<=0 or not m.is_winding_consistent:raise ValueError('Export geometry check failed')
  rows.append({'name':name,'faces':len(m.faces),'bounds_m':m.bounds.tolist(),'volume_m3':float(m.volume),'topology':topology(m)})
 save_json(work/'verification.json',{'model_sha256':file_hash(model),'expected_display_sha256':DISPLAY_SHA256,'exact_display_bytes':file_hash(model)==DISPLAY_SHA256,'components':rows,'anatomical_approval':False})


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('stage',choices=['all','verify'])
 ap.add_argument('--source-zip',type=Path)
 ap.add_argument('--work-dir',type=Path,required=True)
 ap.add_argument('--model',type=Path)
 args=ap.parse_args();work=args.work_dir.resolve()
 if work.exists():ap.error('--work-dir must be new; existing outputs are never overwritten')
 # Validate supplied input before creating any output directory.
 if args.stage=='all':
  if args.source_zip is None:ap.error('--source-zip is required')
  if args.model is not None:ap.error('--model applies only to verify')
  if file_hash(args.source_zip)!=ZIP_SHA256 or file_hash(args.source_zip,'md5')!=ZIP_MD5:
   raise ValueError('Source ZIP does not match pinned source; no outputs created')
 else:
  if args.model is None:ap.error('--model is required for verify')
  if file_hash(args.model)!=DISPLAY_SHA256:
   raise ValueError('Model does not match pinned candidate; no outputs created')
 work.mkdir(parents=True,exist_ok=False)
 if args.stage=='all':
  ingest(args.source_zip,work);extract(work);build_lod(work)
  verify(work/'uff-tomo1b-display.glb',work)
 else:verify(args.model,work)


if __name__=='__main__':main()
