from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(n,b=False):return ImageFont.truetype(B if b else F,n)
rec=json.loads((R/'build-receipt.json').read_text()); bg=(17,23,28);fg=(233,237,240);mut=(165,178,187);line=(94,122,140);blue=(128,191,222)
for lang in ['en','zh']:
 im=Image.new('RGB',(1520,1860),bg);d=ImageDraw.Draw(im)
 def txt(x,y,s,n=23,col=fg,b=False):d.text((x,y),s,font=font(n,b),fill=col)
 txt(32,20,'Adipose pads: add region context' if lang=='en' else '脂肪垫：补充身体区域参照',36,b=True)
 txt(32,72,'4 original abdominal / flank pads • new private reconstruction' if lang=='en' else '4 个原始腹部／侧腰脂肪垫 • 新建私人重建版本',24,mut)
 txt(32,112,'Same meshes and camera. Updated adds labels and an authored body locator.' if lang=='en' else '几何和视角保持一致。Updated 增加标签与原创身体定位轮廓。',22,mut)
 for row,(view,y) in enumerate([('overview',205),('detail',1080)]):
  pad=Image.open(R/f'{view}-pads.png').convert('RGBA');body=Image.open(R/f'{view}-body.png').convert('RGBA')
  if row==0:
   pad=pad.resize((648,810));body=body.resize((648,810))
  else:pad=pad.resize((648,630));body=body.resize((648,630))
  w,h=pad.size
  for idx,x in enumerate([32,800]):
   txt(x,y-45,('Original' if idx==0 else 'Updated')+(' · overview' if row==0 else ' · same-region detail') if lang=='en' else ('Original' if idx==0 else 'Updated')+(' · 全身定位' if row==0 else ' · 同区域近景'),26,b=True)
   if idx:
    mask=body.getchannel('A').point(lambda q:255 if q>64 else 0)
    edge=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask.filter(ImageFilter.MinFilter(5)))
    outline=Image.new('RGBA',body.size,(*line,0));outline.putalpha(edge);im.paste(outline,(x,y),outline)
   im.paste(pad,(x,y),pad)
   if idx:
    for num,name,anchor in [(1,'Abdominal subcutaneous pad 1',(210,90) if row==0 else (30,30)),(2,'Flank pad -1',(15,330) if row==0 else (8,525))]:
     p=rec['views'][view]['anchors'][name];px=x+p[0]*w;py=y+(1-p[1])*h
     ax,ay=x+anchor[0],y+anchor[1]
     d.line([(ax+12,ay+13),(px,py)],fill=blue,width=2);d.ellipse((px-5,py-5,px+5,py+5),fill=blue)
     d.rounded_rectangle((ax,ay,ax+30,ay+30),radius=6,fill=blue);txt(ax+8,ay-2,str(num),22,b=True,col=bg)
  if row==0:
   txt(815,960,'1  Abdominal • 腹部' if lang=='en' else '1  腹部 • Abdominal',22)
   txt(815,995,'2  Flank • 侧腰' if lang=='en' else '2  侧腰 • Flank',22)
 txt(32,1740,'Depth cue: front-facing pads vs side pads. No cutaway or fitted skin boundary.' if lang=='en' else '深度提示：前方脂肪垫与侧方脂肪垫。未作剖切，轮廓不代表拟合皮肤边界。',22,mut)
 txt(32,1780,'Locator is illustrative. Other pads omitted; no volume, complete-anatomy or clinical claim.' if lang=='en' else '轮廓仅供定位；其他脂肪垫未展示。不代表体积、完整解剖或临床验证。',22,mut)
 txt(32,1820,'Source: original Network_Systems_Draft.blend • geometry preserved • CPU Cycles, 32 samples' if lang=='en' else '来源：原创 Network_Systems_Draft.blend • 几何保留 • CPU Cycles，32 samples',19,mut)
 im.save(R/f'comparison-{lang}.png')
 im.convert('L').save(R/f'comparison-{lang}-grayscale.png')
