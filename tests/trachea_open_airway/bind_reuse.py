"""Bind reused cavity evidence to identical decoded shell data in a later export."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--previous-dir',type=Path,required=True);p.add_argument('--current-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.out.exists():raise FileExistsError(a.out)
def shell(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
 node=next(x for x in g['nodes'] if x.get('name','').startswith('Trachea |'));m=g['meshes'][node['mesh']]
 def accessor(index):
  ac=g['accessors'][index];v=g['bufferViews'][ac['bufferView']];width={5121:1,5123:2,5125:4,5126:4}[ac['componentType']]*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[ac['type']]
  offset=v.get('byteOffset',0)+ac.get('byteOffset',0);stride=v.get('byteStride',width)
  data=b''.join(binary[offset+i*stride:offset+i*stride+width] for i in range(ac['count']))
  return {'count':ac['count'],'type':ac['type'],'componentType':ac['componentType'],'sha256':hashlib.sha256(data).hexdigest()}
 data={'transform':{k:node[k] for k in ('matrix','translation','rotation','scale') if k in node},'primitives':[{'attributes':{k:accessor(i) for k,i in sorted(pr['attributes'].items())},'indices':accessor(pr['indices'])} for pr in m['primitives']]}
 return {'artifact_sha256':hashlib.sha256(raw).hexdigest(),'shell_signature':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'decoded_shell_data':data}
rows=[]
for variant in ('open','cutaway'):
 previous=shell(a.previous_dir/f'trachea-{variant}.glb');current=shell(a.current_dir/f'trachea-{variant}.glb')
 assert previous['decoded_shell_data']==current['decoded_shell_data'],'Shell changed; reused cavity checks no longer apply'
 rows.append({'variant':variant,'previous':previous,'current':current,'shell_identical':True})
a.out.write_text(json.dumps({'variants':rows,'scope':'Exact decoded shell positions, normals, indices and node transform unchanged. Band cap cleanup is excluded from this reuse claim; its affected geometry/pixels are reviewed separately.'},indent=2)+'\n')
print('PASS: both shell geometries/normals/indices/transforms unchanged; V6 cavity evidence reusable')
