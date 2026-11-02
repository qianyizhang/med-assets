"""Stage a fresh local replay directory; never render or overwrite reviewed work."""
from pathlib import Path
import argparse, hashlib, shutil, subprocess, sys
if not __debug__: raise SystemExit("Optimized Python is unsupported")
a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a=a.parse_args()
s=a.source.resolve();o=a.output.resolve();root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'verify_package.py')],check=True)
if o==root or root in o.parents: raise SystemExit('Output must be outside delivered package')
if o.exists(): raise SystemExit('Output must not exist')
b=s.read_bytes()
if len(b)!=10587644 or hashlib.sha256(b).hexdigest()!='5f7947838971b88f2c29e992290086e21169eee2c72bb5394948e72aee4bad25': raise SystemExit('Source identity mismatch')
o.mkdir(parents=True,exist_ok=False);(o/'source').mkdir()
(o/'source'/'Network_Systems_Draft.blend').write_bytes(b)
for name in ('build.py','plate.py','verify_geometry.py'): shutil.copy2(root/name,o/name)
print('Pinned source and recipes staged. No render or geometry build was run.')
