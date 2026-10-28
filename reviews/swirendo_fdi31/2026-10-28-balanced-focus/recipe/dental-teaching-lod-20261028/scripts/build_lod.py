"""Teaching-scale QEM derivatives; no clinical validation or source changes.
Works in millimetres internally, exports original metre specimen frame.
Small islands are kept intact; the main component is simplified without an
exact shared-interface collar. No components are discarded or merged.
"""
import sys,time,json,gzip,argparse,gc
from pathlib import Path
import numpy as np,trimesh,pymeshlab
P=Path(__file__).resolve().parents[1];R=P.parent/'dental-interface-repair-20261027/replay';sys.path.insert(0,str(R));from glb_materials import explicit_materials
ap=argparse.ArgumentParser();ap.add_argument('--preset',choices=['clear','balanced','light','trial'],required=True);ap.add_argument('--layers',nargs='+',default=['enamel','dentin','pulp','bone']);args=ap.parse_args()
targets={'clear':{'enamel':25000,'dentin':50000,'pulp':8000,'bone':100000},'balanced':{'enamel':14000,'dentin':25000,'pulp':5000,'bone':40000},'light':{'enamel':8000,'dentin':15000,'pulp':3000,'bone':20000},'trial':{'enamel':14000,'dentin':25000,'pulp':5000,'bone':40000}}
O=P/('trial' if args.preset=='trial' else 'drafts/'+args.preset);O.mkdir(exist_ok=True,parents=True)
colors={'enamel':[236,231,209,255],'dentin':[210,168,105,255],'pulp':[178,54,65,255],'bone':[155,139,121,255]}
scene=trimesh.Scene();records=[];start=time.perf_counter()
for layer in args.layers:
 t=time.perf_counter();src=trimesh.load(R/f'derived/A_1_31_T2_SEG_na__{layer}.ply',process=False)
 components=trimesh.graph.connected_components(src.face_adjacency,nodes=np.arange(len(src.faces)),min_len=1)
 largest=max(components,key=len);sel=np.zeros(len(src.faces));sel[largest]=1;target=targets[args.preset][layer]
 before_components=len(components);before_watertight=bool(src.is_watertight);del components;src._cache.clear();gc.collect()
 print('START',args.preset,layer,'main',len(largest),'target',target,'preserve small faces',int((sel==0).sum()),flush=True)
 ms=pymeshlab.MeshSet();ms.add_mesh(pymeshlab.Mesh(vertex_matrix=src.vertices*1000,face_matrix=src.faces,f_scalar_array=sel))
 ms.apply_filter('compute_selection_by_condition_per_face',condselect='fq > 0.5')
 ms.apply_filter('meshing_decimation_quadric_edge_collapse',targetfacenum=target,selected=True,preservetopology=True,preserveboundary=True,preservenormal=True,optimalplacement=True,planarquadric=True,planarweight=0.001,qualitythr=0.3,autoclean=False)
 mesh=trimesh.Trimesh(vertices=(ms.current_mesh().vertex_matrix()/1000).astype(np.float32),faces=ms.current_mesh().face_matrix(),process=False);mesh.remove_unreferenced_vertices();del ms;gc.collect()
 mesh.visual.vertex_colors=colors[layer];mesh.metadata={'source':'SWIRendo A_1_31_T2_SEG_na','layer':layer,'role':'educational low-poly draft; not clinical validation','units':'metres','coordinate_frame':'source specimen LPS','method':'QEM main component; small islands unchanged; no rigid interface collar'}
 mesh.export(O/f'{layer}.ply');scene.add_geometry(mesh,node_name=f'SWIRendo_31_T2/{layer}',geom_name=f'SWIRendo_31_T2/{layer}')
 # Scoped sanity only, not source-distance audit.
 re=trimesh.load(O/f'{layer}.ply',process=False)
 rec={'layer':layer,'source_triangles':len(src.faces),'target_main_triangles':target,'triangles':len(mesh.faces),'vertices':len(mesh.vertices),'small_component_triangles_retained':int((sel==0).sum()),'components_before':before_components,'components_after':len(trimesh.graph.connected_components(re.face_adjacency,nodes=np.arange(len(re.faces)),min_len=1)),'bounds_mm':(mesh.bounds*1000).tolist(),'finite':bool(np.isfinite(mesh.vertices).all()),'zero_area_faces':int((mesh.area_faces<=0).sum()),'watertight_before':before_watertight,'watertight_after':bool(re.is_watertight),'winding_consistent':bool(re.is_winding_consistent),'seconds':time.perf_counter()-t}
 records.append(rec);(O/'build.json').write_text(json.dumps(records,indent=2));print('DONE',rec,flush=True);mesh._cache.clear();del src,re,largest,sel;gc.collect()
blob=explicit_materials(scene.export(file_type='glb'));path=O/f'FDI31-{args.preset}.glb';path.write_bytes(blob);z=gzip.compress(blob,compresslevel=9,mtime=0);path.with_suffix('.glb.gz').write_bytes(z)
re=trimesh.load(path,process=False);receipt={'preset':args.preset,'path':str(path),'triangles':sum(r['triangles'] for r in records),'bytes':len(blob),'gzip_bytes':len(z),'seconds':time.perf_counter()-start,'reimport_layers':list(re.geometry),'reimport_triangles':sum(len(x.faces) for x in re.geometry.values()),'source_untouched':True,'status':'separate draft pending teaching-scale visual decision','tolerance_context':'No 0.05mm pass/fail gate. Whole specimen ~24mm long, 1%=~0.24mm; thin pulp protected via higher density and visual review.'}
(O/'receipt.json').write_text(json.dumps(receipt,indent=2));print('RESULT',receipt,flush=True)
