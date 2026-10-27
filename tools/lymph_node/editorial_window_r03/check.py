"""Check actual r03 GLB surfaces; source hashes and geometry are separate gates."""

import argparse

import copy

import hashlib

import json

import math

from pathlib import Path

import struct

import subprocess

import sys
import tempfile

from gltf_source import load, accessor, world_blender, dot, EDITED, SOURCE_SHA

TOLERANCE = 5e-8

CANDIDATE_SHA = '2f6f65e98ccd280166343fd6a9d1a59f3d5e97830759dd531d80a43f27487194'

def sub(a,b):return tuple(x-y for x,y in zip(a,b))

def add(a,b):return tuple(x+y for x,y in zip(a,b))

def mul(a,t):return tuple(x*t for x in a)

def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def norm(a):return math.sqrt(dot(a,a))

def segment_distance(p,a,b):
    ab=sub(b,a);t=max(0,min(1,dot(sub(p,a),ab)/dot(ab,ab))) if dot(ab,ab) else 0
    return norm(sub(p,add(a,mul(ab,t))))

def triangle_distance(p,a,b,c):
    if p in (a,b,c):return 0
    ab=sub(b,a);ac=sub(c,a);ap=sub(p,a);n=cross(ab,ac);denom=dot(n,n)
    if not denom:return min(segment_distance(p,a,b),segment_distance(p,b,c),segment_distance(p,c,a))
    wb=dot(cross(ap,ac),n)/denom;wc=dot(cross(ab,ap),n)/denom
    if wb>=0 and wc>=0 and wb+wc<=1:
        return abs(dot(ap,n))/math.sqrt(denom)
    return min(segment_distance(p,a,b),segment_distance(p,b,c),segment_distance(p,c,a))

def validate(sd,sb,cd,cb,mapping,window):
    if cb[:len(sb)]!=sb:
        raise ValueError('Original binary prefix changed')
    normalized=copy.deepcopy(cd)
    normalized['buffers']=sd['buffers'];normalized['bufferViews']=normalized['bufferViews'][:len(sd['bufferViews'])]
    normalized['accessors']=normalized['accessors'][:len(sd['accessors'])]
    declared=copy.deepcopy(cd.get('extras',{}))
    presentation=declared.pop('editorialPresentation',None)
    if declared!=sd.get('extras',{}) or not presentation or presentation.get('sourceSha256')!=SOURCE_SHA or presentation.get('status')!='local-unapproved-candidate':
        raise ValueError('Original extras changed or candidate scope missing')
    normalized.pop('extras',None)
    if 'extras' in sd:normalized['extras']=sd['extras']
    if presentation.get('networkDisplayLabel')!='Source vascular network (identity unresolved)':
        raise ValueError('Neutral network display label changed')
    positions=[world_blender(v) for m in sd['meshes'] for v in accessor(sd,sb,m['primitives'][0]['attributes']['POSITION'])]
    expected_center=tuple((min(v[i] for v in positions)+max(v[i] for v in positions))/2 for i in range(3))
    if tuple(window['centerBlender'])!=expected_center or tuple(window['cameraFront'])!=(1/math.sqrt(5.25),-2/math.sqrt(5.25),.5/math.sqrt(5.25)) or tuple(window['cameraRight'])!=(2/math.sqrt(5),1/math.sqrt(5),0) or window['rightThresholdMetres']!=-.0008 or window['frontThresholdMetres']!=-.0008:
        raise ValueError('Exact historical clipping planes changed')
    center=window['centerBlender'];front=window['cameraFront'];right=window['cameraRight']
    rt=dot(center,right)+window['rightThresholdMetres'];ft=dot(center,front)+window['frontThresholdMetres']
    rows=[]
    for i,m in enumerate(sd['meshes']):
        p=m['primitives'][0];cp=cd['meshes'][i]['primitives'][0]
        if m['name'] not in EDITED:
            if cd['meshes'][i]!=m:
                raise ValueError('Source interior mesh changed: '+m['name'])
            continue
        other_fields=copy.deepcopy(cp)
        other_fields['attributes']=p['attributes'];other_fields['indices']=p['indices']
        if other_fields!=p:
            raise ValueError('Edited primitive material or undeclared fields changed')
        if set(p['attributes'])!=set(cp['attributes']):
            raise ValueError('Attribute set changed')
        for name,idx in p['attributes'].items():
            original=accessor(sd,sb,idx);new=accessor(cd,cb,cp['attributes'][name])
            if new[:len(original)]!=original or not all(math.isfinite(x) for v in new for x in v):
                raise ValueError('Original attribute values changed or nonfinite output')
        verts=accessor(sd,sb,p['attributes']['POSITION']);outverts=accessor(cd,cb,cp['attributes']['POSITION'])
        inds=[v[0] for v in accessor(sd,sb,p['indices'])];newinds=[v[0] for v in accessor(cd,cb,cp['indices'])]
        if len(newinds)%3 or max(newinds)>=len(outverts):raise ValueError('Invalid output indices')
        ids=mapping[m['name']]
        if len(ids)!=len(newinds)//3:raise ValueError('Incomplete source-triangle map')
        max_distance=0;min_orientation=1;total_area=0
        for j,source_id in enumerate(ids):
            source_tri=[verts[k] for k in inds[source_id*3:source_id*3+3]]
            outtri=[outverts[k] for k in newinds[j*3:j*3+3]]
            normal=cross(sub(outtri[1],outtri[0]),sub(outtri[2],outtri[0]))
            source_normal=cross(sub(source_tri[1],source_tri[0]),sub(source_tri[2],source_tri[0]))
            if not norm(normal):raise ValueError('New zero-area triangle')
            orientation=dot(normal,source_normal)/(norm(normal)*norm(source_normal))
            if orientation<=0:raise ValueError('Reoriented triangle')
            min_orientation=min(min_orientation,orientation);total_area+=norm(normal)/2
            distances=[triangle_distance(v,*source_tri) for v in outtri]
            max_distance=max(max_distance,*distances)
            if max(distances)>TOLERANCE:raise ValueError('Output leaves assigned source triangle by >5e-8m')
            world=[world_blender(v) for v in outtri]
            if not (all(dot(v,right)<=rt+TOLERANCE for v in world) or all(dot(v,front)<=ft+TOLERANCE for v in world)):
                raise ValueError('Triangle crosses removed display window')
        normalized['meshes'][i]['primitives'][0]=p
        source_area=sum(norm(cross(sub(verts[inds[k+1]],verts[inds[k]]),sub(verts[inds[k+2]],verts[inds[k]])))/2 for k in range(0,len(inds),3))
        rows.append({'node':m['name'],'triangles':len(newinds)//3,'maxVertexToAssignedSourceTriangleMetres':max_distance,
            'minimumSourceNormalCosine':min_orientation,'retainedSurfaceAreaFraction':total_area/source_area})
    if normalized!=sd:raise ValueError('Undeclared source document change')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate-dir', type=Path, required=True)
    parser.add_argument('--replay-output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    options = parser.parse_args()
    if options.report.exists() or options.replay_output.exists():
        raise FileExistsError('Report and replay output must both be new')
    if hashlib.sha256(options.source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Pinned source mismatch')
    candidate = options.candidate_dir / 'lymph-node-editorial-window-r03.glb'
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != CANDIDATE_SHA:
        raise ValueError('Pinned candidate mismatch')
    receipt = json.loads((options.candidate_dir / 'build-receipt.json').read_text())
    mapping = json.loads((options.candidate_dir / 'triangle-source-map.json').read_text())
    if receipt['sourceSha256'] != SOURCE_SHA or receipt['candidateSha256'] != CANDIDATE_SHA:
        raise ValueError('Receipt identity mismatch')
    sd, sb = load(options.source)
    cd, cb = load(candidate)
    rows = validate(sd, sb, cd, cb, mapping, receipt['window'])
    negatives = []

    def rejects(name, document, binary, expected, window=None):
        # Deliberately bypass only candidate-byte identity to exercise semantic guards.
        try:
            validate(sd, sb, document, binary, mapping, window or receipt['window'])
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError(f'{name}: wrong rejection: {error}') from error
            negatives.append({'case': name, 'rejection': str(error)})
        else:
            raise AssertionError(f'{name}: corruption was accepted')

    broken = copy.deepcopy(cd)
    broken['extras']['editorialPresentation']['networkDisplayLabel'] = 'Blood vessels confirmed'
    rejects('unsupported vessel identity', broken, cb, 'Neutral network display label')
    broken = copy.deepcopy(cd)
    broken['nodes'][1]['extras']['label'] = 'invented tissue'
    rejects('provider annotation changed', broken, cb, 'Undeclared source document change')
    broken = copy.deepcopy(cd)
    broken['nodes'][0]['translation'] = [0.001, 0, 0]
    rejects('source transform changed', broken, cb, 'Undeclared source document change')
    broken = copy.deepcopy(cd)
    broken['materials'][0]['name'] = 'incorrect material'
    rejects('source material changed', broken, cb, 'Undeclared source document change')
    window = copy.deepcopy(receipt['window'])
    window['frontThresholdMetres'] += 0.001
    rejects('clipping plane changed', cd, cb, 'Exact historical clipping planes', window)
    broken = bytearray(cb)
    broken[0] ^= 1
    rejects('original source binary changed', cd, bytes(broken), 'Original binary prefix')
    network = next(m for m in cd['meshes'] if m['name'] == 'Yao_blood_vasculature')
    index = cd['accessors'][network['primitives'][0]['indices']]
    view = cd['bufferViews'][index['bufferView']]
    offset = view.get('byteOffset', 0) + index.get('byteOffset', 0)
    triangle = struct.unpack_from('<III', cb, offset)
    broken = bytearray(cb)
    struct.pack_into('<III', broken, offset, triangle[0], triangle[0], triangle[0])
    rejects('serialized zero-area fragment', cd, bytes(broken), 'New zero-area triangle')
    broken = bytearray(cb)
    struct.pack_into('<III', broken, offset, triangle[0], triangle[2], triangle[1])
    rejects('reversed network triangle', cd, bytes(broken), 'Reoriented triangle')

    builder = Path(__file__).with_name('build.py')
    command = [sys.executable, str(builder), '--source', str(options.source),
               '--output', str(options.replay_output)]
    replay = subprocess.run(command, capture_output=True, text=True)
    if replay.returncode or (options.replay_output / candidate.name).read_bytes() != candidate.read_bytes():
        raise AssertionError('Replay failed or output bytes changed: ' + replay.stderr)
    overwrite = subprocess.run(command, capture_output=True, text=True)
    if not overwrite.returncode or 'FileExistsError' not in overwrite.stderr:
        raise AssertionError('Existing-output guard failed')
    negatives.append({'case': 'existing output', 'rejection': 'FileExistsError'})
    with tempfile.TemporaryDirectory(prefix='lymph-r03-source-') as temporary:
        bad_source = Path(temporary) / 'wrong-source.glb'
        data = bytearray(options.source.read_bytes())
        data[-1] ^= 1
        bad_source.write_bytes(data)
        wrong = subprocess.run([sys.executable, str(builder), '--source', str(bad_source),
                                '--output', str(Path(temporary) / 'output')],
                               capture_output=True, text=True)
        if not wrong.returncode or 'Pinned source mismatch' not in wrong.stderr:
            raise AssertionError('Wrong-source guard failed')
    negatives.append({'case': 'wrong source hash', 'rejection': 'Pinned source mismatch'})
    result = {'sourceSha256': SOURCE_SHA, 'candidateSha256': CANDIDATE_SHA,
              'editedSurfaces': rows, 'negativeControls': negatives,
              'deterministicReplayByteExact': True,
              'scope': 'Source-constrained GLB checks and replay only; no visual, anatomical, clinical or browser-runtime approval.'}
    with options.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(f'PASS: source surfaces, byte-exact replay and {len(negatives)} negative controls; other gates remain separate.')


if __name__ == '__main__':
    main()
