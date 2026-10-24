from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
G=Path('reviews/muscle/2026-10-24-bounded-migration')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=json.loads((R/G/'FILE-HASHES.json').read_text())
for name,x in h.items():
 p=R/name;assert p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],name
m=json.loads((R/G/'transport-manifest.json').read_text());r=json.loads((R/m['reviewRecord']).read_text());src=json.loads((R/m['sourceMap']).read_text());p=R/m['canonicalPath'];t=m['transport'];b=p.read_bytes();assert len(b)==t['decodedBytes'] and sha(p)==t['decodedSha256'];n=struct.unpack('<I',b[12:16])[0];g=json.loads(b[20:20+n]);assert r['evidence']==m['evidence'];assert r['sourceDependencies']==m['sourceMap']
for node in r['nodeIdentityMap']:
 assert g['nodes'][node['index']]['name']==node['name']
 if node['sourceObjectName'] is not None:assert g['nodes'][node['index']].get('extras',{}).get('source_object_name')==node['sourceObjectName']
selected={x['sourceObjectName'] for x in src['selection']}
if 'sourceCollection' in src:assert {n['sourceObjectName'] for n in r['nodeIdentityMap']}==selected
else:assert {n['name'] for n in r['nodeIdentityMap']}==selected
seen={sha(p):len(b)}
for e in m['evidence']:
 p=R/e['path'];b=p.read_bytes();assert sha(p)==e['sha256'] and len(b)==e['bytes'];assert b[:4]==b'RIFF' and b[8:12]==b'WEBP';assert e['originalPNG']['bundled'] is False and e['originalPNG']['sha256']!=e['sha256'];seen[e['sha256']]=e['bytes']
 if e['selectionRole']=='candidate':assert e['assetBinding']==t['decodedSha256']
for x in src['externalHistoricalRecords']+src['recipeDependencies']+src['licenseReceipts']:assert x['bundled'] is False and len(x['sha256'])==64
assert sum(seen.values())==m['uniqueMediaBytes'] and len(seen)==m['uniqueMediaOids']
if '--strict-package' in sys.argv:assert set(h)=={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and p!=R/G/'FILE-HASHES.json'}
print(json.dumps({'identityChecks':'passed','scope':'Local retained bytes only; no source rebuild or runtime approval','mediaBytes':sum(seen.values()),'status':m['status']}))
