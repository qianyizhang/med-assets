"""Locally authored data-only GLB subsetter; preserves raw accessor bytes and hierarchy."""
import pathlib, json, struct, hashlib, copy
D=pathlib.Path(__file__).resolve().parents[1]
from resolve_shared_source import shared_atlas
S=shared_atlas()
raw=S.read_bytes(); jl,jt=struct.unpack_from('<II',raw,12); assert jt==0x4e4f534a
j=json.loads(raw[20:20+jl]); bl,bt=struct.unpack_from('<II',raw,20+jl); assert bt==0x004e4942
binary=raw[28+jl:28+jl+bl]
assert not any(j.get(k) for k in ['images','textures','animations','skins','extensionsUsed'])
assert not any('sparse' in a for a in j['accessors'])
parents={c:i for i,n in enumerate(j['nodes']) for c in n.get('children',[])}
def sha(b): return hashlib.sha256(b).hexdigest()
def write_glb(path,g,b):
    g['buffers']=[{'byteLength':len(b)}]
    jb=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();jb+=b' '*((-len(jb))%4);b+=b'\0'*((-len(b))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(jb)+len(b))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(b),0x004e4942)+b)
def subset(id,roots):
    selected=set()
    def walk(i):
        selected.add(i)
        for c in j['nodes'][i].get('children',[]):walk(c)
    for name in roots:walk(next(i for i,n in enumerate(j['nodes']) if n.get('name')==name))
    mesh_nodes=selected.copy()
    for i in list(selected):
        while i in parents:i=parents[i];selected.add(i)
    ns=sorted(selected); nmap={v:i for i,v in enumerate(ns)}
    ms=sorted({j['nodes'][i]['mesh'] for i in mesh_nodes if 'mesh' in j['nodes'][i]}); mmap={v:i for i,v in enumerate(ms)}
    aset=set(); matset=set()
    for i in ms:
        for p in j['meshes'][i]['primitives']:
            aset.update(p['attributes'].values())
            if 'indices' in p:aset.add(p['indices'])
            if 'material' in p:matset.add(p['material'])
            assert not p.get('targets') and not p.get('extensions')
    aa=sorted(aset); amap={v:i for i,v in enumerate(aa)}; mats=sorted(matset); matmap={v:i for i,v in enumerate(mats)}
    g={'asset':copy.deepcopy(j['asset']),'scene':0,'scenes':[{'nodes':[nmap[i] for i in ns if i not in parents]}], 'nodes':[], 'meshes':[], 'accessors':[],'bufferViews':[],'materials':[copy.deepcopy(j['materials'][i]) for i in mats]}
    for i in ns:
        n=copy.deepcopy(j['nodes'][i]);
        if 'children' in n:n['children']=[nmap[c] for c in n['children'] if c in nmap]
        if 'mesh' in n:
            if i in mesh_nodes:n['mesh']=mmap[n['mesh']]
            else:del n['mesh']
        g['nodes'].append(n)
    for i in ms:
        m=copy.deepcopy(j['meshes'][i])
        for p in m['primitives']:
            p['attributes']={k:amap[v] for k,v in p['attributes'].items()}
            if 'indices' in p:p['indices']=amap[p['indices']]
            if 'material' in p:p['material']=matmap[p['material']]
        g['meshes'].append(m)
    out=bytearray(); checks=[]
    for i in aa:
        a=copy.deepcopy(j['accessors'][i]);v=j['bufferViews'][a['bufferView']]
        size={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a['componentType']]*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}[a['type']]
        stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0);length=(a['count']-1)*stride+size
        buf=binary[start:start+length]; assert len(buf)==length
        out+=b'\0'*((-len(out))%4);nv={'buffer':0,'byteOffset':len(out),'byteLength':length}
        if 'byteStride' in v:nv['byteStride']=stride
        if 'target' in v:nv['target']=v['target']
        a['bufferView']=len(g['bufferViews']);a.pop('byteOffset',None);g['bufferViews'].append(nv);g['accessors'].append(a);out+=buf
        checks.append({'source_accessor':i,'output_accessor':amap[i],'bytes':length,'raw_payload_sha256':sha(buf),'preserved_exactly':True})
    model=D/'models'/id;model.mkdir(parents=True,exist_ok=True);path=model/(id+'.glb');write_glb(path,g,bytes(out))
    report={'id':id,'source_sha256':sha(raw),'file':str(path.relative_to(D)),'sha256':sha(path.read_bytes()),'roots':roots,'selected_mesh_names':[j['nodes'][i]['name'] for i in sorted(mesh_nodes) if 'mesh' in j['nodes'][i]],'retained_ancestor_names':[j['nodes'][i]['name'] for i in ns if i not in mesh_nodes],'nodes_transforms_and_names':'unchanged; index references remapped, unselected children removed','materials':'unchanged native source materials','geometry':'Accessor payload bytes preserved exactly; no resampling, smoothing, welding, normals edit, centering, scale, mirror, or registration','accessor_payload_checks':checks,'approval':'unreviewed source subset; not a pass'}
    (model/'extraction-audit.json').write_text(json.dumps(report,indent=2)); print(id,len(out),report['sha256'])
    return report
if __name__=='__main__':
    reports=[subset(id,roots) for id,roots in [
        ('liver_hra_female_r01',['VH_F_liver']),
        ('spleen_hra_female_r01',['VH_F_spleen']),
        ('pancreas_hra_female_r01',['VH_F_pancreas']),
        ('bladder_hra_female_r01',['VH_F_urinary_bladder']),
        ('pancreas_hra_female_context_r01',['VH_F_pancreas','VH_F_ducts_of_pancreas','VH_F_duodenum','VH_F_spleen']),
        ('bladder_hra_female_context_r01',['VH_F_urinary_bladder','VH_F_right_ureter','VH_F_left_ureter','VH_F_uterus','VH_F_vagina','VH_F_rectum'])
    ]]
    (D/'sources/subset-index.json').write_text(json.dumps(reports,indent=2))
