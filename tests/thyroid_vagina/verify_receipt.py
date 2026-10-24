#!/usr/bin/env python3
"""Offline receipt verification. Default checks text manifest closure; --strict reads media bytes."""
from pathlib import Path,PurePosixPath
import json,hashlib,struct,argparse
p=argparse.ArgumentParser();p.add_argument('--strict',action='store_true');args=p.parse_args()
R=Path(__file__).resolve().parents[2];M=json.loads((R/'tests/thyroid_vagina/receipt-manifest.json').read_text());media={};n=0

def check(ref,read=True):
 q=PurePosixPath(ref['file']);assert not q.is_absolute() and '..' not in q.parts
 assert len(ref['sha256'])==64 and ref['bytes']>0
 if read:
  b=(R/q).read_bytes();assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256'],str(q);return b
for ref in M['records']:
 r=json.loads(check(ref));assert r['migrationOnly'] and r['newStudyCount']==0 and not r['clinicalValidation'] and not r['defaultWholeBodyReplacement']
 a=r['artifact'];check(a,False);media[a['sha256']]=a;n+=1
 for sr in r['sourceRecords']:
  s=json.loads(check(sr));assert s['externalDependency'] and not s['automaticallyDownloaded'] and not s['rawIncluded'];assert s['license']=='CC-BY-4.0'
 for t in r['textRecords']:check(t)
 for e in r['evidence']:
  check(e,False);media[e['sha256']]=e;assert e['sha256']!=e['originalPNG']['sha256'] and not e['originalPNG']['included']
  if e['selectionRole']=='before':assert e['assetBinding']!=a['sha256']
  else:assert e['assetBinding']==a['sha256']
 if args.strict:
  b=check(a);assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
  length,typ=struct.unpack_from('<II',b,12);assert typ==0x4e4f534a;g=json.loads(b[20:20+length]);assert not g.get('animations');assert not any('uri' in x for key in ['images','buffers'] for x in g.get(key,[]))
  if r['variantId']=='vagina_hra__context-r02':assert len(g['meshes'])==23
  for e in r['evidence']:
   b=check(e);assert b[:4]==b'RIFF' and b[8:12]==b'WEBP'
assert n==M['expectedModels']==2 and len(media)==8
print('PASS', 'strict local media bytes + manifest closure' if args.strict else 'manifest-only text/hash/path closure; media not read', '| 2 existing studies, 6 selected WebPs. No source fetch, reconstruction or fresh anatomy/runtime pass.')
