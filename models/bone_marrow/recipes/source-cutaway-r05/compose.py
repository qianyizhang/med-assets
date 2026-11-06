from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,hashlib,json
ap=argparse.ArgumentParser();ap.add_argument('--renders',required=True);ap.add_argument('--baseline',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();R=Path(a.renders);B=Path(a.baseline);O=Path(a.out)
rows=json.loads((R/'bindings.json').read_text())
for r in rows:
 if hashlib.sha256((R/r['file']).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Native render hash mismatch')
baseline_image=Image.open(B/'front.png').convert('RGBA')
if baseline_image.size!=(1000,1200) or hashlib.sha256(baseline_image.tobytes()).hexdigest()!='b32fd147c241f16e99b42246b01e60eea6f74079e37b0d04b25832ad8dc7cc4f':raise ValueError('Baseline decoded pixel hash mismatch')
if O.exists():raise ValueError('Output must be new')
O.mkdir(parents=True);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(font,24);g=ImageFont.truetype(font,20);im=Image.new('RGB',(1600,1150),'#171d20');d=ImageDraw.Draw(im)
for i,(path,title) in enumerate([(B/'front.png','Before: disconnected schematic compartment'),(R/'front.png','Candidate: source envelope + authored interior')]):
 q=Image.open(path).convert('RGB');q.thumbnail((780,960));im.paste(q,(10+i*800,65));d.text((20+i*800,22),title,font=f,fill='#edf0f2')
for y,t in [(1030,'Different models, separate framing. BP3D femoral exterior only; internal cortex/network/marrow are authored.'),(1065,'Teaching cutaway: front marrow removed for visibility. Network is NOT micro-CT / measured tissue.'),(1100,'Illustrative color transition, not an age-specific marrow boundary. Original whole model remains Needs revision.')]:d.text((25,y),t,font=g,fill='#d7c28e')
im.save(O/'before-after.png')
# Separate explanatory context: never substitute it for native evidence.
im=Image.new('RGB',(1600,1260),'#171d20');d=ImageDraw.Draw(im);F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';h=ImageFont.truetype(F,30);t=ImageFont.truetype(F,25);small=ImageFont.truetype(F,22)
d.text((35,22),'Proximal femur cutaway · 股骨近端剖示教学',font=h,fill='#edf0f2');d.text((35,70),'Source exterior + authored interior · 来源外形 + 人工内部结构',font=t,fill='#ddc38a');q=Image.open(R/'front.png').convert('RGB');q.thumbnail((800,960));im.paste(q,(20,125))
blocks=[(175,'Outer shape / 外形',['BodyParts3D left femur','BodyParts3D 左股骨外形','Window and lower crop are editorial.','开窗与下端截断为展示处理。']),(370,'Shell + network / 外壳与网架',['Cortical offset and connected network','are authored—not measured micro-CT.','皮质骨厚度与连通网架为人工示意，','不是测量结果或 micro-CT 重建。']),(605,'Marrow display / 骨髓显示',['Red/yellow colors teach compartments.','Color transition is not an age map.','红/黄色用于区分教学区域，','渐变不代表年龄相关的分布界线。']),(825,'Removed for visibility / 为观察而移除',['Front marrow is partly removed.','Visible gaps are not physiological air.','前部部分骨髓被移除以显示网架，','可见间隙不代表生理性空气。'])]
for y,title,lines in blocks:
 d.text((870,y),title,font=t,fill='#e9ecef')
 for k,line in enumerate(lines):d.text((870,y+48+k*36),line,font=small,fill='#b9c6cc')
d.text((35,1125),'Teaching only; not patient-specific/clinical. Original remains Needs revision.',font=t,fill='#ddc38a');d.text((35,1170),'仅用于结构关系教学，不是个体化或临床模型。原始完整骨髓模型仍需修改。',font=t,fill='#ddc38a');im.save(O/'annotated-context.png');native=[]
for fn in ['front.png','oblique.png','reverse.png','close.png']:
 q=Image.open(R/fn);dest=O/(Path(fn).stem+'.webp');q.save(dest,lossless=True);assert q.convert('RGBA').tobytes()==Image.open(dest).convert('RGBA').tobytes();native.append({'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'decoded_pixels_equal_png_sha256':hashlib.sha256((R/fn).read_bytes()).hexdigest()})
(O/'media-bindings.json').write_text(json.dumps({'native':native,'baseline_glb_sha256':'c277ea5b96dfa8437e6ab80e3f5d69d87b95b3a5e0412ec521b3192377d95597','baseline_png_sha256':hashlib.sha256((B/'front.png').read_bytes()).hexdigest(),'before_after_sha256':hashlib.sha256((O/'before-after.png').read_bytes()).hexdigest(),'context_sha256':hashlib.sha256((O/'annotated-context.png').read_bytes()).hexdigest(),'scope':'Native WebPs lossless; composite/context resize native panels and add explanatory labels; not anatomy verification.'},indent=2))
