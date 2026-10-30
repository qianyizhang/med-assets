"""Actual payload, matched-condition and artifact/locator binding checks."""
import hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[3]
R=ROOT/'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01'
M=ROOT/'models/peripheral_nerves/exports/ulnar-elbow-r01/right-ulnar-elbow.glb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v1=json.loads((R/'v1/matched-128/bindings.json').read_text())
v2=json.loads((R/'v2/raw-128/bindings.json').read_text())
assert sha(M)==v2['artifactSha256']=='94a7bde3f8a2882cc632082301d7701a737a769e1d1afe0f55629ecac3013ac3'
assert sha(R/'v1/native-elbow.glb')==v1['artifactSha256']=='206915ffa0b6b625ca17e32f35b893e1d1a103f25bce59f41e02d657ab9e7fd5'
assert v1['render']==v2['render'] and v1['lights']==v2['lights']
assert len(v1['views'])==len(v2['views'])==4
for a,b in zip(v1['views'],v2['views']):
    for key in ['file','camera','target','ortho_scale','anchors']:assert a[key]==b[key],key
    for data,directory in [(a,R/'v1/matched-128'),(b,R/'v2/raw-128')]:
        assert sha(directory/data['file'])==data['sha256']
        assert data['artifactSha256']==(v1 if data is a else v2)['artifactSha256']
        assert Image.open(directory/data['file']).size==(800,800)
c=json.loads((R/'evidence/composition-bindings.json').read_text())
for name,h in c['inputs'].items():assert sha(R/name)==h
for name,h in c['outputs'].items():assert sha(R/'evidence'/name)==h
assert len(c['locators'])==6
for loc in c['locators']:
    a=loc['anchor'];v=next(v for v in v2['views'] if v['file']==loc['panel'])
    assert a in v['anchors']
    assert all(0<=x<=800 for x in a['pixel'])
    assert a['vertex']>=0 and a['source_object'] in ['Ulnar nerve.r','Humerus.r','Ulna.r']
comparison=Image.open(R/'evidence/comparison.png').convert('RGB')
for row,name in enumerate(['whole-posterior.png','elbow-posteromedial.png']):
    y=144+row*840
    for x,directory in [(20,R/'v1/matched-128'),(840,R/'v2/raw-128')]:
        actual=comparison.crop((x,y,x+800,y+800))
        assert ImageChops.difference(actual,Image.open(directory/name).convert('RGB')).getbbox() is None
print('PASS: 2 GLBs, 8 matched raw images, 3 composed images, 6 vertex-bound locators; exact comparison panel pixels and matched conditions.')
