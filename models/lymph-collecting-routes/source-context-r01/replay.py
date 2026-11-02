"""Source-pinned, new-directory replay. --check-only does not render or write."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
if not __debug__: raise SystemExit('Optimized Python is unsupported')
ROOT=Path(__file__).resolve().parent
SOURCE_SHA='5f7947838971b88f2c29e992290086e21169eee2c72bb5394948e72aee4bad25'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
 subprocess.run([sys.executable,str(ROOT/'verify_package.py')],check=True)
 source=a.source.resolve(strict=True);out=a.output.resolve()
 if out.exists():raise ValueError('Output must not exist')
 if out==ROOT or ROOT in out.parents:raise ValueError('Output must be outside the delivered package')
 data=source.read_bytes()
 if len(data)!=10587644 or hashlib.sha256(data).hexdigest()!=SOURCE_SHA:raise ValueError('Wrong source scene; exact pinned bytes required')
 if a.check_only:print('Source and output preflight passed; no render or write performed');return
 blender=shutil.which('blender')
 if not blender:raise RuntimeError('Blender 4.3.2 is required')
 if not subprocess.check_output([blender,'--version'],text=True).splitlines()[0] == 'Blender 4.3.2':raise RuntimeError('Blender 4.3.2 required')
 import PIL
 for f in ['NotoSansCJK-Regular.ttc','NotoSansCJK-Bold.ttc']:
  if not (Path('/usr/share/fonts/opentype/noto')/f).is_file():raise RuntimeError('Required Noto CJK font missing: '+f)
 out.mkdir(parents=True,exist_ok=False);(out/'source').mkdir();shutil.copyfile(source,out/'source/Network_Systems_Draft.blend')
 for f in ['build.py','plate.py','verify_geometry.py']:shutil.copyfile(ROOT/'recipe'/f,out/f)
 for cmd in [[blender,'-b','-t','4','--python',str(out/'build.py')],[sys.executable,str(out/'plate.py')],[blender,'-b','-t','2','--python',str(out/'verify_geometry.py')]]:subprocess.run(cmd,cwd=out,check=True)
 checks={}
 for name in ['selected-source-routes.glb','comparison-en.png','comparison-zh.png','comparison-en-grayscale.png','comparison-zh-grayscale.png']:
  checks[name]=hashlib.sha256((out/name).read_bytes()).hexdigest()==hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
 (out/'package-replay-result.json').write_text(json.dumps(checks,indent=2)+'\n')
 if not all(checks.values()):raise RuntimeError('Replay bytes differ; preserve output for inspection')
 print('Pinned final bytes match; no clinical or live-runtime approval')
if __name__=='__main__':main()
