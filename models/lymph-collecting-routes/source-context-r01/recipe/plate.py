from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from pathlib import Path
import json
R=Path(__file__).resolve().parent
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';B=F.replace('Regular','Bold')
def font(n,b=False):return ImageFont.truetype(B if b else F,n)
rec=json.loads((R/'build-receipt.json').read_text());bg=(17,23,28);fg=(233,237,240);mut=(165,178,187);blue=(128,191,222)
for lang in ['en','zh']:
 im=Image.new('RGB',(1520,1960),bg);d=ImageDraw.Draw(im)
 def txt(x,y,s,n=23,col=fg,b=False):d.text((x,y),s,font=font(n,b),fill=col)
 txt(32,20,'Thoracic duct: name the route, mark its limits' if lang=='en' else 'Thoracic duct 胸导管：标明路径与模型边界',34,b=True)
 txt(32,72,'Source-named “Thoracic duct — left venous angle” • new private reconstruction' if lang=='en' else '源文件名称：Thoracic duct — left venous angle • 新建私人重建版本',23,mut)
 txt(32,112,'Source name is not anatomical verification. No venous junction or continuous lumen shown.' if lang=='en' else '源文件名称不等于解剖验证。未展示经验证的静脉连接或连续管腔。',22,mut)
 for row,(view,y) in enumerate([('overview',205),('detail',1180)]):
  size=(648,810) if row==0 else (648,630)
  pads=Image.open(R/f'{view}-pads.png').convert('RGBA').resize(size);body=Image.open(R/f'{view}-body.png').convert('RGBA').resize(size);route=Image.open(R/f'{view}-route.png').convert('RGBA').resize(size);w,h=size
  for idx,x in enumerate([32,800]):
   txt(x,y-45,('Original' if idx==0 else 'Updated')+(' · overview' if row==0 else ' · route detail') if lang=='en' else ('Original' if idx==0 else 'Updated')+(' · 总览' if row==0 else ' · 路径近景'),26,b=True)
   if idx:
    mask=body.getchannel('A').point(lambda q:255 if q>64 else 0);edge=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask.filter(ImageFilter.MinFilter(5)));outline=Image.new('RGBA',size,(75,92,105,0));outline.putalpha(edge);im.paste(outline,(x,y),outline)
    muted=pads.convert('L').convert('RGBA');muted.putalpha(pads.getchannel('A').point(lambda q:int(q*.45)));im.paste(muted,(x,y),muted);im.paste(route,(x,y),route)
    for num,key,anchor in [(1,'upper',(435,85) if row==0 else (435,70)),(2,'lower',(50,350) if row==0 else (50,525))]:
     p=rec['views'][view]['anchors'][key];px=x+p[0]*w;py=y+(1-p[1])*h;ax,ay=x+anchor[0],y+anchor[1]
     d.line([(ax+14,ay+14),(px,py)],fill=blue,width=2);d.ellipse((px-6,py-6,px+6,py+6),outline=blue,width=2);d.rounded_rectangle((ax,ay,ax+32,ay+32),radius=6,fill=blue);txt(ax+8,ay-2,str(num),22,col=bg,b=True)
   else:im.paste(pads,(x,y),pads)
  if row==0:
   txt(815,1030,'1  Upper source cap ≠ verified vein junction' if lang=='en' else '1  上端源模型封口 ≠ 已验证的静脉连接',21)
   txt(815,1065,'2  Lower source cap ≠ complete inflow anatomy' if lang=='en' else '2  下端源模型封口 ≠ 完整流入解剖',21)
   txt(815,1100,'Bright: selected route. Gray: retained scaffold.' if lang=='en' else '亮色：所选路径。灰色：保留的原始支架。',20,mut)
 txt(32,1840,'Schematic source path; other tissues omitted. Detail crops peripheral routes, not selected endpoints.' if lang=='en' else '源路径为示意结构；其他组织省略。近景裁去周围支路，但保留所选路径的两端。',22,mut)
 txt(32,1880,'Caps mark model limits, not lumen continuity. Body outline is an editorial locator, not registration.' if lang=='en' else '封口表示模型边界，并非连续管腔。身体轮廓仅作编辑定位参照，不代表解剖配准。',22,mut)
 txt(32,1920,'Same source geometry / cameras • original scaffold preserved • no clinical or live-runtime claim' if lang=='en' else '源几何／视角一致 • 原始支架保留 • 不代表临床或实时运行验证',20,mut)
 im.save(R/f'comparison-{lang}.png');im.convert('L').save(R/f'comparison-{lang}-grayscale.png')
