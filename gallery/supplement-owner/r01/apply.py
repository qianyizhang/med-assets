"""Change only the exact archived supplement link, after all identity checks."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BINDING=json.loads((HERE/'binding.json').read_text())
OLD='candidate.html?asset=${encodeURIComponent(a.id)}&candidate=${encodeURIComponent(c.id)}'
NEW='candidate.html?asset=${encodeURIComponent(c.assetId)}&candidate=${encodeURIComponent(c.id)}'
def digest(raw): return hashlib.sha256(raw).hexdigest()
def apply(directory):
 target=Path(directory)
 raw={name:(target/name).read_bytes() for name in BINDING['inputs']}
 for name,expected in BINDING['inputs'].items():
  if digest(raw[name])!=expected: raise ValueError('Exact preserved input required: '+name)
 source=raw['review.js'].decode()
 if source.count(OLD)!=1: raise ValueError('Unique original archive link required')
 updated=source.replace(OLD,NEW).encode()
 if digest(updated)!=BINDING['output']: raise ValueError('Exact output identity required')
 (target/'review.js').write_bytes(updated)
 return {'review.js':digest(updated)}
if __name__=='__main__':
 import sys
 print(json.dumps(apply(sys.argv[1]),indent=2))
