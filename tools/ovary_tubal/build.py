"""Combine four pinned HRA exports without changing their native source content."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

MANIFEST = 'sources/datasets/hra/ovary-tubal-context/source-manifest.json'
GENERATOR = 'med-assets native ovary/tubal context r01'
KEYS = {'asset','scene','scenes','nodes','meshes','accessors','bufferViews','buffers','materials'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    require(len(data)>=28 and data[:4]==b'glTF', 'Expected hydrated GLB')
    magic,version,total=struct.unpack_from('<III',data)
    require(version==2 and total==len(data), 'Invalid GLB header')
    size,kind=struct.unpack_from('<II',data,12)
    require(kind==0x4e4f534a, 'Missing GLB JSON')
    doc=json.loads(data[20:20+size])
    cursor=20+size
    length,kind=struct.unpack_from('<II',data,cursor)
    require(kind==0x004e4942 and cursor+8+length==len(data), 'Unexpected GLB chunks')
    return doc,data[cursor+8:]


def encode(doc,payload):
    text=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
    text+=b' '*((-len(text))%4)
    payload+=b'\0'*((-len(payload))%4)
    return struct.pack('<III',0x46546c67,2,28+len(text)+len(payload))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(payload),0x004e4942)+payload


def read_sources(root):
    manifest=json.loads((root/MANIFEST).read_text())
    require(len(manifest['models'])==4, 'Expected four pinned sources')
    by_file={row['file']:row for row in manifest['files']}
    blobs={}
    for row in manifest['files']:
        data=(root/row['file']).read_bytes()
        require(len(data)==row['size'] and sha(data)==row['sha256'], 'Source identity mismatch: '+row['file'])
        require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['gitBlobSha1'], 'Git source blob mismatch')
        blobs[row['file']]=data
    sources=[]
    for name in manifest['models']:
        doc,payload=decode(blobs[name])
        require(set(doc)==KEYS and doc['scene']==0 and len(doc['scenes'])==1, 'Unsupported source schema')
        require(len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0], 'External source buffer')
        for node in doc['nodes']:
            require(not any(k in node for k in ('translation','rotation','scale','matrix')), 'Source frame changed')
            if 'mesh' in node:
                require(node['extras']['source_spatial_entity']=='#VHFemaleOrgans','Source entity changed')
        sources.append({'file':name,'sha256':by_file[name]['sha256'],'document':doc,'payload':payload})
    return manifest,sources


def combine(sources):
    out={'asset':{'version':'2.0','generator':GENERATOR},'scene':0,
         'scenes':[{'name':'Source-native ovary and tubal-end context','nodes':[],
                    'extras':{'sourceManifest':MANIFEST,'scope':'Coarse source-native relationships. Source labels, gaps and cuts retained; no follicle, attachment, uterus or lumen claim.'}}],
         'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[],'materials':[]}
    payload=bytearray()
    for source in sources:
        doc=source['document'];start=len(payload)
        offsets={k:len(out[k]) for k in ('nodes','meshes','accessors','bufferViews','materials')}
        payload.extend(source['payload']);payload.extend(b'\0'*((-len(payload))%4))
        for original in doc['bufferViews']:
            row=copy.deepcopy(original);row['buffer']=0;row['byteOffset']=row.get('byteOffset',0)+start;out['bufferViews'].append(row)
        for original in doc['accessors']:
            require('sparse' not in original,'Sparse source accessor unsupported')
            row=copy.deepcopy(original);row['bufferView']+=offsets['bufferViews'];out['accessors'].append(row)
        out['materials'].extend(copy.deepcopy(doc['materials']))
        for original in doc['meshes']:
            row=copy.deepcopy(original)
            for primitive in row['primitives']:
                require(set(primitive)<= {'attributes','indices','material','mode'},'Unsupported source primitive')
                primitive['attributes']={k:v+offsets['accessors'] for k,v in primitive['attributes'].items()}
                if 'indices' in primitive:primitive['indices']+=offsets['accessors']
                if 'material' in primitive:primitive['material']+=offsets['materials']
            out['meshes'].append(row)
        for original in doc['nodes']:
            row=copy.deepcopy(original)
            if 'mesh' in row:row['mesh']+=offsets['meshes']
            if 'children' in row:row['children']=[x+offsets['nodes'] for x in row['children']]
            out['nodes'].append(row)
        out['scenes'][0]['nodes'].extend(x+offsets['nodes'] for x in doc['scenes'][0]['nodes'])
    out['buffers']=[{'byteLength':len(payload)}]
    return encode(out,bytes(payload))


def validate(sources,candidate):
    """Recover each original JSON array and complete BIN chunk independently."""
    doc,payload=decode(candidate)
    require(set(doc)==KEYS and doc['scene']==0 and len(doc['scenes'])==1,'Candidate schema drift')
    offsets={k:0 for k in ('nodes','meshes','accessors','bufferViews','materials')};start=0;roots=[];rows=[]
    for source in sources:
        original=source['document'];part=source['payload']
        require(payload[start:start+len(part)]==part,'Source BIN changed')
        for category in offsets:
            recovered=copy.deepcopy(doc[category][offsets[category]:offsets[category]+len(original[category])])
            for index,row in enumerate(recovered):
                if category=='bufferViews':
                    row['byteOffset']=row.get('byteOffset',0)-start
                    if 'byteOffset' not in original[category][index] and row['byteOffset']==0:del row['byteOffset']
                elif category=='accessors':row['bufferView']-=offsets['bufferViews']
                elif category=='meshes':
                    for primitive in row['primitives']:
                        primitive['attributes']={k:v-offsets['accessors'] for k,v in primitive['attributes'].items()}
                        if 'indices' in primitive:primitive['indices']-=offsets['accessors']
                        if 'material' in primitive:primitive['material']-=offsets['materials']
                elif category=='nodes':
                    if 'mesh' in row:row['mesh']-=offsets['meshes']
                    if 'children' in row:row['children']=[x-offsets['nodes'] for x in row['children']]
            require(recovered==original[category],'Source '+category+' changed')
        roots.extend(x+offsets['nodes'] for x in original['scenes'][0]['nodes'])
        rows.append({'file':source['file'],'sha256':source['sha256'],'binSha256':sha(part),'binOffset':start,
                     'sourceArraysRecoveredExactly':True,'sourceBinPreservedExactly':True})
        start=(start+len(part)+3)//4*4
        for key in offsets:offsets[key]+=len(original[key])
    require(all(len(doc[k])==n for k,n in offsets.items()),'Candidate inventory differs')
    require(doc['scenes'][0]['nodes']==roots,'Source root hierarchy changed')
    require(len(payload)==start and doc['buffers']==[{'byteLength':start}],'Candidate buffer extent differs')
    require('animations' not in doc and 'skins' not in doc,'Unexpected animation/rig')
    return {'sources':rows,'meshes':len(doc['meshes']),'nodes':len(doc['nodes']),'materials':len(doc['materials']),
            'sourceRoots':roots,'sourceNames':[n['name'] for n in doc['nodes']],
            'preserved':'All source node graphs/extras/transforms, materials, mesh/accessor/view arrays recovered exactly after index rebasing; all source BIN bytes exact.',
            'noAnimationTransferred':True}


def run(root,output):
    require(not output.exists(),'Output already exists')
    manifest,sources=read_sources(root)
    data=combine(sources);checks=validate(sources,data)
    require(checks['meshes']==10 and checks['nodes']==12,'Unexpected native node inventory')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
    reread=output.read_bytes();require(reread==data,'Export reload differs')
    validate(sources,reread)
    result={'artifact':{'file':output.name,'bytes':len(data),'sha256':sha(data)},'sourceCommit':manifest['commit'],
            'sourceManifestSha256':sha((root/MANIFEST).read_bytes()),'checks':checks}
    output.with_suffix('.build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.root,args.output),indent=2))
