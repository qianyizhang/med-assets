from pathlib import Path
import argparse,shutil,runpy
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert not out.exists(),'New output directory required'
runpy.run_path(str(Path(__file__).with_name('verify_bounded_receipt.py')))
for origin,folder in [(R/'assemblies/marrow-comparison/2026-10-23','models'),(R/'sources/datasets/marrow-comparison-v1','sources'),(Path(__file__).parent/'original_recipes','tools')]:
 (out/folder).mkdir(parents=True,exist_ok=True)
 for f in origin.iterdir():
  if f.is_file() and (folder!='models' or f.suffix=='.glb'):shutil.copy2(f,out/folder/f.name)
(out/'evidence').mkdir();print('Prepared new offline replay workspace; no reconstruction executed.')
