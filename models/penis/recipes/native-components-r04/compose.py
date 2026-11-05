from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--renders',required=True);p.add_argument('--baseline-renders');p.add_argument('--out',required=True);a=p.parse_args();R=Path(a.renders);B=Path(a.baseline_renders) if a.baseline_renders else None;O=Path(a.out);assert json.loads((R/'bindings.json').read_text())['sha256']=='c44d35e13be11d2fb35141747d819d4609a45ca0a5527c89e1015618d17cab70','Render binding mismatch';assert json.loads((B/'bindings.json').read_text())['baseline_sha256']=='8bf7e4b3e66731df07a3167b1a18b033280e1195f76a9ff3205249b5c16f926a','Baseline binding mismatch';assert not O.exists(),'Output file must be new';im=Image.new('RGB',(1800,1020),'#13171c');d=ImageDraw.Draw(im);f=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
d.text((28,18),'Penile internal components / 阴茎内部组织关系：源模型核查',font=f(30),fill='#eeeeee');d.text((28,68),'Different sources and poses; no registration / 不同来源及姿态，未配准',font=f(20),fill='#aab2bd')
for i,(path,title) in enumerate([('baseline-renders/whole.png','Original cylinder/sphere draft / 原柱体与球体草稿'),('r04/plus-y.png','Source components / 源组织结构'),('r04/side.png','Native source side view / 源模型侧向观察')]):
 x=20+i*595;d.text((x,114),title,font=f(20),fill='#e7ebef');im.paste(Image.open(B/'whole.png' if path.startswith('baseline') else R/Path(path).name).convert('RGB').resize((570,570)),(x,155))
lines=[('Blue-gray: cavernosal body · Tan: spongiosum · Rose: glans. Skin omitted, not an external-surface model.','#dce6e9'),('蓝灰：阴茎海绵体；浅褐：尿道海绵体；淡粉：阴茎头。未显示皮肤，不是体表模型。','#dce6e9'),('Source glans has edge defects; no urethral lumen or internal septum added. Coarse source ends retained.','#f3b853'),('源阴茎头存在边拓扑缺陷；未添加尿道腔或内部中隔。保留粗糙的源端部形态。','#f3b853'),('Original remains Needs revision · Not clinical validation · Z-Anatomy CC BY-SA 4.0','#aab2bd')]
for j,(s,c) in enumerate(lines):d.text((28,770+j*39),s,font=f(21),fill=c)
im.save(O)
