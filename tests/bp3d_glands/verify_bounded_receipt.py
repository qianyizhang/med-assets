#!/usr/bin/env python3
"""Offline exact storage checks only; no reconstruction/anatomy/runtime verdict."""
import pathlib,json,hashlib,struct
R=pathlib.Path(__file__).resolve().parents[2];models=0;images={}
for p in sorted((R/'reviews').glob('*/2026-10-23-bp3d-bounded-migration/bounded-record.json')):
 r=json.loads(p.read_text());a=r['artifact'];b=(R/a['file']).read_bytes();assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256'];assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
 n,k=struct.unpack_from('<II',b,12);assert k==0x4e4f534a;j=json.loads(b[20:20+n]);assert not j.get('animations');assert not any('uri' in x for key in ['buffers','images'] for x in j.get(key,[]));assert r['migrationOnly'] and r['newStudyCount']==0;models+=1
 for e in r['evidence']:
  b=(R/e['file']).read_bytes();assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'];assert b[:4]==b'RIFF' and b[8:12]==b'WEBP';images[e['sha256']]=len(b)
 s=json.loads((R/r['externalSourceRecord']).read_text());assert s['externalDependency'] and not s['automaticallyDownloaded'];assert len(s['members'])==13 and sum(x['bytes'] for x in s['members'])==2089656
 for x in r['sourceRecords']:
  assert any(m['id']==x['file_id'] and m['sha256']==x['source_sha256'] for m in s['members'])
assert models==4 and len(images)==11
print('PASS 4 exact stored GLBs, 11 display derivatives, 13 external member bindings. No fresh source reconstruction, topology, anatomy or runtime validation.')
