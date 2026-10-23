"""Read-only exact receipt integrity; no anatomical/runtime certification."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
r=json.loads((R/'reviews/draft_muscle/2026-10-23-achilles-context/record.json').read_text())
assert r['newAcceptedCandidateCount']==0 and not r['originalGatesChanged']
for e in r['files']:
 p=(R/e['file']).resolve();assert p.is_relative_to(R.resolve());b=p.read_bytes();assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
print('24 exact payloads verified; limited static supplement only.')
