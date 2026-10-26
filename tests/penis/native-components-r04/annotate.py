from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--renders',required=True);p.add_argument('--baseline-renders');p.add_argument('--out',required=True);a=p.parse_args();R=Path(a.renders);B=Path(a.baseline_renders) if a.baseline_renders else None;O=Path(a.out);assert json.loads((R/'bindings.json').read_text())['sha256']=='c44d35e13be11d2fb35141747d819d4609a45ca0a5527c89e1015618d17cab70','Render binding mismatch';assert not O.exists(),'Output file must be new';im=Image.new('RGB',(1700,1120),'#13171c');d=ImageDraw.Draw(im);f=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
d.text((28,20),'Internal erectile tissues / 内部勃起组织：结构关系',font=f(31),fill='#eee');d.text((28,72),'Source-preserved surfaces; skin omitted / 保留源表面，未显示皮肤',font=f(22),fill='#b0b8c2')
im.paste(Image.open(R/'plus-y.png').convert('RGB').resize((900,900)),(0,120));im.paste(Image.open(R/'side.png').convert('RGB').resize((550,550)),(1110,450));
def lead(pt,anchor,txt,sub):
 d.line((pt,anchor),fill='#c9d2db',width=2);d.ellipse((pt[0]-4,pt[1]-4,pt[0]+4,pt[1]+4),fill='#c9d2db');d.text((anchor[0]+10,anchor[1]-20),txt,font=f(22),fill='#eee');d.text((anchor[0]+10,anchor[1]+14),sub,font=f(20),fill='#b0b8c2')
lead((450,365),(780,155),'Proximal / 近端','Root region, toward pelvis / 根部，朝向骨盆')
lead((392,562),(780,235),'Cavernosal body / 阴茎海绵体','Paired form joined in source / 源中两侧形态相连')
lead((450,545),(780,315),'Spongiosum / 尿道海绵体','Ventral column continues to glans / 腹侧组织延续至阴茎头')
lead((500,715),(780,395),'Glans · distal / 阴茎头 · 远端','No urethral lumen added / 未添加尿道腔')
d.text((30,1014),'Source defects retained; no watertight fusion, internal septum or full external anatomy. Original still needs revision.',font=f(21),fill='#f3b853');d.text((30,1050),'保留源缺陷；组织重叠不代表水密融合。未显示内部中隔或完整体表解剖。原草稿仍需修改。',font=f(21),fill='#f3b853')
im.save(O)
