"""Actual-payload replay and failure checks for the exterior derivative recipe."""
import argparse, copy, importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
builder=module('exterior_builder',ROOT/'heart/exterior-presentation-r01/build.py')
verifier=module('exterior_verify',Path(__file__).with_name('verify_pair.py'))
p=argparse.ArgumentParser()
p.add_argument('--source-repo',type=Path,required=True)
p.add_argument('--candidates',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists(): raise ValueError('Refusing an existing regression receipt')
spec=ROOT/'heart/exterior-presentation-r01/visibility-spec.json'
checks=[]
def refused(label,fn):
    try: fn()
    except (ValueError,AssertionError): checks.append({'check':label,'result':'passed-rejected'})
    else: raise AssertionError('Guard unexpectedly accepted: '+label)

with tempfile.TemporaryDirectory(prefix='heart-exterior-guards-') as temp:
    scratch=Path(temp)
    for kind,(relative,expected,_) in builder.SOURCES.items():
        source=a.source_repo/relative
        candidate=a.candidates/kind/(kind+'-opaque-exterior.glb')
        original_bytes=candidate.read_bytes()
        replay=scratch/kind
        receipt=builder.build(a.source_repo,kind,replay)
        assert (replay/receipt['candidate_file']).read_bytes()==original_bytes
        checks.append({'check':kind+' deterministic replay','result':'passed-byte-identical','sha256':receipt['candidate_sha256']})
        refused(kind+' existing-output guard',lambda:builder.build(a.source_repo,kind,replay))
        assert (replay/receipt['candidate_file']).read_bytes()==original_bytes
        verifier.verify(source,candidate,spec)
        checks.append({'check':kind+' original-candidate differential integrity','result':'passed'})
        doc,binary=builder.read_glb(original_bytes)
        broken=scratch/(kind+'-corrupt-bin.glb')
        broken.write_bytes(builder.write_glb(doc,bytes([binary[0]^1])+binary[1:]))
        refused(kind+' changed-buffer rejection',lambda:verifier.verify(source,broken,spec))
        altered=copy.deepcopy(doc)
        next(n for n in altered['nodes'] if n['name']=='RV | complete wall')['translation']=[.01,0,0]
        broken.write_bytes(builder.write_glb(altered,binary))
        refused(kind+' changed-wall-transform rejection',lambda:verifier.verify(source,broken,spec))
        altered=copy.deepcopy(doc)
        next(n for n in altered['nodes'] if n['name']=='RV | complete wall')['name']='Unapproved replacement wall'
        broken.write_bytes(builder.write_glb(altered,binary))
        refused(kind+' changed-membership rejection',lambda:verifier.verify(source,broken,spec))
        if kind=='animated-source':
            altered=copy.deepcopy(doc)
            altered['animations'][0]['samplers'][0]['interpolation']='STEP'
            broken.write_bytes(builder.write_glb(altered,binary))
            refused('changed-animation-sampling rejection',lambda:verifier.verify(source,broken,spec))
    fake_repo=scratch/'substitute-source'
    relative=builder.SOURCES['static'][0];bad=fake_repo/relative;bad.parent.mkdir(parents=True)
    bad.write_bytes(b'version https://git-lfs.github.com/spec/v1\n')
    absent=scratch/'should-not-exist'
    refused('unhydrated-or-substitute-source rejection',lambda:builder.build(fake_repo,'static',absent))
    assert not absent.exists()
    copied=scratch/'recipe';copied.mkdir()
    (copied/'build.py').write_bytes((ROOT/'heart/exterior-presentation-r01/build.py').read_bytes())
    altered=json.loads(spec.read_text());altered['opaque_exterior_hidden_names'][0]='RV | complete wall'
    (copied/'visibility-spec.json').write_text(json.dumps(altered))
    bad_builder=module('bad_visibility_spec',copied/'build.py')
    refused('altered-native-membership-spec rejection',lambda:bad_builder.build(a.source_repo,'static',absent))
    assert not absent.exists()

a.output.write_text(json.dumps({'scope':'Actual two-source replay, no-overwrite and corruption/identity failure checks; no runtime or anatomy approval','checks':checks,'count':len(checks)},indent=2)+'\n')
print('PASS',len(checks),'replay/integrity/failure checks')
