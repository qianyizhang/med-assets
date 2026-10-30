"""Independent differential check of the exact source/candidate GLB payloads."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

def read(path):
    raw = path.read_bytes()
    if struct.unpack_from('<III', raw) != (0x46546c67, 2, len(raw)):
        raise ValueError('Incomplete GLB payload')
    n, tag = struct.unpack_from('<II', raw, 12)
    assert tag == 0x4e4f534a
    doc = json.loads(raw[20:20+n])
    nbin, tag = struct.unpack_from('<II', raw, 20+n)
    assert tag == 0x004e4942 and 28+n+nbin == len(raw)
    return doc, raw[28+n:], hashlib.sha256(raw).hexdigest()

def verify(source, candidate, spec_path):
    original, oldbin, source_sha = read(source)
    updated, newbin, candidate_sha = read(candidate)
    spec = json.loads(spec_path.read_text())
    hidden = set(spec['opaque_exterior_hidden_names'])
    assert oldbin == newbin, 'A geometry, morph, or sampler byte changed'
    assert len(hidden) == 123
    for field in set(original) | set(updated):
        if field not in {'asset','nodes','scenes','animations'}:
            assert original.get(field) == updated.get(field), field
    before = {n['name']: n for n in original['nodes']}
    after = {n['name']: n for n in updated['nodes']}
    cutaways = {n['name'] for n in original['nodes'] if n.get('extras',{}).get('view_role') == 'cutaway'}
    assert set(after) == set(before) - hidden - cutaways, 'Unexpected exterior membership'
    assert len(after) == len(updated['nodes'])
    def child_names(node, doc):
        return [doc['nodes'][i]['name'] for i in node.get('children', [])]
    for name, node in after.items():
        old = before[name]
        assert {k:v for k,v in node.items() if k != 'children'} == {k:v for k,v in old.items() if k != 'children'}, name
        assert child_names(node, updated) == [n for n in child_names(old, original) if n in after], name
    assert sum('mesh' in n for n in after.values()) == 124
    def reachable(doc):
        found = set()
        pending = list(doc['scenes'][doc.get('scene',0)]['nodes'])
        while pending:
            i = pending.pop()
            assert 0 <= i < len(doc['nodes']) and i not in found, 'Graph is not a single-parent forest'
            found.add(i)
            pending.extend(doc['nodes'][i].get('children', []))
        return found
    assert reachable(updated) == set(range(len(updated['nodes']))), 'Orphan candidate node'
    def channel_signature(animation, doc, names):
        return [{'sampler':c['sampler'], 'target':{
            **c['target'], 'node':doc['nodes'][c['target']['node']]['name']}}
            for c in animation['channels'] if doc['nodes'][c['target']['node']]['name'] in names]
    assert len(original.get('animations', [])) == len(updated.get('animations', []))
    tracks = 0
    for old, new in zip(original.get('animations', []), updated.get('animations', [])):
        assert {k:v for k,v in old.items() if k != 'channels'} == {k:v for k,v in new.items() if k != 'channels'}
        assert channel_signature(old, original, after) == channel_signature(new, updated, after), 'Motion track changed'
        tracks += len(new['channels'])
    def float_accessor(index):
        acc = updated['accessors'][index];view=updated['bufferViews'][acc['bufferView']]
        assert acc['componentType'] == 5126 and acc['type'] == 'SCALAR'
        assert 'sparse' not in acc and 'byteStride' not in view
        return struct.unpack_from('<'+'f'*acc['count'],newbin,view.get('byteOffset',0)+acc.get('byteOffset',0))
    sample_counts=set();clip_ends=set();loop_errors=[]
    for animation in updated.get('animations', []):
        for ch in animation['channels']:
            sampler=animation['samplers'][ch['sampler']]
            times=float_accessor(sampler['input']);weights=float_accessor(sampler['output'])
            assert ch['target']['path']=='weights'
            width=len(weights)//len(times)
            assert len(weights)==width*len(times) and width>0
            assert abs(times[0])<1e-6 and abs(times[-1]-.8)<1e-6
            assert sampler.get('interpolation','LINEAR')=='LINEAR'
            loop_errors.extend(abs(a-b) for a,b in zip(weights[:width],weights[-width:]))
            sample_counts.add(len(times));clip_ends.add(times[-1])
    assert not loop_errors or max(loop_errors)<1e-6
    return {'source_sha256':source_sha,'candidate_sha256':candidate_sha,
        'identical_bin_sha256':hashlib.sha256(newbin).hexdigest(),
        'unchanged_meshes_materials_accessors':True,'unchanged_retained_node_transforms':True,
        'unchanged_retained_morphs_and_sampler_bytes':True,'source_internal_nodes_excluded':123,
        'cutaway_duplicate_nodes_excluded':len(cutaways),'visible_mesh_nodes':124,
        'retained_animation_channels':tracks,'samples_per_retained_channel':sorted(sample_counts),
        'clip_end_seconds':sorted(clip_ends),'max_loop_weight_error':max(loop_errors,default=0),
        'scope':'Exact data and presentation-membership integrity; not actual viewer runtime, new physiology or repaired internal anatomy'}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('Refusing existing verification result')
    result=verify(a.source,a.candidate,a.spec)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
