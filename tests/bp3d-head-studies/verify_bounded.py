"""Read-only local manifest-subset identity checks, not source rebuild/render validation."""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
G='reviews/bp3d-head-studies/2026-10-24-bounded-migration'
S='sources/datasets/bp3d-4.0-head-studies'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=json.loads((R/G/'FILE-HASHES.json').read_text())
for name,rec in checks.items():
 p=R/name
 assert p.is_file() and p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256'],name
m=json.loads((R/G/'transport-manifest.json').read_text());src=json.loads((R/S/'external-source-map.json').read_text());seen={};ev=set()
for s in m['studies']:
 p=R/s['canonicalPath'];t=s['transport'];raw=p.read_bytes();assert sha(p)==t['decodedSha256'] and len(raw)==t['decodedBytes'];assert raw[:4]==b'glTF'
 n,k=struct.unpack('<II',raw[12:20]);g=json.loads(raw[20:20+n]);r=json.loads((R/s['reviewRecord']).read_text());assert len(r['componentIdentityMap'])==r['componentCount'];seen[sha(p)]=len(raw)
 for c in r['componentIdentityMap']:
  ex=g['nodes'][c['nodeIndex']]['extras'];assert ex['source_sha256']==c['sourceSha256']==src['members'][c['sourceFileId']]['sha256']
 for e in s['evidence']:
  p=R/e['path'];raw=p.read_bytes();assert sha(p)==e['sha256'] and len(raw)==e['bytes'];
  if e['format']=='WEBP':
   assert raw[:4]==b'RIFF' and raw[8:12]==b'WEBP';assert e['sha256']!=e['originalPngSha256']
  elif e['format']=='PNG':
   assert raw[:8]==b'\x89PNG\r\n\x1a\n';a=json.loads((R/e['additiveRecord']).read_text());assert a['sourceSha256']==e['sourceSha256']==t['decodedSha256'];assert any(x['sha256']==e['sha256'] and x['sourceSha256']==e['sourceSha256'] for x in a['evidence'])
   for linked in a['sourceRecords']+a['evidence']:
    lp=R/linked['file'];assert lp.is_file() and sha(lp)==linked['sha256'],linked['file']
  else:raise AssertionError('Unsupported image format')
  seen[sha(p)]=len(raw);ev.add(sha(p))
assert len(seen)==m['uniqueMediaOids'] and sum(seen.values())==m['uniqueMediaBytes'] and len(ev)==m['uniqueSelectedEvidence']
if '--strict-package' in sys.argv:
 assert set(checks)=={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and str(p.relative_to(R))!=G+'/FILE-HASHES.json'},'Unlisted or stale package files'
print(json.dumps({'identityChecks':'passed','files':len(checks),'uniqueMediaBytes':sum(seen.values()),'status':m['status'],'scope':'Local retained bytes only; external gzip/source archives not re-fetched; no source rebuild,rendering,anatomy or runtime pass'}))
