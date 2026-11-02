from pathlib import Path
if not __debug__: raise RuntimeError('Optimized Python is unsupported; integrity assertions are required')
import json,base64,hashlib,html,subprocess,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
parser=argparse.ArgumentParser();parser.add_argument('--render-dir',required=True);args=parser.parse_args();P=Path(args.render_dir).resolve()
if any(P.glob('comparison-*')):raise ValueError('Comparison output exists; preserve previous draft')
receipt=json.loads((P/'render-receipt.json').read_text())
if receipt['sourceSha256']!='4e2637cf6c844aef85ab77c2c1049d4e7647348a13c34d784795b98825f7c8c7':raise ValueError('Wrong source receipt')
if hashlib.sha256((P/'camera-source.json').read_bytes()).hexdigest()!='671e6c4db4791e76cef0960f0f3c85864f9a37ed2b73ac1636f93854d9bde064':raise ValueError('Wrong camera contract')
for name,sha in receipt['renderedFileHashes'].items():
 if hashlib.sha256((P/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed render input')
names=[('Gastric surface','胃面','FMA:15837'),('Diaphragmatic surface','膈面','FMA:15828'),('Colic surface','结肠面','FMA:15838'),('Hilum','脾门','UBERON:0001248'),('Renal surface','肾面','FMA:15839')]
views=[('Source oblique','来源斜视'),('Derived opposite view','派生反向视图'),('Source lower view','来源下方视图')]
records=[]
for v in range(3):
 a=np.asarray(Image.open(P/f'view-{v}-ids.png').convert('RGB')); rec=[]
 for j,r in enumerate([114,156,188,213,235]):
  mask=(np.abs(a[:,:,0].astype(float)-r)<3)&(a[:,:,1]<3)&(a[:,:,2]<3);d=distance_transform_edt(mask);y,x=np.unravel_index(d.argmax(),d.shape)
  rec.append({'number':j+1,'label':names[j][0],'sourceId':names[j][2],'visiblePixels':int(mask.sum()),'interiorRadius':float(d.max()),'anchor':[int(x),int(y)],'marked':bool(d.max()>=15)})
 records.append(rec)
 uri='data:image/png;base64,'+base64.b64encode((P/f'view-{v}-original.png').read_bytes()).decode()
 for lang in ['en','zh']:
  zh=lang=='zh'; title='脾脏：来源表面定位' if zh else 'Spleen · source-surface locator'
  H=1440 if v==0 else 1130
  s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1980" height="{H}" viewBox="0 0 1980 {H}"><rect width="1980" height="{H}" fill="#11161d"/><g font-family="DejaVu Sans,Noto Sans CJK SC,sans-serif" fill="#e8edf2">']
  def text(x,y,t,size=24,color='#e8edf2'):s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(t)}</text>')
  text(28,48,title,34);text(28,86,views[v][1 if zh else 0]+' · '+('相同几何、材质、相机与光照' if zh else 'Same geometry, materials, camera and lighting'),23,'#b9c4cf')
  text(28,130,'Original / 原始 r03 重渲染' if zh else 'Original · unchanged r03 rerender',27);text(792,130,'Updated / 更新' if zh else 'Updated',27)
  for x in [28,792]:s.append(f'<image href="{uri}" x="{x}" y="150" width="720" height="720"/>')
  if v==0:
   for xx in [28,792]:
    s.append(f'<rect x="{xx+380}" y="580" width="220" height="250" fill="none" stroke="#111" stroke-width="4"/><rect x="{xx+380}" y="580" width="220" height="250" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="9 5"/>')
    text(xx+380,572,'细节 A' if zh else 'Detail A',19,'#111')
  for r in rec:
   if not r['marked']:continue
   x,y=r['anchor'];x+=792;y+=150;s.append(f'<circle cx="{x}" cy="{y}" r="12" fill="#fff" stroke="#111" stroke-width="2"/><text x="{x}" y="{y+5}" text-anchor="middle" font-size="16" font-weight="bold" fill="#111">{r["number"]}</text>')
  text(1540,150,'来源标签 / Source key' if zh else 'Source labels',26)
  for j,r in enumerate(rec):
   y=205+j*125;text(1540,y,f'{j+1}. '+names[j][1 if zh else 0],24)
   if zh:text(1570,y+30,names[j][0],18,'#b9c4cf')
   text(1570,y+56,names[j][2],17,'#a6b2be')
   status=('本视图已定位' if zh else 'Located in this view') if r['marked'] else ('此视图未标记；参见其他视图' if zh else 'Unmarked here; see other views')
   text(1570,y+80,status,17,'#b9c4cf')
  if v==0:
   text(28,914,'细节 A · 同一图像裁切，编号位置不变' if zh else 'Detail A · matched exact crop, unchanged marker positions',26)
   for xx in [180,730]:
    s.append(f'<defs><clipPath id="crop{xx}"><rect x="{xx}" y="945" width="308" height="350"/></clipPath></defs><g clip-path="url(#crop{xx})"><g transform="translate({xx-532} 343) scale(1.4)"><image href="{uri}" width="720" height="720"/>')
    if xx==730:
     for r in rec:
      if r['marked']:
       x,y=r['anchor'];s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#fff" stroke="#111" stroke-width="1.5"/><text x="{x}" y="{y+4}" text-anchor="middle" font-size="12" font-weight="bold" fill="#111">{r["number"]}</text>')
    s.append('</g></g>')
   text(180,1320,'Original / 原始' if zh else 'Original',22);text(730,1320,'Updated / 更新' if zh else 'Updated',22)
   text(1130,1040,'窄区域 2、3、5 的放大定位' if zh else 'Closer view of narrow patches 2, 3 and 5',24)
   text(1130,1130,'此视图 1、4 较宽；2、3、5 只露出窄区域。' if zh else 'Here 1 and 4 are broad; 2, 3 and 5 are narrow.',22,'#b9c4cf')
   text(1130,1080,'不是新增剖面或重塑几何。' if zh else 'No cutaway or geometry reshaping.',22,'#b9c4cf')
  else:
   text(28,960,'Original 是未改变的 r03 在统一光照下重新渲染；不是历史原图。' if zh else 'Original is unchanged r03 freshly rendered under matched lighting—not the historical PNG.',23)
  if v!=0:
   takeaway=('此视图主要展示 2；其他区域转到斜视或下方视图定位。' if zh else 'Notice: 2 dominates this view; locate the other patches in the oblique/lower views.') if v==1 else ('此视图让 5 更明显；与斜视中的同号区域对应。' if zh else 'Notice: 5 is broader here; match its number to the narrow patch in the oblique view.')
   text(28,1005,takeaway,23)
  text(28,1360 if v==0 else 1055,'编号锚点位于可见的来源表面；小到无法清晰标记的区域不作隐藏定位。' if zh else 'Numbers anchor to visible source surfaces. Hidden or tiny patches are not labeled through the organ.',23)
  text(28,1393 if v==0 else 1088,'来源命名不等于边界解剖验证；不含内部红白髓或血管。原始外观接受范围不变。' if zh else 'Source annotations, not validated anatomical boundaries. No internal pulp or vessels; original exterior acceptance is unchanged.',21,'#b9c4cf')
  text(28,1425 if v==0 else 1118,'HRA Female v1.10 · Kristen Browne / Heidi Schlehlein · CC BY 4.0 · Added locator labels / 新增定位标签',18,'#8d9baa')
  s.append('</g></svg>');out=P/f'comparison-{v}-{lang}.svg';out.write_text(''.join(s));subprocess.run(['inkscape',str(out),'--export-type=png','--export-filename='+str(out.with_suffix('.png'))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
(P/'anchors.json').write_text(json.dumps(records,indent=2));assert set(r['number'] for rs in records for r in rs if r['marked'])==set(range(1,6))
print('All 5 source patches have >=15px visible-interior anchor coverage; 6 matched bilingual comparison panels generated.')
