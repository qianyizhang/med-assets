"""Check hydrated local candidates, native provenance, image bindings and pairs."""
import argparse, hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'heart/exterior-presentation-r01'
REVIEW=ROOT/'reviews/heart_exterior/2026-10-30-native-visibility-r01'
spec=importlib.util.spec_from_file_location('pair',Path(__file__).with_name('verify_pair.py'))
pair=importlib.util.module_from_spec(spec);spec.loader.exec_module(pair)
p=argparse.ArgumentParser();p.add_argument('--source-repo',type=Path,required=True);a=p.parse_args()
visibility=json.loads((PACKAGE/'visibility-spec.json').read_text())
names=set(visibility['opaque_exterior_hidden_names'])
for fn,source in zip(['native-visibility-contract.json','animated-native-visibility-contract.json'],visibility['native_sources']):
    receipt=json.loads((REVIEW/'checks'/fn).read_text())
    assert receipt['source_sha256']==source['sha256']
    assert hashlib.sha256((a.source_repo/source['file']).read_bytes()).hexdigest()==source['sha256']
    assert set(receipt['member_names'])==names and receipt['member_count']==123
    assert receipt['all_member_drivers_identical'] is True
    assert {d['path'] for d in receipt['common_drivers']}=={'hide_render','hide_viewport'}
    assert all(d['expression']==visibility['rule']['expression'] for d in receipt['common_drivers'])
    for state in receipt['evaluated_states']:
        expected=123 if state['cutaway']==0 and state['material_set']<1.5 else 0
        assert state['hidden_render_count']==state['hidden_viewport_count']==expected
results={}
for kind,source,prefix in [
    ('static','body/anatomy-workshop-r1/meshes/heart_detailed.glb','static'),
    ('animated-source','heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb','animated-source')]:
    candidate=PACKAGE/'exports'/(kind+'-opaque-exterior.glb')
    result=pair.verify(a.source_repo/source,candidate,PACKAGE/'visibility-spec.json')
    retained=json.loads((REVIEW/'checks'/(kind+'-verify.json')).read_text())
    assert result==retained
    original=json.loads((REVIEW/('original-'+prefix+'-bindings.json')).read_text())
    updated=json.loads((REVIEW/('updated-'+prefix+'-bindings.json')).read_text())
    assert original['sha256']==result['source_sha256'] and updated['sha256']==result['candidate_sha256']
    assert original['lights']==updated['lights'] and original['bounds']==updated['bounds']
    assert original['frame']==updated['frame']==0 and original['fps']==updated['fps']==30
    before={v['view']:v for v in original['views']};after={v['view']:v for v in updated['views']}
    assert set(before)==set(after)
    for name in before:
        for field in ['camera','rotation','target','orthoScale']:
            assert before[name][field]==after[name][field]
    for binding in [original,updated]:
        for view in binding['views']:
            image=(REVIEW/view['file']).resolve()
            assert image.is_relative_to(REVIEW.resolve())
            assert hashlib.sha256(image.read_bytes()).hexdigest()==view['sha256']
    results[kind]={'artifact':result['candidate_sha256'],'matched_views':len(before),'exterior_meshes':result['visible_mesh_nodes']}
print(json.dumps({'passed':results,'scope':'Local hydrated provenance/payload/image and matching-condition checks; no new pixel-review, anatomy, runtime or publication approval'},indent=2))
