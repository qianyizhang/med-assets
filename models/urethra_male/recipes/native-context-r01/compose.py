from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont
import hashlib,json
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);opts=ap.parse_args();P=opts.work;O=P/'r01/review-comparison.png';assert not O.exists();f='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font=lambda n:ImageFont.truetype(f,n)
assert hashlib.sha256((P/'r01/context.glb').read_bytes()).hexdigest()=='d2d88c936287f4ea5978aba1f17e86975c587a102e498595dd7a58aa07c269e7'
im=Image.new('RGB',(1600,1080),'#171b20');d=ImageDraw.Draw(im)
d.text((36,20),'Male urethra: isolated draft → same-source context',font=font(32),fill='#f1f3f5');d.text((36,64),'男性尿道：孤立草稿 → 同源结构位置关系',font=font(27),fill='#d1d7dd')
rows=[]
for x,fn,en,zh in [(30,'baseline-renders/whole.png','Original authored draft · still needs revision','原始示意草稿 · 仍需修订'),(820,'r01/translucent-renders/context-side-source.png','Source-context pilot · transparency is diagnostic','同源背景试验 · 透明仅用于显示内部关系')]:
 src=Image.open(P/fn).convert('RGB');im.paste(src.resize((750,750)),(x,180));d.text((x,118),en,font=font(23),fill='#f1f3f5');d.text((x,151),zh,font=font(21),fill='#cbd1d8');rows.append({'image':fn,'sha256':hashlib.sha256((P/fn).read_bytes()).hexdigest()})
d.text((36,945),'Different models, poses and framing; not registered or scale-matched.',font=font(23),fill='#e8bc73')
d.text((36,978),'模型、姿态与取景不同，未经配准或等比例匹配；来源管面不等于已验证的管腔。',font=font(23),fill='#e8bc73')
d.text((36,1017),'No wall-thickness, outlet, flow or clinical-validation claim. Source geometry unchanged.',font=font(22),fill='#cbd1d8')
im.save(O);(P/'r01/comparison-bindings.json').write_text(json.dumps(rows,indent=2))
