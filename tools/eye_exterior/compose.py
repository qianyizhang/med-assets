"""Compose source-bound teaching and matched evidence; keep native panel pixels."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat

FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BG='#10191e'; FG='#edf1f2'; MUTED='#bcc9cf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Sheet:
    def __init__(self,size):
        self.image=Image.new('RGB',size,BG); self.overlay=Image.new('RGBA',size)
        self.draw=ImageDraw.Draw(self.overlay); self.panels=[]; self.texts=[]; self.elements=[]

    def text(self,xy,text,size=30,fill=FG):
        font=ImageFont.truetype(str(FONT),size)
        box=self.draw.textbbox(xy,text,font=font,anchor='lt')
        assert 0<=box[0] and 0<=box[1] and box[2]<=self.image.width and box[3]<=self.image.height, text
        self.draw.text(xy,text,font=font,fill=fill,anchor='lt')
        self.texts.append({'text':text,'box':list(box)})
        # CJK ascent/descent varies; SVG uses explicit top-edge baseline intent.
        self.elements.append(f'<text x="{xy[0]}" y="{xy[1]}" font-size="{size}" fill="{fill}" dominant-baseline="text-before-edge">{html.escape(text)}</text>')

    def panel(self,path,xy,crop=None):
        source=Image.open(path).convert('RGB'); crop=crop or (0,0,*source.size); panel=source.crop(crop)
        assert 0<=xy[0] and 0<=xy[1] and xy[0]+panel.width<=self.image.width and xy[1]+panel.height<=self.image.height
        self.image.paste(panel,xy)
        self.panels.append({'file':path.name,'sha256':digest(path),'crop':list(crop),'position':list(xy),'size':list(panel.size),'resampling':False})
        encoded=base64.b64encode(path.read_bytes()).decode(); ident='crop'+str(len(self.panels))
        self.elements.append(f'<defs><clipPath id="{ident}"><rect x="{xy[0]}" y="{xy[1]}" width="{panel.width}" height="{panel.height}"/></clipPath></defs><image x="{xy[0]-crop[0]}" y="{xy[1]-crop[1]}" width="{source.width}" height="{source.height}" href="data:image/png;base64,{encoded}" clip-path="url(#{ident})"/>')

    def leader(self,number,start,end):
        self.draw.line([tuple(start),tuple(end)],fill=FG,width=2)
        x,y=end; self.draw.ellipse((x-4,y-4,x+4,y+4),fill=FG)
        x,y=start; self.draw.ellipse((x-21,y-21,x+21,y+21),fill=FG)
        self.draw.text((x,y-1),str(number),font=ImageFont.truetype(str(FONT),28),fill=BG,anchor='mm')
        self.elements.append(f'<path d="M {start[0]} {start[1]} L {end[0]} {end[1]}" stroke="{FG}" stroke-width="2"/><circle cx="{end[0]}" cy="{end[1]}" r="4" fill="{FG}"/><circle cx="{x}" cy="{y}" r="21" fill="{FG}"/><text x="{x}" y="{y}" fill="{BG}" font-size="28" text-anchor="middle" dominant-baseline="central">{number}</text>')

    def save(self,path,inputs,svg=False):
        final=Image.alpha_composite(self.image.convert('RGBA'),self.overlay).convert('RGB');final.save(path)
        protected=0
        for panel in self.panels:
            source=Image.open(inputs[panel['file']]).convert('RGB').crop(panel['crop'])
            x,y=panel['position'];w,h=panel['size'];actual=final.crop((x,y,x+w,y+h))
            alpha=self.overlay.getchannel('A').crop((x,y,x+w,y+h))
            diff=ImageChops.difference(source,actual);diff.paste((0,0,0),mask=alpha.point(lambda a:255 if a else 0))
            assert diff.getbbox() is None
            protected+=sum(count for count,value in alpha.getcolors(w*h) if value==0)
        if svg:
            path.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.image.width}" height="{self.image.height}" viewBox="0 0 {self.image.width} {self.image.height}"><rect width="100%" height="100%" fill="{BG}"/><g font-family="Noto Sans CJK JP, Noto Sans CJK SC, sans-serif">'+''.join(self.elements)+'</g></svg>')
        return {'file':path.name,'bytes':path.stat().st_size,'sha256':digest(path),'size':list(final.size),
                'panels':self.panels,'texts':self.texts,'sourcePixelsUnchangedOutsideEditorialOverlay':protected}


def run(args):
    assert not args.output.exists()
    receipt=json.loads((args.renders/'reimport-render.json').read_text())
    inputs={};matched=[]
    for row in receipt['views']:
        for key,hashkey in [('file','sha256'),('sourceImage','sourceImageSha256')]:
            path=args.renders/row[key];assert digest(path)==row[hashkey];inputs[path.name]=path
        source=Image.open(inputs[row['sourceImage']]).convert('RGB');export=Image.open(inputs[row['file']]).convert('RGB')
        assert source.size==export.size
        diff=ImageChops.difference(source,export);mean=ImageStat.Stat(diff).mean
        changed=sum(1 for p in diff.getdata() if p!=(0,0,0))
        # Rendering is sampled, not exact identity. This cap is a presentation
        # regression screen, alongside exact decoded geometry and pixel review.
        assert max(mean)<.01 and changed/(source.width*source.height)<.001
        matched.append({'view':row['view'],'identicalRGB':diff.getbbox() is None,'meanAbsoluteRGBDifference0to255':mean,
                        'maximumChannelDifference':max(b for a,b in diff.getextrema()),'changedPixels':changed,
                        'totalPixels':source.width*source.height,'matchingCameraScaleLighting':True})
    args.output.mkdir(parents=True); records=[];leaders=[]
    teaching=Sheet((2120,1790))
    teaching.text((40,28),'Globe & extraocular courses / 眼球外形与眼外肌走行',48)
    teaching.text((40,103),'Each side shown separately · names follow the source / 分侧显示 · 名称沿用来源',29,MUTED)
    for side,x in [('R',40),('L',1080)]:
        view=next(v for v in receipt['views'] if v['view']=='source-'+side+'-oblique')
        teaching.text((x,158),'Source '+side+' · oblique / 来源'+('右' if side=='R' else '左')+' · 斜视',30)
        crop=(0,120,1000,700);xy=(x,210)
        teaching.panel(inputs[view['file']],xy,crop)
        assert view['frameMarginsPx']['top']>crop[1]+40
        assert 900-view['frameMarginsPx']['bottom']<crop[3]-40
        for number,role,start in [(1,'lateral-course',(x+(900 if side=='R' else 100),625)),
                                  (2,'trochlea',(x+(840 if side=='R' else 160),270)),
                                  (3,'optic-segment',(x+(100 if side=='R' else 900),300))]:
            anchor=view['anchors'][role];assert anchor['sourceNode']==anchor['rayHitNode']
            end=(xy[0]+anchor['pixel'][0]-crop[0],xy[1]+anchor['pixel'][1]-crop[1])
            teaching.leader(number,start,end)
            leaders.append({'view':view['view'],'number':number,'role':role,'sourceNode':anchor['sourceNode'],
                            'sourcePixel':anchor['pixel'],'start':list(start),'end':list(end)})
    teaching.text((40,826),'Source R · posterior detail / 来源右 · 后方细节',34)
    detail=next(v for v in receipt['views'] if v['view']=='source-R-posterior')
    crop=(70,40,930,750);xy=(40,892);teaching.panel(inputs[detail['file']],xy,crop)
    for number,role,start in [(1,'lateral-course',(840,1400)),(2,'trochlea',(510,960)),(3,'optic-segment',(70,1090))]:
        a=detail['anchors'][role];end=(xy[0]+a['pixel'][0]-crop[0],xy[1]+a['pixel'][1]-crop[1])
        teaching.leader(number,start,end)
        leaders.append({'view':detail['view'],'number':number,'role':role,'sourceNode':a['sourceNode'],
                        'sourcePixel':a['pixel'],'start':list(start),'end':list(end)})
    teaching.text((980,925),'Follow the same numbers / 循编号对照',36)
    teaching.text((980,1005),'1  Lateral rectus course / 外直肌走行',32)
    teaching.text((980,1054),'Source: Lateral rectus muscle',24,MUTED)
    teaching.text((980,1132),'2  Trochlea & superior-oblique turn',32)
    teaching.text((980,1182),'    滑车与上斜肌转折',32)
    teaching.text((980,1231),'Source: Trochlea of superior oblique muscle',24,MUTED)
    teaching.text((980,1307),'3  Retained optic segment · end shown',32)
    teaching.text((980,1357),'    保留的视神经段 · 标出源端部',32)
    teaching.text((980,1406),'Source: Optic nerve (II)',24,MUTED)
    teaching.text((980,1488),'Segment only; pathway continuity is unverified.',27)
    teaching.text((980,1532),'仅为来源片段；未验证视路连续性。',27)
    teaching.text((40,1642),'20 source surfaces · neutral display materials · source gaps and overlaps retained',28)
    teaching.text((40,1685),'20个来源表面 · 中性显示材质 · 保留源间隙与重叠；不作附着、肌肉动作或眼前段分层展示。',28)
    teaching.text((40,1740),'Z-Anatomy / BodyParts3D · CC BY-SA 4.0 · Exact source names and attribution in the accompanying manifest.',24,MUTED)
    records.append(teaching.save(args.output/'teaching.png',inputs,svg=True))
    ImageOps.grayscale(Image.open(args.output/'teaching.png')).save(args.output/'teaching-grayscale.png')
    for row in receipt['views']:
        pair=Sheet((2120,1140))
        pair.text((40,24),'Native source / 原生来源  →  Export reimport / 导出重载',39)
        pair.text((40,88),row['view']+' · matching camera, scale and neutral display / 同视角、比例及中性显示',28,MUTED)
        pair.text((40,143),'Original source evaluation / 来源求值表面',28)
        pair.text((1080,143),'Updated GLB reimport / GLB重新导入',28)
        pair.panel(inputs[row['sourceImage']],(40,195));pair.panel(inputs[row['file']],(1080,195))
        pair.text((40,1108),'Source-labelled exterior scope; not the old schematic baseline. / 来源命名的外形范围；非原示意模型对照。',23,MUTED)
        records.append(pair.save(args.output/('matched-'+row['view']+'.png'),inputs))
    output={'candidateSha256':receipt['candidateSha256'],'font':{'file':FONT.name,'sha256':digest(FONT)},
            'matchedViews':matched,'leaders':leaders,'sheets':records,
            'otherFiles':[{'file':name,'bytes':(args.output/name).stat().st_size,'sha256':digest(args.output/name)} for name in ('teaching.svg','teaching-grayscale.png')],
            'limits':'Source names/laterality only; static source-preserving display. No anatomy/clinical or browser-runtime certification.'}
    (args.output/'composition.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'matchedViews':matched,'leaders':len(leaders),'sheets':len(records)},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--renders',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args())
