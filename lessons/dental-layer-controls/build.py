"""Build a self-contained offline viewer without duplicating canonical GLB in the repo."""
import argparse,base64,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
EXPECTED='90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7'
def build(source,out,script=None):
 data=Path(source).read_bytes()
 if hashlib.sha256(data).hexdigest()!=EXPECTED:raise ValueError('Expected the exact FDI31 Balanced source bytes, not an LFS pointer or replacement.')
 s=(D/'index.template.html').read_text()
 for key,file in [('CONTROLLER','controller.js'),('RENDERER','renderer.js'),('APP','app.js'),('AUTHORING','authoring.js')]:
  code=(D/file).read_text()
  if '</script' in code.lower():raise ValueError('Unexpected inline script terminator.')
  s=s.replace('/* '+key+' */',code)
 # The runtime validates the complete source-bound script before enabling controls.
 if script is not None:
  import subprocess
  subprocess.run(['node',str(D/'script.cjs'),'check',str(source),str(script)],check=True,capture_output=True,text=True)
 s=s.replace('SCRIPT_BASE64',base64.b64encode(Path(script).read_bytes()).decode() if script is not None else '')
 s=s.replace('BASE64_DATA',base64.b64encode(data).decode())
 Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(s)
 return {'file':Path(out).name,'source_sha256':EXPECTED,'source_bytes':len(data),'html_bytes':Path(out).stat().st_size,'network_dependencies':[],'geometry':'source arrays unchanged; only display matrices and visibility change','validation':'editorial control prototype; no clinical or physiological validation'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--script');a=p.parse_args();print(json.dumps(build(a.source,a.out,a.script),indent=2))
