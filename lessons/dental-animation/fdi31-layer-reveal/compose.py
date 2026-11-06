from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import math,json
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def txt(d,xy,s,size=16,fill='#b8cbd3',strong=False):d.text(xy,s,font=ImageFont.truetype(bold if strong else font,size),fill=fill)
files=sorted((ROOT/'source-frames').glob('*.png'));frames=[]
for i,p in enumerate(files):
 t=i/71; im=Image.new('RGB',(960,540),'#10242e');d=ImageDraw.Draw(im)
 d.rounded_rectangle((24,85,578,470),22,fill='#1d3542')
 layer=Image.open(p).convert('RGBA');layer=layer.resize((550,413),Image.Resampling.LANCZOS);im.paste(layer,(25,65),layer);d=ImageDraw.Draw(im)
 txt(d,(30,20),'DENTAL / ANIMATION STUDY 01',13,'#73d5cf');txt(d,(30,44),'One specimen, four source-labelled layers',25,'#f1f0e8',True)
 stage=0 if t<.17 else 1 if t<.4 else 2 if t<.72 else 3
 txt(d,(608,102),['ESTABLISH','REVEAL','INSPECT','RESET'][stage],13,'#73d5cf',True)
 h=['A prepared FDI 31','Separate without cutting','Read the source labels','Return to the source pose'][stage]
 txt(d,(608,141),h,19,'#f1f0e8',True)
 lines=[['Existing Balanced source mesh.','This is a prepared T2 specimen.'],['Editorial offsets reveal layers.','No anatomy has been repaired.'],['Enamel, dentin, pulp and bone.','Colour helps identify each layer.'],['Reversible transforms only.','Not physiological tissue motion.']][stage]
 for j,l in enumerate(lines):txt(d,(608,183+j*25),l,14)
 d.line((608,249,925,249),fill='#38535f')
 txt(d,(608,278),'SOURCE GEOMETRY / DRAFT LOOK',13,'#e9b461',True)
 for j,l in enumerate(['Source labels are not validation.','Surface artifacts remain visible.','Not a healthy canal baseline.','Buccolingual orientation unresolved.']):txt(d,(608,307+j*24),l,13)
 txt(d,(608,420),'SWIRendo • Benz / Heck / Walter',12,'#7f9da9');txt(d,(608,439),'2024 • CC BY-SA 4.0',12,'#7f9da9')
 for x,(n,c) in zip([38,168,296,407],[('Enamel','#dbe8e5'),('Dentin','#d99a4c'),('Pulp','#d64c74'),('Bone','#719bae')]):
  d.rounded_rectangle((x,444,x+10,454),2,fill=c);txt(d,(x+16,439),n,12,'#d7e3e7')
 d.line((30,489,930,489),fill='#29434f',width=3);d.line((30,489,30+900*t,489),fill='#73d5cf',width=3)
 txt(d,(30,507),'Editorial exploded view • Prepared specimen • No clinical or motion validation',12,'#8eaab5');txt(d,(875,507),f'{i/8:3.1f} / 9s',12,'#8eaab5')
 frames.append(im)
 if i in (0,30,50,71):im.save(OUT/f'fdi31-shot-{i}.jpg',quality=92)
if len(frames)!=72:raise SystemExit(f'Incomplete source render: {len(frames)} / 72')
frames[0].save(OUT/'fdi31-source-layer-reveal.gif',save_all=True,append_images=frames[1:],duration=[120,130]*36,loop=0,optimize=True)
print(OUT/'fdi31-source-layer-reveal.gif')
