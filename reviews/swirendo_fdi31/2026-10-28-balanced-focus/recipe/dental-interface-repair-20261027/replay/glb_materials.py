"""Add explicit nonmetallic materials; preserve mesh buffers and vertex colors."""
import json,struct

def explicit_materials(blob):
 n,t=struct.unpack_from('<II',blob,12);assert t==0x4e4f534a
 doc=json.loads(blob[20:20+n]);tail=blob[20+n:]
 doc['materials']=[]
 for mesh in doc['meshes']:
  name=mesh.get('name','source_layer')
  idx=len(doc['materials']);doc['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':.7},'doubleSided':True})
  for primitive in mesh['primitives']:primitive['material']=idx
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
 return struct.pack('<III',0x46546c67,2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
