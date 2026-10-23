import pathlib,hashlib
D=pathlib.Path(__file__).resolve().parents[1]
EXPECTED='95f0c3d2f918582608692ca1139e8bdb18c147a16470e9ee9af8b276bd77c422'
def shared_atlas():
 p=D/'sources/shared-united-female.glb'
 if not p.is_file():raise FileNotFoundError('Supply the explicit external atlas through replay.py --source; no automatic download.')
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 if h.hexdigest()!=EXPECTED:raise ValueError('External source SHA mismatch')
 return p
