from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,textwrap,json
import argparse
parser=argparse.ArgumentParser(description='Label actual rendered pixels in a NEW output directory only.')
parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
a=parser.parse_args();D=Path(a.input).resolve();OUT=Path(a.output).resolve();OUT.mkdir(parents=True,exist_ok=False)
W,H=2400,1450;im=Image.new('RGB',(W,H),'#141b22');d=ImageDraw.Draw(im)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
f=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
def text(x,y,t,size=25,color='#dee5eb',bold=False):d.text((x,y),t,font=f(size,bold),fill=color)
def wrap(x,y,t,width=48,size=24,color='#b9c5cf'):
 lines=[]; limit=max(1,width//2)
 while t:
  n=min(limit,len(t))
  while n<len(t) and t[n] in '，。；：、！？）':n+=1
  lines.append(t[:n]);t=t[n:]
 for line in lines:text(x,y,line,size,color);y+=size+9
 return y
text(45,30,'食管壁',48,bold=True);text(46,92,'短节段纵向剖切示意｜四层管壁，五个标注区',28)
im.paste(Image.open(D/'oblique.png').convert('RGB').resize((900,990)),(35,170));text(45,1185,'纵向楔形切除使管壁内部可见',25)
# Exact-render cross section with numbered anchors inside each modeled compartment.
im.paste(Image.open(D/'cross-section.png').convert('RGB').resize((650,715)),(980,170));text(1000,920,'同一 GLB 模型的横断面视图',25)
center=(980+325,170+357.5);params=json.loads((D/'parameters.json').read_text());angles=[150,120,90,60,30]
r=[params[x] for x in ['lumen_radius_m','mucosa_outer_radius_m','submucosa_outer_radius_m','circular_muscle_outer_radius_m','longitudinal_muscle_outer_radius_m','adventitia_outer_radius_m']]
radii=[]
for i,angle in enumerate(angles):
 t=math.radians(angle);v=r.copy();v[0]+=params['lumen_fold_amplitude_m']*math.cos(params['illustrative_fold_count']*t);v[1]+=params['mucosa_outer_fold_amplitude_m']*math.cos(params['illustrative_fold_count']*t);radii.append((v[i]+v[i+1])/2)
pixels_per_m=1100/(r[-1]*.033/.0118)
for k,(r,a) in enumerate(zip(radii,angles),1):
 t=math.radians(a);x=center[0]+r*pixels_per_m*.65*math.cos(t);y=center[1]-r*pixels_per_m*.65*math.sin(t)
 if k==5:
  tx,ty=x,y;x+=48;y-=23;d.line((tx,ty,x,y),fill='white',width=2);d.ellipse((tx-3,ty-3,tx+3,ty+3),fill='#15222c',outline='white')
 d.ellipse((x-17,y-17,x+17,y+17),fill='#15222c',outline='white',width=2);box=d.textbbox((0,0),str(k),font=f(21,True));d.text((x-(box[2]-box[0])/2,y-14),str(k),font=f(21,True),fill='white')
text(1250,515,'管腔',24,bold=True)
labels=[('1  黏膜（合并表示）','上皮、固有层和黏膜肌层合并表示，未分别建模。'),('2  黏膜下层','结缔组织区域；省略腺体、血管和神经。'),('3  内环行肌层','外肌层（固有肌层）的内层；典型肌纤维环绕管腔排列。'),('4  外纵行肌层','外肌层（固有肌层）的外层；典型肌纤维沿食管长轴排列。'),('5  外膜','本胸段示意模型最外侧的结缔组织层。')]
y=180
for name,desc in labels:
 text(1690,y,name,29,bold=True);y=wrap(1690,y+44,desc,43,23)+37
text(985,1000,'本图不表达实测尺寸',27,bold=True)
wrap(985,1048,'各层厚度、管腔褶皱、节段长度及颜色均为教学设定；楔形缺口和端面是人为剖切，不是正常解剖开口。',78,23)
wrap(985,1165,'未重建单个细胞、肌纤维、神经丛或食管各段肌肉类型的差异。',78,23)
d.line((45,1280,2355,1280),fill='#4b5c69',width=2)
text(45,1310,'仅为教学补充：不是患者模型，不替代完整食管模型及其动画。',27,bold=True)
text(45,1360,'参考：哥伦比亚大学人体组织学实验课程；MH 109 医学组织学切片集。未复制参考图片。',23)
im.save(OUT/'teaching-sheet-zh-CN.png')
