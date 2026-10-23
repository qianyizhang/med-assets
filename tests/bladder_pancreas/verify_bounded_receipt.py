#!/usr/bin/env python3
"""Offline exact payload/source-audit binding; not anatomy or runtime approval."""
import json,hashlib,pathlib,struct
R=pathlib.Path(__file__).resolve().parents[2]
count=0
for aid,rev in [('bladder','hra-female-context-r03'),('pancreas','hra-female-context-r04')]:
 record=json.loads((R/'reviews'/aid/rev/'bounded-record.json').read_text());a=record['artifact'];p=R/a['file'];b=p.read_bytes()
 assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
 assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
 jlen,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a;j=json.loads(b[20:20+jlen]);assert not j.get('animations')
 assert not any('uri' in x for k in ['buffers','images'] for x in j.get(k,[]))
 for e in record['evidence']:
  x=(R/e['file']).read_bytes();assert len(x)==e['bytes'] and hashlib.sha256(x).hexdigest()==e['sha256'];assert x[:4]==b'RIFF' and x[8:12]==b'WEBP';count+=1
 for k in ['sourceRoleKey','cameraRecipe']:
  x=(R/record[k]['file']).read_bytes();assert hashlib.sha256(x).hexdigest()==record[k]['sha256']
 audit=json.loads((R/'models'/aid/'provenance'/rev/'final-independent-source-audit.json').read_text());assert audit['sha256']==a['sha256'];assert audit['all_position_index_other_nonnormal_attributes_source_byte_identical'];assert audit['all_source_node_transform_fields_identical'];assert audit['all_selected_mesh_ancestor_chains_identical']
 assert record['gates']['anatomy']['status']=='unreviewed' and record['gates']['runtime']['status']=='unverified';assert record['newStudyCount']==0
assert count==6
print('PASS: two exact GLBs, six WebP derivatives, role/camera bindings and retained source-audit assertions. No fresh source reconstruction, anatomy or runtime claim.')
