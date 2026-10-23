#!/usr/bin/env python3
"""Re-export saved baked source, not the historical procedural generator."""
from pathlib import Path
import argparse,hashlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[2]
s=r/'models/blood_cell_study/source/blood-cell-authored-study-r05-public.blend'
assert hashlib.sha256(s.read_bytes()).hexdigest()=='f3123f0c84444ada60a2c0abe81520b166da4a4be69ba447211c11ada2191ad1'
assert not a.output.exists(),'Refuse to overwrite existing output'
subprocess.run(['blender','--background',str(s),'--threads','1','--python',str(r/'reviews/blood_cell_study/authored-r05/export_baked.py'),'--',str(a.output.resolve())],check=True)
assert hashlib.sha256(a.output.read_bytes()).hexdigest()=='4c7c738b3ca6ae6cc7e44a449be0f7d26d04ceb9975e43d3b834a2caad96618c'
print('Exact baked-source export passed; no procedural regeneration claim.')
