#!/usr/bin/env python3
"""Reproduce the historical five-patch source subset from the public immutable raw GLB.
No raw source or full material-only intermediate is written/copied. Geometry streams are packed losslessly.
"""
import argparse,json,struct,pathlib,copy,hashlib,numpy as np
p=argparse.ArgumentParser();p.add_argument('--raw',required=True,type=pathlib.Path);p.add_argument('--output',required=True,type=pathlib.Path);p.add_argument('--receipt',required=True,type=pathlib.Path);args=p.parse_args()
raw=args.raw.read_bytes();sourceHash=hashlib.sha256(raw).hexdigest()
if len(raw)!=103690760 or sourceHash!='bd8e24e9d52b49719c6a1cafa1f54fc40c1d3f811b9d32df78d5c20ebb78c197':raise SystemExit('Wrong raw source: exact bytes/hash required; no output written')
jlen,jtype=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+jlen]);binary=memoryview(raw)[28+jlen:];tail=memoryview(raw)[20+jlen:]
colors=[[.45,.34,.17,1]]*3+[[.42,.16,.19,1],[.4,.12,.14,1],[.42,.14,.17,1],[.39,.09,.12,1],[.44,.16,.19,1],[.68,.62,.48,1]]
for i,m in enumerate(g['materials']):
 m['pbrMetallicRoughness']['baseColorFactor']=colors[i];m['pbrMetallicRoughness']['roughnessFactor']=.62;m['pbrMetallicRoughness']['metallicFactor']=0;m.pop('alphaMode',None);m['name']='Display_'+m['name'];m['extras']={'displayNote':'Illustrative non-measured matte color. Opaque layer inspection; no geometry or normal changes.'}
g['asset']['extras']={'sourceSha256':sourceHash,'sourceReference':'https://lod.humanatlas.io/ref-organ/mouth-female/v1.0','license':'CC BY 4.0','changes':'Material JSON only: illustrative colors, roughness 0.62 and opaque cheek/frenula. All source BIN bytes, nodes, transforms, names, mesh definitions and attributes retained. No reconstruction, registration or smoothing.'}
# Verify the old material-only stage by streaming its serialization into SHA-256, not by writing a103MB copy.
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);h=hashlib.sha256();h.update(struct.pack('<4sII',b'glTF',2,20+len(j)+len(tail)));h.update(struct.pack('<II',len(j),jtype));h.update(j);h.update(tail);materialHash=h.hexdigest();assert materialHash=='7527f09810df6bf59d523304e675795175e24d6cf32799f5ad8e4c866df3cc89'
names=['VH_F_mouth','VH_F_tongue','VH_F_posterior_part_of_tongue','VH_F_dorsal_tongue','VH_F_ventral_tongue','VH_F_fungiform_papillae','VH_F_circumvallate_papillae'];nis=[i for i,n in enumerate(g['nodes']) if n['name'] in names];ni_map={old:new for new,old in enumerate(nis)};mis=[g['nodes'][i]['mesh'] for i in nis if 'mesh' in g['nodes'][i]];mi_map={old:new for new,old in enumerate(mis)};ais=sorted(set(i for m in mis for pri in g['meshes'][m]['primitives'] for i in [pri['indices'],*pri['attributes'].values()]));ai_map={old:new for new,old in enumerate(ais)};vis=sorted(set(g['accessors'][i]['bufferView'] for i in ais));vi_map={old:new for new,old in enumerate(vis)};mats=sorted(set(pri['material'] for m in mis for pri in g['meshes'][m]['primitives']));ma_map={old:new for new,old in enumerate(mats)}
out={'asset':copy.deepcopy(g['asset']),'scene':0,'scenes':[{'nodes':[ni_map[0]],'name':'Tongue surfaces only — no internal musculature'}],'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'materials':[copy.deepcopy(g['materials'][i]) for i in mats]};buf=bytearray();receipt=[]
for i in ais:
 a=copy.deepcopy(g['accessors'][i]);v=g['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];item={5121:1,5123:2,5125:4,5126:4}[a['componentType']]*dim;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',item)
 b=np.ndarray((a['count'],),dtype='V'+str(item),buffer=binary,offset=start,strides=(stride,)).tobytes();vnew={'buffer':0,'byteOffset':len(buf),'byteLength':len(b)}
 if 'target' in v:vnew['target']=v['target']
 buf.extend(b);buf.extend(b'\0'*((-len(buf))%4));a['bufferView']=len(out['bufferViews']);a.pop('byteOffset',None);out['bufferViews'].append(vnew);out['accessors'].append(a);receipt.append({'sourceAccessor':i,'outputAccessor':ai_map[i],'logicalStreamSha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'byteExactStream':True})
for i in mis:
 m=copy.deepcopy(g['meshes'][i])
 for pri in m['primitives']:
  pri['indices']=ai_map[pri['indices']];pri['attributes']={k:ai_map[v] for k,v in pri['attributes'].items()};pri['material']=ma_map[pri['material']]
 out['meshes'].append(m)
for i in nis:
 n=copy.deepcopy(g['nodes'][i]);n['extras']=dict(n.get('extras',{}),sourceNodeIndex=i)
 if 'children' in n:n['children']=[ni_map[j] for j in n['children'] if j in ni_map]
 if 'mesh' in n:n['mesh']=mi_map[n['mesh']]
 out['nodes'].append(n)
out['buffers']=[{'byteLength':len(buf)}];out['asset']['extras']['changes']+=' Scoped subset retains five source tongue meshes and unchanged root/tongue hierarchy; unused mesh streams omitted losslessly. Not whole mouth or internal tongue musculature.'
j=json.dumps(out,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=struct.pack('<4sII',b'glTF',2,28+len(j)+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf
outputHash=hashlib.sha256(b).hexdigest();assert len(b)==16647708 and outputHash=='a76dc3c882994ff1515f30f9047872a634a6cdf9275e1eec7b4aa9ba13633d12'
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open('xb') as f:f.write(b)
rec={'rawSourceSHA256':sourceHash,'rawSourceBytes':len(raw),'materialOnlyIntermediateSHA256StreamedNotWritten':materialHash,'outputSHA256':outputHash,'outputBytes':len(b),'retainedSourceNodeIndices':nis,'retainedSourceMeshIndices':mis,'logicalStreams':receipt,'method':'Historical material JSON edit plus byte-exact per-accessor extraction. No raw/full intermediate copy, coordinate transform, welding, reconstruction or normal edit.','verifiedScope':'Raw source to historical five-patch subset only; not a full authored geometry pipeline replay'}
args.receipt.parent.mkdir(parents=True,exist_ok=True)
with args.receipt.open('x') as f:json.dump(rec,f,indent=2)
print(json.dumps({k:v for k,v in rec.items() if k!='logicalStreams'},indent=2))
