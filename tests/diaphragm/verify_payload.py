from pathlib import Path
import hashlib,json
from PIL import Image
r=Path(__file__).resolve().parents[2]
m=json.loads((r/'reviews/diaphragm/2026-10-24-z-static-study/PAYLOAD-HASHES.json').read_text())
for n,v in m.items():
 p=r/n
 assert p.stat().st_size==v['bytes'],n
 assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],n
 if p.suffix=='.png':assert not Image.open(p).info,n
print(f"Verified {len(m)} payload files; no medical/runtime/rebuild claim")
