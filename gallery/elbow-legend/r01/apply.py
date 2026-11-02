import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BINDING=json.loads((HERE/'binding.json').read_text())
def digest(raw):return hashlib.sha256(raw).hexdigest()
def apply(directory):
 target=Path(directory)
 for name,expected in BINDING['inputs'].items():
  if digest((target/name).read_bytes())!=expected:raise ValueError('Exact preserved input required: '+name)
 payload={name:(HERE/name).read_bytes() for name in BINDING['outputs']}
 for name,expected in BINDING['outputs'].items():
  if digest(payload[name])!=expected:raise ValueError('Reviewed correction mismatch: '+name)
 for name,raw in payload.items():(target/name).write_bytes(raw)
 return {name:digest(raw) for name,raw in payload.items()}
if __name__=='__main__':
 import sys
 print(json.dumps(apply(sys.argv[1]),indent=2))
