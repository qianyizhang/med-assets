import os
from PIL import Image,ImageDraw,ImageFont
import numpy as np,os,json
R=os.path.dirname(os.path.abspath(__file__))
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def F(size,b=False):return ImageFont.truetype(bold if b else font,size)
# Label actual points in the rendered orthographic teaching view.
W,H=2100,1560;out=Image.new('RGB',(W,H),'#0a131c');d=ImageDraw.Draw(out)
d.text((70,45),'CARDIAC ATLAS',font=F(22,True),fill='#77d5d0')
d.text((70,86),'Inside the heart',font=F(48,True),fill='#f2f5f8')
d.text((70,152),'Idealized end-diastolic teaching view  /  anterior tissues removed',font=F(23),fill='#aebcc8')
im=Image.open(R+'/renders/02_clinical_cutaway.png').convert('RGB').resize((1180,1180),Image.Resampling.LANCZOS);off=(460,225);out.paste(im,off)
d=ImageDraw.Draw(out)
pos=np.array([1.,-14.5,3.4]);tar=np.array([0.,.05,.56]);f=(tar-pos);f/=np.linalg.norm(f);right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,f)
def proj(p):
 q=np.array(p)-tar;u=.5+q@right/6.8;v=.5+q@up/6.8;return (off[0]+1180*u,off[1]+1180*(1-v))
labels=[('Right atrium',(-1.,.32,1.48),'left','#71bbec'),('Pulmonary valve',(-.37,-.43,1.17),'left','#ead9a5'),('Tricuspid valve',(-.65,.05,.79),'left','#ead9a5'),('Right ventricle',(-.64,.12,-.35),'left','#71bbec'),('Interventricular septum',(.12,.0,-.58),'left','#e8b461'),('Papillary muscles',(.32,-.03,-1.02),'left','#dbe8ec'),('Left atrium',(.58,.73,1.52),'right','#ef929c'),('Aortic valve',(.32,.17,1.02),'right','#ead9a5'),('Mitral valve',(.55,.13,.67),'right','#ead9a5'),('Chordae tendineae',(.66,.14,-.15),'right','#dbe8ec'),('Left ventricle',(.95,.32,-.50),'right','#ef929c'),('Trabeculae carneae',(1.19,.26,-.68),'right','#ef929c')]
for side in ('left','right'):
 items=sorted([x for x in labels if x[2]==side],key=lambda a:proj(a[1])[1])
 for j,(name,p,_,color) in enumerate(items):
  tx,ty=proj(p);ly=400+j*153
  if side=='left':
   x=65;d.text((x,ly-28),name,font=F(23,True),fill=color);start=(x+345,ly+8);elbow=(435,ly+8)
  else:
   x=1710;d.text((x,ly-28),name,font=F(23,True),fill=color);start=(1685,ly+8);elbow=(1660,ly+8)
  d.line([start,elbow,(tx,ty)],fill=color,width=2);d.ellipse((tx-5,ty-5,tx+5,ty+5),fill=color)
d.text((70,1435),'WALL LAYERS   Endocardial lining  •  Myocardium  •  Epicardial outer surface',font=F(23),fill='#b8c8d5')
d.text((70,1480),'Great vessels and coronary overlay hidden for clarity. Procedural educational anatomy; not clinically validated.',font=F(20),fill='#8295a5')
out.save(R+'/renders/08_labeled_teaching_cutaway.png')
# Actual exported maps, shown as a usable asset-pipeline contact sheet.
w,h=2200,1410;out=Image.new('RGB',(w,h),'#0a131c');d=ImageDraw.Draw(out)
d.text((65,40),'MESH → UV → BAKED PBR',font=F(23,True),fill='#77d5d0');d.text((65,85),'The real texture pipeline',font=F(44,True),fill='#f3f6f9')
d.text((65,148),'Shared 2048² atlas for four chamber walls • Actual Blender Cycles bakes',font=F(24),fill='#b7c5d1')
files=[('UV layout','wall_atlas_UV_layout_2K.png','Packed islands; copied back to original wall meshes'),('Base color','wall_atlas_BaseColor_2K.png','sRGB • lighting-free tissue color'),('Roughness','wall_atlas_Roughness_2K.png','Linear / Non-Color • surface finish'),('Tangent normal','wall_atlas_Normal_OpenGL_2K.png','OpenGL +Y • Non-Color • microrelief')]
for i,(title,fn,caption) in enumerate(files):
 x=65+(i%2)*1080;y=230+(i//2)*550
 image=Image.open(R+'/textures/'+fn).convert('RGB').resize((475,475),Image.Resampling.LANCZOS);out.paste(image,(x,y));d.text((x+500,y+25),title,font=F(31,True),fill='#f0f4f7')
 words=caption.split();lines=[];line=''
 for word in words:
  if len(line+' '+word)>31:lines.append(line);line=word
  else:line=(line+' '+word).strip()
 lines.append(line)
 for j,line in enumerate(lines):d.text((x+500,y+90+j*32),line,font=F(22),fill='#abbcc9')
 d.text((x+500,y+250),'2048 × 2048 PNG',font=F(21),fill='#78d1cc')
d.text((65,1340),'Scope: chamber walls. Fine structures remain procedural; clinical and transparent views are material presets.',font=F(22),fill='#b2c3cf')
out.save(R+'/renders/09_texture_pipeline.png')
print('Teaching plates written')
