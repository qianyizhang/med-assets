#!/usr/bin/env python3
"""Blender 4.3.2 required; baseline supplied from canonical repository. No network."""
import argparse,hashlib,json,pathlib,subprocess
D=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--blender',default='blender');p.add_argument('--render',action='store_true');a=p.parse_args();O=pathlib.Path(a.output).resolve()
for name,h in json.loads((D/'dependency-hashes.json').read_text()).items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h,name
assert hashlib.sha256(pathlib.Path(a.baseline).read_bytes()).hexdigest()=='2d2d4e269995f11179cfa423a302f144d9d163883ccde0995a2987e83dd2e898'
if O.exists():raise FileExistsError('Use a new, nonexistent output directory')
O.mkdir(parents=True,exist_ok=False)
def run(script,args):subprocess.run([a.blender,'-b','--disable-autoexec','--python-exit-code','1','-t','2','--python',str(D/script),'--']+args,check=True)
run('trim_recipe.py',['--baseline',str(pathlib.Path(a.baseline).resolve()),'--output',str(O/'recipe-trim-input')])
run('screen_contacts.py',['--input',str(O/'recipe-trim-input/recipe_trimmed_routes.glb'),'--output',str(O/'trim-contact-audit.json')])
run('repair_junctions.py',['--work',str(O)]+([] if a.render else ['--skip-renders']))
f=O/'result/bronchial_whole_junction_experiment.glb';actual=hashlib.sha256(f.read_bytes()).hexdigest();expected='3408ca8e8f394dd268b1dbeafdc59fdc8cc104c0976628e455dbc070ae0a7993';receipt={'expected_sha256':expected,'actual_sha256':actual,'byte_identical':actual==expected,'render_requested':a.render,'scope':'Rebuild identity, not anatomical or browser validation'};(O/'replay-receipt.json').write_text(json.dumps(receipt,indent=2));assert actual==expected,receipt
