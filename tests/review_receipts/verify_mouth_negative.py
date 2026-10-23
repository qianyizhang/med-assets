"""Read-only negative-review packet integrity; no new visual/runtime verdict."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
p=R/'reviews/draft_mouth/2026-10-23-context-rejected/record.json'
r=json.loads(p.read_text());assert r['status']=='needs-revision' and r['newAcceptedCandidateCount']==0 and not r['existingGatesChanged']
assert len(r['artifacts'])==2 and all(not x['payloadIncluded'] for x in r['artifacts'])
for f in r['files']:
 q=(R/f['file']).resolve();assert q.is_relative_to(R.resolve());b=q.read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
for e in r['evidence']:
 b=(R/e['file']).read_bytes();assert b.startswith(b'\x89PNG\r\n\x1a\n') and hashlib.sha256(b).hexdigest()==e['sha256'];assert len(e['artifactBindings'])==2
print('Negative review packet integrity passed; no model promotion or runtime/anatomy claim.')
