import json,struct,os,glob,hashlib
import numpy as np
R=os.path.dirname(os.path.abspath(__file__))
report={}
for path in glob.glob(R+'/*.glb'):
 raw=open(path,'rb').read();size,typ=struct.unpack_from('<II',raw,12);d=json.loads(raw[20:20+size]);off=20+size;ln,typ=struct.unpack_from('<II',raw,off);binary=raw[off+8:off+8+ln]
 # Standard glTF scene-root scale in metres, preserving all animated data.
 if not d.get('asset',{}).get('extras',{}).get('native_BU_mm'):
  for scene in d['scenes']:
   idx=len(d['nodes']);d['nodes'].append({'name':'UNITS | 25 mm per native BU','scale':[.025]*3,'children':scene['nodes']});scene['nodes']=[idx]
  d['asset']['extras']={'native_BU_mm':25,'world_units':'metres','clinical_status':'Educational idealization; not biomechanical or clinical simulation','cycle_seconds':.8,'reference_phase':'End diastole at t=0, atrial contraction begins','axes':'+X patient left,+Y superior,+Z anterior'}
  for anim in d.get('animations',[]):anim['name']='CardiacCycle_75BPM'
  js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);body=struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary;open(path,'wb').write(struct.pack('<III',0x46546c67,2,len(body)+12)+body)
 def accessor(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.frombuffer(binary,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 animations=d.get('animations',[]);assert len(animations)==1
 anim=animations[0];times=[accessor(x['input']) for x in anim['samplers']];assert abs(max(x.max() for x in times)-.8)<1e-5
 moving=[];max_loop_error=0
 for ch in anim['channels']:
  sampler=anim['samplers'][ch['sampler']];a=accessor(sampler['output']);node=d['nodes'][ch['target']['node']];assert ch['target']['path']=='weights'
  delta=float(np.ptp(a));assert delta>.01
  max_loop_error=max(max_loop_error,float(abs(a[0]-a[-1]).max()));moving.append({'name':node['name'],'weight_range':[float(a.min()),float(a.max())]})
 assert max_loop_error<1e-5
 assert any('leaflet' in x['name'] for x in moving)
 assert any('LV' in x['name'] and ('wall' in x['name'] or 'anterior section' in x['name']) for x in moving)
 assert any('LA' in x['name'] and ('wall' in x['name'] or 'anterior section' in x['name']) for x in moving)
 mesh_by_node=[];bounds=[];morph_displacements=[]
 for n in d['nodes']:
  if 'mesh' not in n:continue
  m=d['meshes'][n['mesh']]
  for p in m['primitives']:
   a=accessor(p['attributes']['POSITION']);bounds.append(a)
   for t in p.get('targets',[]):
    delta=accessor(t['POSITION']);morph_displacements.append(float(np.linalg.norm(delta,axis=1).max())*.025)
 allv=np.concatenate(bounds)*.025
 report[os.path.basename(path)]={'bytes':os.path.getsize(path),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'clips':len(animations),'clip_name':anim['name'],'duration_s':.8,'animated_nodes':len(moving),'mesh_nodes':sum('mesh' in n for n in d['nodes']),'loop_weight_error':max_loop_error,'max_vertex_morph_displacement_m':max(morph_displacements),'untransformed_mesh_bounds_m':[allv.min(0).tolist(),allv.max(0).tolist()],'images_embedded':len(d.get('images',[])),'external_uris':[x['uri'] for k in ['buffers','images'] for x in d.get(k,[]) if 'uri' in x],'moving_nodes':moving}
 assert not report[os.path.basename(path)]['external_uris']
json.dump(report,open(R+'/GLB_VALIDATION.json','w'),indent=2)
for n,r in report.items():print(n,{k:v for k,v in r.items() if k!='moving_nodes'})
