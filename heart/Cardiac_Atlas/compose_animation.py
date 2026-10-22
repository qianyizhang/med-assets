import os
from PIL import Image,ImageDraw,ImageFont
import os,subprocess,json,numpy as np
R=os.path.dirname(os.path.abspath(__file__));F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def ft(n,b=False):return ImageFont.truetype(B if b else F,n)
# All 24 native frames per 0.8s cycle, encoded at 30fps.
folder=R+'/animation/composite';os.makedirs(folder,exist_ok=True)
phases=['Atrial systole','Atrial systole','Isovolumetric contraction','Ventricular ejection','Ventricular ejection','Ventricular ejection','Relaxation','Diastolic filling','Diastolic filling','Diastolic filling','Diastolic filling','Diastolic filling']
for i,fr in enumerate(range(1,25)):
 canvas=Image.new('RGB',(1920,850),'#0a131c');d=ImageDraw.Draw(canvas)
 d.text((35,18),'CARDIAC ATLAS',font=ft(27,True),fill='#7bd3cd');d.text((1570,22),'75 BPM  /  schematic',font=ft(22),fill='#a9bac6')
 for j,(mode,label) in enumerate([('tissue','Tissue-style'),('clinical','Clinical cutaway'),('transparent','Transparent')]):
  im=Image.open(R+'/animation/'+mode+'/'+str(fr).zfill(3)+'.png').convert('RGB');canvas.paste(im,(j*640,95));d.text((j*640+30,64),label,font=ft(25,True),fill='#e9eff4')
 d.rectangle((35,765,1885,773),fill='#263a49');d.rectangle((35,765,35+int(1850*(i+1)/24),773),fill='#69d3ca')
 d.text((35,796),('Atrial systole' if fr<=3 else 'Isovolumetric contraction' if fr<=5 else 'Ventricular ejection' if fr<=11 else 'Relaxation' if fr<=13 else 'Diastolic filling'),font=ft(24,True),fill='#dce9ef');d.text((840,799),'Illustrative motion and valve timing • not a physiological simulation',font=ft(22),fill='#96acbc')
 canvas.save(folder+'/'+str(i).zfill(3)+'.png')
# Every source frame is rendered directly; no optical-flow interpolation.
cmd=['ffmpeg','-y','-framerate','30','-i',folder+'/%03d.png','-vf','fps=30,format=yuv420p','-c:v','libx264','-crf','18','-preset','medium',R+'/animation/one_cycle.mp4'];subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg','-y','-stream_loop','8','-i',R+'/animation/one_cycle.mp4','-t','7.2','-c','copy','-movflags','+faststart',R+'/Cardiac_Atlas_Beating_Heart.mp4'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
# Verify more than one still frame and actual phase-dependent deformation.
a=np.asarray(Image.open(R+'/animation/tissue/001.png')).astype(float);b=np.asarray(Image.open(R+'/animation/tissue/009.png')).astype(float)
qa={'preview_rendered_fps':30,'encoded_fps':30,'native_timeline_fps':30,'bpm':75,'seconds_per_cycle':.8,'duration_seconds':7.2,'tissue_ED_vs_systole_mean_absolute_pixel_difference':float(abs(a-b).mean()),'source_frames_per_mode':24,'note':'Preview renders each native frame; no optical-flow interpolation. Native scene contains full continuous driver animation.'}
json.dump(qa,open(R+'/exports/video_QA.json','w'),indent=2)
# Poster from actual three material renders.
canvas=Image.new('RGB',(1980,920),'#0a131c');d=ImageDraw.Draw(canvas);d.text((45,25),'One editable heart. Three teaching views.',font=ft(40,True),fill='#edf3f7')
for j,(fn,label) in enumerate([('01_tissue_hero.png','Tissue-style / procedural PBR'),('03_clinical_full.png','Clinical / circulation categories'),('04_transparent.png','Transparent / internal relationships')]):
 im=Image.open(R+'/renders/'+fn).convert('RGB').resize((640,640),Image.Resampling.LANCZOS);canvas.paste(im,(20+j*650,125));d.text((35+j*650,797),label,font=ft(25,True),fill='#b3d3df')
d.text((45,866),'Real Blender geometry and animation. Idealized anatomy; not patient-derived or clinically validated.',font=ft(23),fill='#93aab9');canvas.save(R+'/renders/10_three_materials.png')
print('MOVIE AND POSTER COMPLETE')
