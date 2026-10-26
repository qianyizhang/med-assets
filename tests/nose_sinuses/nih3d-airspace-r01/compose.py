from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--renders',required=True);p.add_argument('--out',required=True);a=p.parse_args();R=Path(a.renders);O=Path(a.out)
rows=json.loads((R/'bindings.json').read_text())
for r in rows:
 if hashlib.sha256((R/r['file']).read_bytes()).hexdigest()!=r['png_sha256']:raise ValueError('Render hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True);im=Image.new('RGB',(1600,950),'#171d20');d=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(font,24);s=ImageFont.truetype(font,20)
for i,(fn,title) in enumerate([('baseline-oblique.png','Existing authored schematic (still Needs revision)'),('candidate-oblique.png','NIH3D CT airspace cast — separate source candidate')]):
 q=Image.open(R/fn).convert('RGB');q.thumbnail((760,760));im.paste(q,(20+i*800,65));d.text((20+i*800,22),title,font=f,fill='#eeeeee')
for y,text,color in [(842,'Different models / independent fit scales. No anatomical registration or tissue equivalence.','#d5dbe0'),(875,'Cast = filled AIRSPACE, not mucosa/conchae. Disclosed cyst indentation; detected intersections retained.','#e3bd7e'),(908,'NIH3D 3DPX-002305 · nevitdilmen · CC BY4.0. Physical units and anatomical axes undocumented.','#b9c3ca')]:d.text((25,y),text,font=s,fill=color)
im.save(O/'baseline-source-comparison.png');bindings=[]
for fn in ['candidate-minusY.png','candidate-plusY.png','candidate-plusX.png','candidate-oblique.png']:
 q=Image.open(R/fn);dest=O/(Path(fn).stem+'.webp');q.save(dest,lossless=True);assert list(q.convert('RGBA').getdata())==list(Image.open(dest).convert('RGBA').getdata());bindings.append({'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'decoded_pixels_exact_to_png_sha256':hashlib.sha256((R/fn).read_bytes()).hexdigest()})
(O/'media-bindings.json').write_text(json.dumps({'native':bindings,'comparison':'Side-by-side resized panels from exact baseline/candidate GLB renders; annotations are not anatomy labels.','comparison_sha256':hashlib.sha256((O/'baseline-source-comparison.png').read_bytes()).hexdigest()},indent=2))
