"""Source-bound bilingual locators and matched within-study comparison plates."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

p=argparse.ArgumentParser();p.add_argument('--review',type=Path,required=True);a=p.parse_args();R=a.review
V1=R/'v1/matched-128';V2=R/'v2/raw-128';OUT=R/'evidence';OUT.mkdir(exist_ok=False)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
cjk='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def f(size,zh=False,strong=False):return ImageFont.truetype(cjk if zh else bold if strong else font,size)
ink='#182c37';muted='#526670';accent='#8b4510'
def txt(d,xy,s,size=22,zh=False,strong=False,fill=ink):d.text(xy,s,font=f(size,zh,strong),fill=fill)
bindings={v['file']:v for v in json.loads((V2/'bindings.json').read_text())['views']}
input_hashes={}
def load(path):
    input_hashes[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')

plate=Image.new('RGB',(1800,1100),'#f5f7f8');d=ImageDraw.Draw(plate)
txt(d,(40,24),'Right ulnar nerve at the elbow',38,strong=True)
txt(d,(42,73),'右侧尺神经与肘部骨性标志',28,zh=True)
txt(d,(1030,38),'Source-native static study · illustrative colors',22,fill=muted)
txt(d,(1030,77),'来源坐标与静态姿态 · 颜色仅作区分',21,zh=True,fill=muted)
panels=[('whole-posterior.png','Whole context','全局定位',40),('elbow-posteromedial.png','Oblique detail','斜位细节',630),('elbow-medial.png','Medial detail','内侧细节',1220)]
label_rows=[]
for filename,en,zh,x in panels:
    txt(d,(x,127),en,24,strong=True);txt(d,(x+255,130),zh,21,zh=True)
    y=170;size=540;plate.paste(load(V2/filename).resize((size,size),Image.Resampling.LANCZOS),(x,y))
    view=bindings[filename];anchors={v['key']:v for v in view['anchors']}
    def pixel(key):return tuple([x+anchors[key]['pixel'][0]*size/800,y+anchors[key]['pixel'][1]*size/800])
    if filename.startswith('whole'):
        # Whole view is +Y orthographic; source elbow box is 0.16 native units
        # across X and Z, centered at the detail camera target. No registration.
        center=(x+(.195-.217)/.66*size+size/2,y+(1.13-1.105)/.66*size+size/2)
        half=.08/.66*size
        # +Y viewing reverses X on screen.
        center=(x-(-.217+.195)/.66*size+size/2,center[1])
        box=(center[0]-half,center[1]-half,center[0]+half,center[1]+half)
        d.rectangle(box,outline=ink,width=3);txt(d,(x+20,y+300),'Detail region',18,strong=True)
        txt(d,(x+20,y+326),'细节区域',18,zh=True)
        d.line((x+145,y+320,box[0],center[1]),fill=ink,width=2)
        for key,dy in [('proximal_extent',-18),('distal_extent',15)]:
            px,py=pixel(key);d.ellipse((px-5,py-5,px+5,py+5),outline=ink,width=2)
            tx=x+12 if key=='proximal_extent' else x+310
            ty=py+dy
            line_end=tx+135 if key=='proximal_extent' else tx-8
            d.line((px,py,line_end,ty+10),fill=ink,width=2)
            txt(d,(tx,ty),'Source extent',16,strong=True);txt(d,(tx,ty+21),'来源范围端点',16,zh=True)
    else:
        positions={'nerve':(.15,.18),'medial_epicondyle':(.13,.54),'olecranon':(.87,.55)}
        for number,key in enumerate(['nerve','medial_epicondyle','olecranon'],1):
            px,py=pixel(key);rx,ry=positions[key];cx,cy=x+rx*size,y+ry*size
            d.line((cx,cy,px,py),fill=ink,width=2)
            d.ellipse((px-3,py-3,px+3,py+3),fill=ink)
            d.ellipse((cx-15,cy-15,cx+15,cy+15),fill='#ffffff',outline=ink,width=2)
            txt(d,(cx-7,cy-12),str(number),19,strong=True)
            label_rows.append({'panel':filename,'label':number,'anchor':anchors[key],'displayPixel':[px,py]})
labels=[('1  Ulnar nerve','尺神经'),('2  Medial epicondyle of humerus','肱骨内上髁'),('3  Olecranon of ulna','尺骨鹰嘴')]
for (en,zh),x in zip(labels,[40,630,1220]):
    txt(d,(x,752),en,23,strong=True);txt(d,(x,788),zh,23,zh=True)
d.line((40,837,1760,837),fill='#c5d0d5',width=2)
for y,en,zh in [
 (857,'Skin, muscles and retinaculum omitted; this is not a cubital tunnel model.','未显示皮肤、肌肉与支持带；不表示完整肘管。'),
 (936,'Source endpoints are not anatomical origins or terminations. No clinical or motion validation.','来源端点不是解剖起点或末梢。未作临床或运动验证。')]:
    txt(d,(40,y),en,23);txt(d,(40,y+34),zh,22,zh=True)
txt(d,(40,1044),'Z-Anatomy · CC BY-SA 4.0 | BodyParts3D · Database Center for Life Science · historical CC BY-SA 2.1 Japan credit',18,fill=muted)
plate.save(OUT/'teaching.png');ImageOps.grayscale(plate).save(OUT/'teaching-grayscale.png')

compare=Image.new('RGB',(1640,1870),'#f5f7f8');q=ImageDraw.Draw(compare)
txt(q,(30,20),'Original: source study v1',28,strong=True);txt(q,(850,20),'Updated: source study v2',28,strong=True)
txt(q,(30,64),'Matched GLB reimports · unchanged geometry · intentional material differences',22,fill=muted)
for row,(filename,label) in enumerate([('whole-posterior.png','Whole context'),('elbow-posteromedial.png','Elbow detail')]):
    y=110+row*840
    txt(q,(30,y),label,23,strong=True)
    compare.paste(load(V1/filename),(20,y+34));compare.paste(load(V2/filename),(840,y+34))
txt(q,(30,1805),'Separate regional supplement. The historical whole-body scaffold is not registered to these source-native views.',20)
txt(q,(30,1835),'Independent source review prompted darker materials, clearer locators and explicit limits in the teaching sheet.',18,fill=muted)
compare.save(OUT/'comparison.png')
(OUT/'composition-bindings.json').write_text(json.dumps({'inputs':input_hashes,'locators':label_rows,'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.png')},'scope':'Numeric leaders terminate on projected exact reimport mesh vertices; semantic landmarks are based on source graphical endpoints and independent pixel review. No cross-source registration.'},indent=2)+'\n')
