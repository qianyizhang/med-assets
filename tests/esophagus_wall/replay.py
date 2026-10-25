#!/usr/bin/env python3
"""Portable new-output-only build/render/label replay. Never edits existing delivery files."""
import argparse,pathlib,subprocess,sys,shutil,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--params');p.add_argument('--blender',default='blender');a=p.parse_args();S=pathlib.Path(__file__).resolve().parent;O=pathlib.Path(a.output).resolve()
if O.exists():raise SystemExit('Refusing existing output directory: '+str(O))
O.mkdir(parents=True)
params=pathlib.Path(a.params).resolve() if a.params else S/'parameters.json'
def run(args):subprocess.run(args,check=True)
run([a.blender,'-b','--disable-autoexec','--python-exit-code','1','-t','4','--python',str(S/'build_wall.py'),'--','--params',str(params),'--output',str(O/'model')])
run([a.blender,'-b','--disable-autoexec','--python-exit-code','1','-t','4','--python',str(S/'render_wall.py'),'--','--input',str(O/'model/esophagus-wall-cutaway-r01.glb'),'--output',str(O/'renders')])
for lang,script in [('en','label_sheet.py'),('zh-CN','label_sheet_zh.py')]:run([sys.executable,str(S/script),'--input',str(O/'renders'),'--output',str(O/lang)])
h=hashlib.sha256((O/'model/esophagus-wall-cutaway-r01.glb').read_bytes()).hexdigest();(O/'replay-result.json').write_text(json.dumps({'sha256':h,'default_parameters':a.params is None,'matches_reviewed_default_glb':h=='e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5','scope':'illustrative teaching geometry only; not anatomical or runtime certification'},indent=2));print('Replay complete:',O)
