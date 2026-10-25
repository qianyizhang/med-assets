from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,textwrap,json
import argparse
parser=argparse.ArgumentParser(description='Label actual rendered pixels in a NEW output directory only.')
parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
a=parser.parse_args();D=Path(a.input).resolve();OUT=Path(a.output).resolve();OUT.mkdir(parents=True,exist_ok=False)
W,H=2400,1450;im=Image.new('RGB',(W,H),'#141b22');d=ImageDraw.Draw(im)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
def text(x,y,t,size=25,color='#dee5eb',bold=False):d.text((x,y),t,font=f(size,bold),fill=color)
def wrap(x,y,t,width=48,size=24,color='#b9c5cf'):
 for line in textwrap.wrap(t,width):text(x,y,line,size,color);y+=size+9
 return y
text(45,30,'ESOPHAGEAL WALL',48,bold=True);text(46,92,'Illustrative short-segment cutaway | four tunics, five labeled compartments',28)
im.paste(Image.open(D/'oblique.png').convert('RGB').resize((900,990)),(35,170));text(45,1185,'Longitudinal wedge exposes the inner wall',25)
# Exact-render cross section with numbered anchors inside each modeled compartment.
im.paste(Image.open(D/'cross-section.png').convert('RGB').resize((650,715)),(980,170));text(1000,920,'Transverse view of the same GLB',25)
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
text(1250,515,'LUMEN',24,bold=True)
labels=[('1  Mucosa','Composite compartment; epithelium, lamina propria and muscularis mucosae are not separated.'),('2  Submucosa','Connective tissue compartment. Glands, vessels and nerves omitted.'),('3  Inner circular muscle','Muscularis externa: typical fibers wrap around the lumen.'),('4  Outer longitudinal muscle','Muscularis externa: typical fibers run along the organ.'),('5  Adventitia','Outer connective tissue in this illustrative thoracic segment.')]
y=180
for name,desc in labels:
 text(1690,y,name,29,bold=True);y=wrap(1690,y+44,desc,43,23)+37
text(985,1000,'What the drawing does NOT measure',27,bold=True)
wrap(985,1048,'Layer thicknesses, folded lumen, length and colors are explanatory choices. The wedge and end faces are editorial cuts.',78,23)
wrap(985,1165,'Individual cells, muscle fibers, nerve plexuses and regional muscle-type variation are not reconstructed.',78,23)
d.line((45,1280,2355,1280),fill='#4b5c69',width=2)
text(45,1310,'Teaching supplement, not a patient model or replacement of the full-organ animation.',27,bold=True)
text(45,1360,'References: Columbia human histology laboratory; MH 109 Medical Histology Collection. No source imagery copied.',23)
im.save(OUT/'teaching-sheet.png')
