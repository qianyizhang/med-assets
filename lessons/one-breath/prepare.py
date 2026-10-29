"""Stage exact existing local assets and the repository's pinned Three.js vendor files."""
import argparse,hashlib,json,shutil,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True);p.add_argument('--trachea-root',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'.local');a=p.parse_args()
if a.out.exists():raise FileExistsError('Use a new local staging directory')
manifest=json.loads((ROOT/'assets.json').read_text());sources=[]
for item in manifest['assets']:
 source=(a.trachea_root/item['file']) if item['id'].startswith('trachea') else (a.asset_root/item['source'])
 raw=source.read_bytes()
 if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Wrong or unresolved local asset: '+item['id'])
 sources.append((item,raw))
a.out.mkdir(parents=True)
for item,raw in sources:(a.out/item['file']).write_bytes(raw)
fixture=json.loads((ROOT.parents[1]/'ci/glb-runtime-fixture.json').read_text())
for item in fixture['resources']:
 if not item['path'].startswith('vendor/'):continue
 with urllib.request.urlopen(item['url'],timeout=45) as r:raw=r.read()
 if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Dependency identity mismatch')
 target=a.out/item['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(a.out/'vendor/package.json').write_text('{"name":"three","type":"module","exports":"./build/three.module.js"}\n')
(a.out/'staging-receipt.json').write_text(json.dumps({'assets':manifest['assets'],'threeVersion':fixture['threeVersion'],'source':'Existing local models; official dependency bytes pinned by current repository fixture'},indent=2)+'\n')
print('Prepared local assets and pinned Three.js',fixture['threeVersion'])
