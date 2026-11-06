"""Rebuild issue 102's local, unapproved material-only teaching-color trial."""
import argparse, copy, hashlib, json, struct
from pathlib import Path

BASELINE_SHA = 'e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5'
CANDIDATE_SHA = 'c7ec6420edbd62f94b85610e1c51f6fa4dd31dc008248c19a9731ac5cef0c311'
PALETTE = ['A93664', 'F2D38C', '276D8A', 'D1905A', '596878']

def digest(data): return hashlib.sha256(data).hexdigest()
def linear(x): return x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4
def chunks(data):
    assert struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data))
    out=[]; offset=12
    while offset < len(data):
        length, kind=struct.unpack_from('<II',data,offset); offset+=8
        assert length%4==0 and offset+length<=len(data)
        out.append((kind,data[offset:offset+length]));offset+=length
    assert offset==len(data) and out[0][0]==0x4e4f534a
    return out

def main():
    if not __debug__:
        raise RuntimeError('Palette replay requires Python assertions; do not use -O')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--params',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args(); raw=a.input.read_bytes()
    assert digest(raw)==BASELINE_SHA, 'Unrecognized baseline'
    original=chunks(raw); doc=json.loads(original[0][1]); updated=copy.deepcopy(doc)
    assert len(doc['materials'])==len(doc['meshes'])==5
    changes=[]
    for index,(material,color) in enumerate(zip(updated['materials'],PALETTE)):
        assert material['name'].startswith(f'{index+1:02d} ')
        pbr=material['pbrMetallicRoughness']; before=pbr['baseColorFactor']
        pbr['baseColorFactor']=[linear(int(color[i:i+2],16)/255) for i in (0,2,4)]+[1]
        changes.append({'material':material['name'],'oldLinearRGBA':before,
                        'newSRGBHex':'#'+color,'newLinearRGBA':pbr['baseColorFactor']})
    json_bytes=json.dumps(updated,separators=(',',':'),ensure_ascii=False).encode()
    json_bytes+=b' '*((-len(json_bytes))%4)
    new_chunks=[(original[0][0],json_bytes)]+original[1:]
    body=b''.join(struct.pack('<II',len(data),kind)+data for kind,data in new_chunks)
    candidate=struct.pack('<4sII',b'glTF',2,len(body)+12)+body
    # An independent reconstruction allows only the five named material colors.
    check=json.loads(chunks(candidate)[0][1])
    for index,material in enumerate(check['materials']):
        material['pbrMetallicRoughness']['baseColorFactor']=doc['materials'][index]['pbrMetallicRoughness']['baseColorFactor']
    assert check==doc, 'Change outside material colors'
    assert chunks(candidate)[1:]==original[1:], 'Binary geometry changed'
    assert digest(candidate)==CANDIDATE_SHA, 'Palette replay differs from reviewed local trial'
    a.output.mkdir(parents=True,exist_ok=False)
    for name,data,filename in [('baseline',raw,'esophagus-wall-cutaway-r01.glb'),
                               ('candidate',candidate,'esophagus-wall-palette-r01.glb')]:
        folder=a.output/name;folder.mkdir();(folder/filename).write_bytes(data)
        (folder/'parameters.json').write_bytes(a.params.read_bytes())
    receipt={'baselineSha256':digest(raw),'candidateSha256':digest(candidate),
             'baselineBytes':len(raw),'candidateBytes':len(candidate),
             'changedFields':['materials/'+str(i)+'/pbrMetallicRoughness/baseColorFactor' for i in range(5)],
             'allOtherJSONDeepEqual':True,'allNonJSONChunksByteIdentical':True,
             'binaryChunkSha256':[digest(data) for _,data in original[1:]],
             'palette':changes,'clinicalApproval':False,
             'scope':'Unapproved illustrative color coding; geometry, transforms, layer order, roughness and lighting unchanged.'}
    (a.output/'material-change-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
