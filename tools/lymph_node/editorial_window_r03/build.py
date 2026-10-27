"""Refined editorial window: clip original triangles; interpolate attributes only."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
from gltf_source import SOURCE_SHA, EDITED, load, accessor, write_glb, world_blender, dot

def clip(poly,axis,threshold,keep_less):
    """Sutherland-Hodgman on source-triangle barycentric coordinates."""
    if not poly:
        return []
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp=dot(p['world'],axis)-threshold
        dq=dot(q['world'],axis)-threshold
        pi=dp<=0 if keep_less else dp>=0
        qi=dq<=0 if keep_less else dq>=0
        if pi:
            out.append(p)
        if pi!=qi:
            t=dp/(dp-dq)
            out.append({'weights':tuple((1-t)*x+t*y for x,y in zip(p['weights'],q['weights'])),
                'world':tuple((1-t)*x+t*y for x,y in zip(p['world'],q['world']))})
    return out

def append_accessor(doc,binary,values,kind,component):
    dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[kind]
    fmt={5125:'I',5126:'f'}[component]
    packed=bytearray()
    for row in values:
        packed.extend(struct.pack('<'+fmt*dims,*row))
    binary.extend(b'\0'*((-len(binary))%4))
    start=len(binary);binary.extend(packed)
    bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(packed),'target':34963 if kind=='SCALAR' else 34962})
    ai=len(doc['accessors']);doc['accessors'].append({'bufferView':bv,'componentType':component,'count':len(values),'type':kind,
        'min':[min(v[i] for v in values) for i in range(dims)],'max':[max(v[i] for v in values) for i in range(dims)]})
    return ai

def build(source,output):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError('Pinned source mismatch')
    output.mkdir(parents=True,exist_ok=False)
    sd,sb=load(source);doc=copy.deepcopy(sd);binary=bytearray(sb)
    positions=[]
    for m in sd['meshes']:
        positions.extend(world_blender(p) for p in accessor(sd,sb,m['primitives'][0]['attributes']['POSITION']))
    center=tuple((min(v[i] for v in positions)+max(v[i] for v in positions))/2 for i in range(3))
    front=(1/math.sqrt(5.25),-2/math.sqrt(5.25),.5/math.sqrt(5.25))
    right=(2/math.sqrt(5),1/math.sqrt(5),0)
    # Exact r02 display planes extended to source vascular network; back and peripheral source surfaces remain.
    rcut=dot(center,right)-.0008;fcut=dot(center,front)-.0008
    changed=[]; max_bary_error=0; source_surface_ids={}; omitted=[]
    for mesh_index,mesh in enumerate(doc['meshes']):
        if mesh['name'] not in EDITED:
            continue
        p=mesh['primitives'][0]
        if any(sd['accessors'][v]['componentType']!=5126 for v in p['attributes'].values()):
            raise ValueError('Unexpected non-float source attribute')
        attrs={k:accessor(sd,sb,v) for k,v in p['attributes'].items()}
        ind=[x[0] for x in accessor(sd,sb,p['indices'])]
        # Original positions/attributes remain exact. New vertices are only plane-edge intersections.
        newattrs=copy.deepcopy(attrs);newind=[];provenance=[]
        raw_kept=0;split=0;removed=0
        for i in range(0,len(ind),3):
            tri=ind[i:i+3]
            poly=[{'world':world_blender(attrs['POSITION'][v]),'weights':tuple(float(j==k) for k in range(3))} for j,v in enumerate(tri)]
            # Union without overlapping interior: left piece + camera-right back piece.
            left=clip(poly,right,rcut,True)
            back=clip(clip(poly,right,rcut,False),front,fcut,True)
            pieces=[x for x in (left,back) if len(x)>=3]
            generated=0
            for piece in pieces:
                for j in range(1,len(piece)-1):
                    outtri=[piece[0],piece[j],piece[j+1]]
                    world=[v['world'] for v in outtri]
                    ab=tuple(world[1][k]-world[0][k] for k in range(3));ac=tuple(world[2][k]-world[0][k] for k in range(3))
                    cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
                    if sum(x*x for x in cross)<1e-40:
                        continue
                    face=[]
                    for v in outtri:
                        w=v['weights'];max_bary_error=max(max_bary_error,abs(sum(w)-1),max(0,-min(w)))
                        exact=next((k for k in range(3) if w[k]==1 and sum(w)==1),None)
                        if exact is not None:
                            face.append(tri[exact]);continue
                        idx=len(newattrs['POSITION']);face.append(idx)
                        for name,array in attrs.items():
                            values=tuple(sum(w[k]*array[tri[k]][j] for k in range(3)) for j in range(len(array[0])))
                            if name=='NORMAL':
                                norm=math.sqrt(sum(x*x for x in values));values=tuple(x/norm for x in values)
                            newattrs[name].append(values)
                    # Validate the actual serialized float32 coordinates, not only the
                    # double-precision construction. Preserve appended attributes, so
                    # this repair changes only precision-invalid face indices/map rows.
                    quantized=[struct.unpack('<fff',struct.pack('<fff',*newattrs['POSITION'][k])) for k in face]
                    qab=tuple(quantized[1][k]-quantized[0][k] for k in range(3))
                    qac=tuple(quantized[2][k]-quantized[0][k] for k in range(3))
                    qcross=(qab[1]*qac[2]-qab[2]*qac[1],qab[2]*qac[0]-qab[0]*qac[2],qab[0]*qac[1]-qab[1]*qac[0])
                    source_positions=[attrs['POSITION'][k] for k in tri]
                    sab=tuple(source_positions[1][k]-source_positions[0][k] for k in range(3))
                    sac=tuple(source_positions[2][k]-source_positions[0][k] for k in range(3))
                    scross=(sab[1]*sac[2]-sab[2]*sac[1],sab[2]*sac[0]-sab[0]*sac[2],sab[0]*sac[1]-sab[1]*sac[0])
                    orientation_dot=dot(qcross,scross)
                    if orientation_dot<=0:
                        local=[newattrs['POSITION'][k] for k in face]
                        lab=tuple(local[1][k]-local[0][k] for k in range(3))
                        lac=tuple(local[2][k]-local[0][k] for k in range(3))
                        lcross=(lab[1]*lac[2]-lab[2]*lac[1],lab[2]*lac[0]-lab[0]*lac[2],lab[0]*lac[1]-lab[1]*lac[0])
                        omitted.append({'mesh':mesh['name'],'sourceTriangle':i//3,
                            'preQuantizationWorldAreaSquareMetres':math.sqrt(sum(x*x for x in cross))/2,
                            'preQuantizationLocalAreaSquareMetres':math.sqrt(sum(x*x for x in lcross))/2,
                            'serializedAreaSquareMetres':math.sqrt(sum(x*x for x in qcross))/2,'indices':face,
                            'serializedSourceNormalDot':orientation_dot,
                            'preQuantizationLocalPositions':local,'serializedPositions':quantized,
                            'reason':'Exactly zero area after float32 serialization' if not any(qcross) else 'Nonpositive source orientation after float32 serialization'})
                        continue
                    newind.extend(face);provenance.append(i//3);generated+=1
            if not generated:removed+=1
            elif generated==1 and len(pieces)==1 and all(v in tri for v in newind[-3:]):raw_kept+=1
            else:split+=1
        for name,values in newattrs.items():
            kind=sd['accessors'][p['attributes'][name]]['type']
            p['attributes'][name]=append_accessor(doc,binary,values,kind,5126)
        p['indices']=append_accessor(doc,binary,[(v,) for v in newind],'SCALAR',5125)
        source_surface_ids[mesh['name']]=provenance
        changed.append({'node':mesh['name'],'rawSourceTriangles':len(ind)//3,'outputTriangles':len(newind)//3,
            'sourceTrianglesRetainedWhole':raw_kept,'sourceTrianglesClipped':split,'sourceTrianglesRemoved':removed,
            'addedInterpolatedVertices':len(newattrs['POSITION'])-len(attrs['POSITION'])})
    doc['buffers'][0]['byteLength']=len(binary)
    doc.setdefault('extras',{})['editorialPresentation']={
        'status':'local-unapproved-candidate','sourceSha256':SOURCE_SHA,'operation':'planar surface clipping of capsule, medulla and front source vascular network; no caps',
        'geometry':'Four source meshes unchanged. Edited surfaces retain original coordinates or barycentric points on original source triangles. No tissue surfaces added.',
        'networkDisplayLabel':'Source vascular network (identity unresolved)',
        'scope':'Editorial omission also affects front vascular network. Editorial display window; not a specimen section, histological boundary or clinical plane. Original source defects and vascular label conflict remain.',
        'sourceAttribution':'Kristen Browne; Heidi Schlehlein. HRA Male Lymph Node v1.2. DOI 10.48539/HBM299.VVXH.634; CC BY 4.0; modified for display, no endorsement.'}
    path=output/'lymph-node-editorial-window-r03.glb';write_glb(path,doc,bytes(binary))
    (output/'triangle-source-map.json').write_text(json.dumps(source_surface_ids,separators=(',',':'))+'\n')
    receipt={'source':str(source.resolve()),'sourceSha256':SOURCE_SHA,'candidate':str(path.resolve()),'candidateSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'candidateBytes':path.stat().st_size,'editedSurfaces':changed,'untouchedMeshes':4,'sourceBinaryPrefixUnchanged':True,'newAnatomicalSurfaces':0,'cappedCutFaces':0,
        'maxBarycentricWeightError':max_bary_error,
        'float32InvalidFragmentsOmitted':omitted,
        'omittedPreQuantizationAreaSquareMetres':sum(x['preQuantizationLocalAreaSquareMetres'] for x in omitted),
        'window':{'centerBlender':center,'cameraFront':front,'cameraRight':right,'rightThresholdMetres':-.0008,'frontThresholdMetres':-.0008,
            'selection':'exact planar clipping, no cap surfaces'},
        'limits':['Open editorial surfaces, not watertight','No anatomy/clinical acceptance','Unresolved source vascular identity','Original native topology defects remain']}
    (output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.source,a.output)
