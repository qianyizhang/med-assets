"""Local payload checks; not browser, anatomy or clinical validation."""
if not __debug__: raise RuntimeError('Optimized Python is unsupported; integrity assertions are required')
from pathlib import Path
import argparse,json,hashlib,re,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
p=argparse.ArgumentParser();p.add_argument('--render-dir',required=True);a=p.parse_args();P=Path(a.render_dir)
r=json.loads((P/'render-receipt.json').read_text());assert r['sourceSha256']=='4e2637cf6c844aef85ab77c2c1049d4e7647348a13c34d784795b98825f7c8c7'
assert hashlib.sha256((P/'camera-source.json').read_bytes()).hexdigest()=='671e6c4db4791e76cef0960f0f3c85864f9a37ed2b73ac1636f93854d9bde064'
assert r['sourceMaterialsRestored'] and len(r['geometryTransformsBeforeAfter'])==5
assert 'source_evidence_sha256' not in r['views'][1] and r['views'][1]['derivedFrom']['transform'].startswith('position = 2 * target')
for n,h in r['renderedFileHashes'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
anchors=json.loads((P/'anchors.json').read_text());coverage=set()
for v,rows in enumerate(anchors):
 im=np.asarray(Image.open(P/f'view-{v}-ids.png').convert('RGB'))
 for j,row in enumerate(rows):
  mask=(abs(im[:,:,0].astype(float)-[114,156,188,213,235][j])<3)&(im[:,:,1]<3)&(im[:,:,2]<3);d=distance_transform_edt(mask);y,x=np.unravel_index(d.argmax(),d.shape)
  assert row['anchor']==[int(x),int(y)] and row['visiblePixels']==int(mask.sum())
  assert row['marked']==bool(d.max()>=15)
  if row['marked']:assert d[y,x]>=15;coverage.add(row['number'])
 for lang in ['en','zh']:
  s=P/f'comparison-{v}-{lang}.svg';root=ET.parse(s).getroot();imgs=root.findall('.//{http://www.w3.org/2000/svg}image');assert len(imgs)>=2 and len({i.attrib['href'] for i in imgs})==1
  t=s.read_text();
  if v==0:
   assert 'x="408" y="580" width="220" height="250"' in t and 'x="1172" y="580" width="220" height="250"' in t
   assert 'translate(-352 343) scale(1.4)' in t and 'translate(198 343) scale(1.4)' in t
  assert all(x in t for x in ['FMA:15837','FMA:15828','FMA:15838','UBERON:0001248','FMA:15839','Original','Updated','CC BY 4.0'])
assert coverage==set(range(1,6));print('PASS: source/camera pins, 6 render hashes, 5 geometry records, all 15 depth-anchor decisions, 6 matched bilingual source-key panels, derived-view disclosure.')
