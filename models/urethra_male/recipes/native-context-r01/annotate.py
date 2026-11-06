from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse
import json,hashlib
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);opts=ap.parse_args();P=opts.work;src=P/'r01/translucent-renders/context-side-source.png';O=P/'r01/annotated-context.png';assert not O.exists();assert hashlib.sha256((P/'r01/context.glb').read_bytes()).hexdigest()=='d2d88c936287f4ea5978aba1f17e86975c587a102e498595dd7a58aa07c269e7'
im=Image.new('RGB',(1600,1440),'#171b20');im.paste(Image.open(src).convert('RGB'),(25,150));d=ImageDraw.Draw(im);font=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
d.text((35,22),'Male urethra · source-context localization study',font=font(33),fill='#eff2f5');d.text((35,70),'男性尿道 · 同源结构位置关系观察',font=font(28),fill='#d0d6dc');d.text((35,113),'Transparent surroundings are a display aid, not physical tissue appearance.',font=font(22),fill='#b7c0c8')
for en,zh,y,target in [('Urinary bladder','膀胱',230,(810,270)),('Prostate','前列腺',430,(925,490)),('Urethral surface','尿道管面',620,(720,579)),('Corpus spongiosum','尿道海绵体',800,(665,625))]:
 tx,ty=target;tx+=25;ty+=150;d.line([(tx,ty),(1145,y+26),(1180,y+26)],fill='#c5d1dc',width=2);d.ellipse((tx-4,ty-4,tx+4,ty+4),fill='#f4d6a3');d.text((1190,y),en,font=font(24),fill='#f0f3f5');d.text((1190,y+37),zh,font=font(25),fill='#cbd3db')
d.text((1188,1010),'Open modeled ends',font=font(23),fill='#e8bc73');d.text((1188,1047),'模型两端开放',font=font(24),fill='#e8bc73');d.text((1188,1090),'≠ verified lumen',font=font(22),fill='#e8bc73');d.text((1188,1127),'≠ 已验证管腔',font=font(23),fill='#e8bc73')
lines=[('Proximal connection and distal protrusion/outlet are unvalidated; no patency or flow claim.','#e8bc73'),('近端连接、远端突出及开口关系未验证；不代表通畅性或生理流动。','#e8bc73'),('Single source surface, not a measured wall. No kidneys or ureters; not the complete urinary tract.','#cbd3db'),('单层来源管面，并非实测管壁；未含肾或输尿管，不是完整泌尿道。','#cbd3db')]
for i,(txt,c) in enumerate(lines):d.text((35,1265+i*38),txt,font=font(23),fill=c)
im.save(O);(P/'r01/annotation-bindings.json').write_text(json.dumps({'source_image':str(src.relative_to(P)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scope':'Source-region names only; no inferred regional urethral segmentation, anatomy certification or physical transparency'},indent=2))
