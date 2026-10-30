"""Bilingual teaching sheet from unchanged, exact-GLB rendered pixels."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CJK='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
INK='#1c303b';MUTED='#526976';PAPER='#f5f7f8'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def text(d,xy,s,size=22,bold=False,zh=False,fill=INK):
    d.text(xy,s,font=ImageFont.truetype(CJK if zh else BOLD if bold else REG,size),fill=fill)

def compose(renders,out):
    if out.exists():raise FileExistsError('New teaching directory required')
    b=json.loads((renders/'bindings.json').read_text())
    views={v['file']:v for v in b['views']}
    inputs={'bindings.json':sha(renders/'bindings.json')}
    plate=Image.new('RGB',(1900,1230),PAPER);d=ImageDraw.Draw(plate)
    text(d,(36,22),'Right median nerve: wrist and hand',38,bold=True)
    text(d,(38,72),'右侧正中神经：腕与手部骨性定位',28,zh=True)
    text(d,(1195,35),'Selected source groups · static study',22,fill=MUTED)
    text(d,(1195,74),'保留来源坐标 · 颜色仅作区分',22,zh=True,fill=MUTED)
    panels=[('whole-source.png','Whole subset','来源范围',36,165,430),
            ('hand-palmar.png','Palmar overview','掌侧总览',520,165,620),
            ('wrist-oblique.png','Wrist detail','腕部斜位细节',1200,165,620)]
    locators=[];positions={}
    for filename,en,zh,x,y,size in panels:
        text(d,(x,121),en,23,bold=True);text(d,(x+280 if size==620 else x+270,125),zh,20,zh=True)
        path=renders/filename
        if sha(path)!=views[filename]['sha256']:raise ValueError('Input image hash mismatch')
        inputs[filename]=sha(path)
        plate.paste(Image.open(path).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),(x,y))
        anchors={a['key']:a for a in views[filename]['anchors']}
        positions[filename]=(x,y,size)
        def project(key):
            q=anchors[key]['pixel'];return x+q[0]*size/900,y+q[1]*size/900
        if filename=='whole-source.png':
            # Exact palmar hand-camera footprint projected into same-axis whole view.
            cx=x+430/2+(-.275+.23)/.86*430
            cy=y+430/2+(1.10-.80)/.86*430
            half=.245/.86*430/2
            box=(cx-half,cy-half,cx+half,cy+half)
            d.rectangle(box,outline=INK,width=3)
            text(d,(x,615),'Box: hand/wrist view',21,bold=True)
            text(d,(x,646),'方框：手与腕的观察范围',21,zh=True)
            d.line((x+190,610,cx,box[3]),fill=INK,width=2)
            for key in ['proximal','distal']:
                px,py=project(key)
                d.ellipse((px-4,py-4,px+4,py+4),outline=INK,width=2)
                tx=x+4 if key=='proximal' else x+285
                ty=py-16 if key=='proximal' else py-12
                d.line((px,py,tx+125 if key=='proximal' else tx-8,ty+10),fill=INK,width=2)
                text(d,(tx,ty),'Source end',16,bold=True)
            text(d,(x,708),'All selected parts retained.',21)
            text(d,(x,738),'Detail views crop the camera.',21)
            text(d,(x,774),'选定结构保留；细节仅改变取景。',20,zh=True)
        else:
            layout=({'trunk':(1,.83,.11),'common':(2,.12,.42),'proper':(3,.10,.73),'scaphoid':(4,.12,.16)}
                    if filename=='hand-palmar.png' else
                    {'trunk':(1,.83,.14),'scaphoid':(4,.12,.38)})
            for key,(number,rx,ry) in layout.items():
                px,py=project(key);cx,cy=x+rx*size,y+ry*size
                assert x<=px<=x+size and y<=py<=y+size
                d.line((cx,cy,px,py),fill=INK,width=2)
                d.ellipse((px-3,py-3,px+3,py+3),fill=INK)
                d.ellipse((cx-16,cy-16,cx+16,cy+16),fill='white',outline=INK,width=2)
                text(d,(cx-7,cy-13),str(number),20,bold=True)
                locators.append({'panel':filename,'number':number,'anchor':anchors[key],
                                 'displayPixel':[px,py],'panelBox':[x,y,size,size]})
    labels=[(38,845,'1  Median nerve trunk','正中神经主干'),
            (950,845,'2  Common palmar digital group','掌侧指总神经组'),
            (38,925,'3  Proper palmar digital group','掌侧指固有神经组'),
            (950,925,'4  Scaphoid bone','舟骨')]
    for x,y,en,zh in labels:
        text(d,(x,y),en,25,bold=True);text(d,(x,y+34),zh,24,zh=True)
    d.line((36,1004,1820,1004),fill='#c5d0d5',width=2)
    text(d,(38,1023),'Skeletal localization only. Soft-tissue nerve/flexor relationships remain unresolved and are excluded.',22)
    text(d,(38,1058),'仅用于骨性定位。神经与屈肌软组织关系尚未解决，不属于本图教学范围。',22,zh=True)
    text(d,(38,1103),'Source ends are incomplete; no complete skin territory, tunnel, motion or clinical validation.',22)
    text(d,(38,1138),'来源末端不代表完整末梢；未验证皮肤分布区、腕管、运动或临床用途。',22,zh=True)
    text(d,(38,1190),'Z-Anatomy · CC BY-SA 4.0 | BodyParts3D · Database Center for Life Science · historical CC BY-SA 2.1 Japan credit',18,fill=MUTED)
    out.mkdir(parents=True)
    plate.save(out/'teaching.png');ImageOps.grayscale(plate).save(out/'teaching-grayscale.png')
    receipt={'artifactSha256':b['artifactSha256'],'inputs':inputs,'outputs':{p.name:sha(p) for p in out.glob('*.png')},
             'locators':locators,'scope':'V2 teaching composition only; exact V1 GLB and raw captures unchanged. '
             'All leaders bind reimported source-object vertices. Source ends do not establish anatomical origins or termini.'}
    (out/'composition-bindings.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--renders',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();compose(a.renders,a.out)
