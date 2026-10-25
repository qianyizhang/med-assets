#!/usr/bin/env python3
"""Render outlined SVGs with no font files or network. Requires Inkscape1.4 + Pillow."""
import argparse,pathlib,json,hashlib,subprocess
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--inkscape',default='inkscape');a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[2];rows=json.loads((root/'reviews/biliary_pathway/2026-10-25-r01/evidence-bindings.json').read_text());out=pathlib.Path(a.output)
for row in rows:assert hashlib.sha256((root/row['svg_path']).read_bytes()).hexdigest()==row['svg_sha256']
if out.exists():raise FileExistsError('Output must not already exist')
out.mkdir(parents=True);result=[]
for row in rows:
 dest=out/(row['language']+'.png');subprocess.run([a.inkscape,str(root/row['svg_path']),'-o',str(dest)],check=True);im=Image.open(dest).convert('RGBA');actual=hashlib.sha256(im.tobytes()).hexdigest();assert actual==row['decoded_rgba_sha256'];result.append({'language':row['language'],'decoded_rgba_sha256':actual,'matches_frozen_preview':True})
(out/'receipt.json').write_text(json.dumps({'renderer':'Inkscape','font_files_required':False,'results':result,'scope':'Raster rendering reproduction, not anatomical or browser validation'},indent=2))
