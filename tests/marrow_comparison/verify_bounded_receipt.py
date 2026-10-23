from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
r=json.loads((R/'reviews/draft_bone/2026-10-23-marrow-comparison/bounded-record.json').read_text())
assert r['newAcceptedCandidateCount']==0 and not r['originalGatesChanged']
for e in r['files']:
 p=(R/e['file']).resolve();assert p.is_relative_to(R.resolve());b=p.read_bytes();assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
print('Exact bounded comparison inputs verified; no anatomy/runtime pass.')
