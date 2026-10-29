"""Local shading/index repair: unchanged positions, winding, materials and colors."""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_source import load, accessor, write_glb
from build import append_accessor
from check import CANDIDATE_SHA, cross, sub, norm

# The input has only unit vectors (within 1.4e-7) or cancellation remnants
# below 1.1e-10. This threshold separates invalid remnants, not anatomy.
INVALID_LENGTH = 1e-6
UNIT_LENGTH_ERROR = 1e-5
# Declared display-normal angular budget for Blender's custom-normal encoding.
# 0.05 degrees is a small shading-direction budget, not exact identity.
NORMAL_ANGLE_DEGREES = .05


def values(doc, binary, index):
    a = doc['accessors'][index]
    if not a.get('normalized'):
        return accessor(doc,binary,index)
    if a['componentType'] not in (5121,5123) or a['type'] not in ('VEC3','VEC4') or 'sparse' in a:
        raise ValueError('Unsupported normalized attribute')
    size,fmt,scale = (1,'B',255) if a['componentType']==5121 else (2,'H',65535)
    dims = int(a['type'][-1]);view=doc['bufferViews'][a['bufferView']]
    offset=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',size*dims)
    return [tuple(x/scale for x in struct.unpack_from('<'+fmt*dims,binary,offset+i*stride))
            for i in range(a['count'])]


def unit(v):
    length = norm(v)
    if not length or not math.isfinite(length):
        raise ValueError('Missing or nonfinite normal')
    return tuple(x/length for x in v)


def repair_normal(normal, face):
    length = norm(normal)
    if not math.isfinite(length):
        raise ValueError('Nonfinite source normal')
    if length < INVALID_LENGTH:
        return unit(cross(sub(face[1], face[0]), sub(face[2], face[0]))), True
    if abs(length-1) > UNIT_LENGTH_ERROR:
        raise ValueError('Unexpected intermediate-length normal')
    return normal, False


def deindex(document, binary, repair=False, full_split=False):
    """Split colliding/invalid corners, or explicitly split all corner fans.

    Full splitting avoids Blender custom-normal fan degeneracy; ordinary shared
    fans remain unchanged in the minimal diagnostic variant. No positions move.
    """
    doc = copy.deepcopy(document)
    doc['bufferViews'] = []; doc['accessors'] = []; doc['buffers'] = [{'byteLength': 0}]
    out = bytearray(); changes = []
    for old_mesh, mesh in zip(document['meshes'], doc['meshes']):
        for old, primitive in zip(old_mesh['primitives'], mesh['primitives']):
            indices = [i[0] for i in accessor(document, binary, old['indices'])]
            attrs = {key: values(document, binary, index) for key,index in old['attributes'].items()}
            if set(attrs) != {'POSITION', 'NORMAL', 'COLOR_0'}:
                raise ValueError('Unexpected attributes')
            expanded = {key:[] if full_split else list(array) for key,array in attrs.items()}
            output_indices = []; seen = set()
            for start in range(0,len(indices),3):
                tri=indices[start:start+3]; key=tuple(sorted(tri)); collision=key in seen; seen.add(key)
                face=[attrs['POSITION'][i] for i in tri]
                for corner, index in enumerate(tri):
                    old_normal=attrs['NORMAL'][index]
                    new, changed=repair_normal(old_normal,face) if repair else (old_normal,False)
                    if full_split or collision or changed:
                        output_indices.append(len(expanded['POSITION']))
                        for attribute,array in attrs.items():
                            expanded[attribute].append(new if attribute=='NORMAL' else array[index])
                    else:
                        output_indices.append(index)
                    if changed:
                        changes.append({'mesh':mesh['name'],'face':start//3,'corner':corner,
                            'inputVertex':index,'inputNormal':old_normal,'inputLength':norm(old_normal),
                            'faceNormal':new})
            for key, attribute_values in expanded.items():
                primitive['attributes'][key] = append_accessor(doc,out,attribute_values,
                    document['accessors'][old['attributes'][key]]['type'],5126)
            primitive['indices']=append_accessor(doc,out,[(i,) for i in output_indices],'SCALAR',5125)
    doc['buffers'][0]['byteLength']=len(out)
    return doc,bytes(out),changes


def repair_extras(full_split=False):
    return {'status':'local-unapproved-candidate','inputSha256':CANDIDATE_SHA,
        'cornerStrategy':'full-split' if full_split else 'minimal-split',
        'policy':'The declared corner strategy changes index sharing only. Positions, winding, occurrences, colors and single-sided materials are unchanged. Only zero/near-zero normals use their existing oriented triangle normal. Full splitting avoids Blender custom-normal fan degeneracy at a measured byte cost.',
        'invalidNormalLengthBelow':INVALID_LENGTH,'validUnitLengthError':UNIT_LENGTH_ERROR,
        'normalAngularBudgetDegrees':NORMAL_ANGLE_DEGREES,
        'scope':'Shading representation only; no anatomical surface or outward-direction inference.'}


def validate_prepared(baseline_doc,baseline_binary,prepared_doc,prepared_binary):
    strategy=prepared_doc.get('extras',{}).get('displayRepair',{}).get('cornerStrategy')
    if strategy not in ('minimal-split','full-split'):
        raise ValueError('Unknown corner strategy')
    full_split=strategy=='full-split'
    expected,binary,changes=deindex(baseline_doc,baseline_binary,repair=True,full_split=full_split)
    expected.setdefault('extras',{})['displayRepair']=repair_extras(full_split)
    if expected!=prepared_doc or binary!=prepared_binary:
        raise ValueError('Prepared artifact differs from pinned-input repair policy')
    return changes


def attribute_faces(doc, binary):
    result = {}
    for mesh in doc['meshes']:
        p = mesh['primitives'][0]
        if len(mesh['primitives']) != 1:
            raise ValueError('Unexpected primitive count')
        attrs = {key: values(doc,binary,index) for key,index in p['attributes'].items()}
        if not {'POSITION','NORMAL','COLOR_0'} <= attrs.keys():
            raise ValueError('Missing normal or color attribute')
        attrs['COLOR_0'] = [tuple(c)+(1.,) if len(c)==3 else tuple(c) for c in attrs['COLOR_0']]
        indices = [x[0] for x in accessor(doc,binary,p['indices'])]
        rows = []
        for start in range(0,len(indices),3):
            tri = indices[start:start+3]
            positions = tuple(attrs['POSITION'][i] for i in tri)
            k = min(range(3), key=lambda j: positions[j:]+positions[:j])
            tri = tri[k:]+tri[:k]
            rows.append(tuple(tuple(attrs[key][i] for i in tri) for key in ('POSITION','NORMAL','COLOR_0')))
        result[mesh['name']] = rows
    return result


def compare_attributes(before, after, angle_degrees=NORMAL_ANGLE_DEGREES):
    """Match every oriented position/color/normal occurrence one-to-one."""
    if set(before) != set(after):
        raise ValueError('Object inventory changed')
    rows = []
    for name, expected in before.items():
        actual = after[name]
        if Counter((p,c) for p,n,c in expected) != Counter((p,c) for p,n,c in actual):
            raise ValueError('Oriented geometry, multiplicity or vertex color changed: '+name)
        groups = defaultdict(list)
        for p,n,c in expected:
            groups[(p,c)].append(n)
        actual_groups = defaultdict(list)
        for p,n,c in actual:
            for normal in n:
                if abs(norm(normal)-1)>UNIT_LENGTH_ERROR:
                    raise ValueError('Missing, zero or nonunit output normal: '+name)
            actual_groups[(p,c)].append(n)
        maximum = 0
        for key, originals in groups.items():
            targets = actual_groups[key]
            # Small coincident groups use a complete bipartite match, so a
            # source tuple cannot be reused and greedy pairing cannot hide loss.
            angles = [[max(math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(unit(a),unit(b)))))))
                           for a,b in zip(old,new)) for old in originals] for new in targets]
            def matching(limit):
                owners = {}
                def assign(i, visited):
                    for j,error in enumerate(angles[i]):
                        if error > limit or j in visited:
                            continue
                        visited.add(j)
                        if j not in owners or assign(owners[j], visited):
                            owners[j] = i
                            return True
                    return False
                return owners if all(assign(i,set()) for i in range(len(targets))) else None
            owners=matching(angle_degrees)
            if owners is None:
                raise ValueError('Normal direction or occurrence changed beyond declared angular budget: '+name)
            # Diagnostic 180-degree runs must not report a gratuitously bad
            # pairing of coincident faces. Find the smallest feasible maximum
            # angle, still using every source occurrence at most once.
            if len(targets)>1:
                levels=sorted({v for row in angles for v in row if v<=angle_degrees})
                low,high=0,len(levels)-1
                while low<high:
                    middle=(low+high)//2
                    if matching(levels[middle]) is None:low=middle+1
                    else:high=middle
                owners=matching(levels[low])
            maximum = max(maximum, *(angles[i][j] for j,i in owners.items()))
        rows.append({'mesh':name,'triangles':len(expected),'maxNormalAngleDegrees':maximum,
                     'vertexColorsExact':True,'orientedPositionsAndMultiplicityExact':True})
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--full-split',action='store_true',help='Separate all triangle corners to avoid Blender normal-fan degeneracy; increases bytes.')
    a=p.parse_args()
    if hashlib.sha256(a.input.read_bytes()).hexdigest()!=CANDIDATE_SHA:
        raise ValueError('Pinned r03 mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    doc,binary=load(a.input);out,blob,changes=deindex(doc,binary,repair=True,full_split=a.full_split)
    out.setdefault('extras',{})['displayRepair']=repair_extras(a.full_split)
    path=a.output/'prepared-display-repair.glb';write_glb(path,out,blob)
    receipt={'inputSha256':CANDIDATE_SHA,'preparedSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'repairedCorners':changes,'repairedCornerCount':len(changes),'normalPolicy':out['extras']['displayRepair']}
    (a.output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Prepared',len(changes),'invalid-normal corners; geometry and colors unchanged')


if __name__=='__main__':main()
