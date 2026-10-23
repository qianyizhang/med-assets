exec((__import__('pathlib').Path(__file__).parent/'audit_source.py').read_text().split('rows=[]')[0])
import copy,csv
sel=['VH_M_cornea_R','VH_M_iris_R','VH_M_lens_R','VH_M_ciliary_body_R','VH_M_ciliary_muscle_R','VH_M_ciliary_processes_R','VH_M_suspensory_ligament_of_lens_R']
palette={'VH_M_cornea_R':([.38,.63,.72,.14],.25),'VH_M_iris_R':([.10,.045,.012,1],.55),'VH_M_lens_R':([.34,.68,.76,1],.4),'VH_M_ciliary_body_R':([.42,.17,.17,1],.65),'VH_M_ciliary_muscle_R':([.31,.075,.105,1],.66),'VH_M_ciliary_processes_R':([.64,.30,.22,1],.58),'VH_M_suspensory_ligament_of_lens_R':([.68,.56,.34,1],.65)}
sourcehash=hashlib.sha256(b).hexdigest(); reports=[]
for mode in ['source-subset','material-only','normal-material']:
 out={'asset':{'version':'2.0','generator':'Exact source accessor subset; no position/triangle edits'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[{'byteLength':0}],'materials':[],'extras':{'scope':'Right anterior-segment layer study only, NOT complete eye or whole-body replacement. Posterior tissues and external anatomy excluded.','sourceSha256':sourcehash,'source':'HRA eye-male-right v1.3; CC BY 4.0','changes':mode}}
 blob=bytearray(); maps={}; rv=[]
 def add_data(raw):
  while len(blob)%4:blob.append(0)
  vi=len(out['bufferViews']);out['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(raw)});blob.extend(raw);return vi
 def cpacc(idx):
  if idx in maps:return maps[idx]
  a=copy.deepcopy(j['accessors'][idx]); values=arr(idx);a['bufferView']=add_data(values.tobytes());a.pop('byteOffset',None);ni=len(out['accessors']);out['accessors'].append(a);maps[idx]=ni;return ni
 for name in sel:
  orig=next(x for x in j['nodes'] if x['name']==name);node=copy.deepcopy(orig);node.pop('children',None);node['mesh']=len(out['meshes']);out['nodes'].append(node);out['scenes'][0]['nodes'].append(len(out['nodes'])-1)
  mesh=copy.deepcopy(j['meshes'][orig['mesh']]);note={'node':name,'sourceNodeId':j['nodes'].index(orig),'normalsChanged':False}
  for prim in mesh['primitives']:
   oldattr=prim['attributes'].copy();oi=prim['indices'];prim['indices']=cpacc(oi);prim['attributes']={k:cpacc(v) for k,v in oldattr.items()};mat=copy.deepcopy(j['materials'][prim['material']]);prim['material']=len(out['materials'])
   if mode!='source-subset':
    c,r=palette[name];mat={'name':name+' illustrative teaching color, not measured tissue','pbrMetallicRoughness':{'baseColorFactor':c,'metallicFactor':0,'roughnessFactor':r},'doubleSided':True}
    if c[3]<1:mat['alphaMode']='BLEND'
   out['materials'].append(mat)
   if mode=='normal-material':
    # Restrict smoothing to lens and cornea whose curvature is supported by source and references.
    # Ciliary and iris creases/ligament thin-sheet normals are left untouched rather than guessing.
    if name in ['VH_M_lens_R','VH_M_cornea_R']:
     v=arr(oldattr['POSITION']);nrm=arr(oldattr['NORMAL']);ix=arr(oi).reshape(-1,3);uv,inv=np.unique(v,axis=0,return_inverse=True);summ=np.zeros((len(uv),3));faces=np.cross(v[ix[:,1]]-v[ix[:,0]],v[ix[:,2]]-v[ix[:,0]])
     for k in range(3):np.add.at(summ,inv[ix[:,k]],faces)
     nn=summ/np.maximum(np.linalg.norm(summ,axis=1)[:,None],1e-30);new=nn[inv];dot=np.sum(new*nrm,axis=1);keep=dot>=np.cos(np.deg2rad(35));new[~keep]=nrm[~keep];a=copy.deepcopy(j['accessors'][oldattr['NORMAL']]);a['bufferView']=add_data(new.astype('<f4').tobytes());a.pop('byteOffset',None);prim['attributes']['NORMAL']=len(out['accessors']);out['accessors'].append(a);note.update({'normalsChanged':True,'sourceNormalsRetainedAtMoreThan35DegreeDifference':int((~keep).sum()),'vertices':len(v)})
  out['meshes'].append(mesh);rv.append(note)
 out['buffers'][0]['byteLength']=len(blob)
 js=json.dumps(out,separators=(',',':')).encode();js+=b' '*((-len(js))%4);blob+=b'\0'*((-len(blob))%4);glb=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
 path=D/'models'/(mode+'.glb');path.write_bytes(glb);reports.append({'mode':mode,'file':str(path.relative_to(D)),'sha256':hashlib.sha256(glb).hexdigest(),'bytes':len(glb),'selectedNodes':rv})
(D/'reviews/build-manifest.json').write_text(json.dumps({'sourceSha256':sourcehash,'selection':sel,'allOtherSourceNodesExcluded': [x['name'] for x in j['nodes'] if 'mesh'in x and x['name'] not in sel],'results':reports},indent=2));print(json.dumps(reports,indent=2))
