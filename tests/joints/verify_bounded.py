"""Local identity checks only; no downloads, rendering or anatomy pass."""
import argparse
from pathlib import Path
import hashlib,json
argparse.ArgumentParser(description=__doc__).parse_args()
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=json.loads((R/'reviews/joints/2026-10-24-bounded-migration/FILE-HASHES.json').read_text())
for name,rec in checks.items():
 p=R/name
 assert p.is_file() and p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256'],name
m=json.loads((R/'reviews/joints/2026-10-24-bounded-migration/transport-manifest.json').read_text());seen={}
for study in m['studies']:
 t=study['transport'];p=R/study['canonicalPath'];assert sha(p)==t['decodedSha256'] and p.stat().st_size==t['decodedBytes'];seen[sha(p)]=p.stat().st_size
 for e in study['evidence']:
  p=R/e['path'];assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes'];seen[sha(p)]=p.stat().st_size
assert len(seen)==m['uniqueMediaOids'] and sum(seen.values())==m['uniqueMediaBytes']
print(json.dumps({'identityChecks':'passed','files':len(checks),'uniqueMediaOids':len(seen),'uniqueMediaBytes':sum(seen.values()),'scope':'Local stored byte identity only; no remote, rendering, clinical or reconstruction validation'}))
