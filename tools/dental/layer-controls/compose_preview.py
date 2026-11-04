from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
D=Path(__file__).resolve().parent;O=D/'output';j=json.loads((O/'preview-frames.json').read_text());frames=[]
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def text(d,xy,s,size=15,fill='#b7cbd4',strong=False):d.text(xy,s,font=ImageFont.truetype(bold if strong else font,size),fill=fill)
for r in j['records']:
 im=Image.new('RGB',(1000,650),'#10242e');d=ImageDraw.Draw(im);d.rounded_rectangle((24,94,664,550),20,fill='#1b3643');d.rounded_rectangle((685,94,978,550),20,fill='#142c37',outline='#3c5b68')
 pix=Image.frombytes('RGBA',(r['width'],r['height']),(O/f"pixels-{r['index']}.rgba").read_bytes());im.paste(pix,(29,100),pix);d=ImageDraw.Draw(im)
 text(d,(30,22),'DENTAL / REUSABLE CONTROL STUDY',12,'#79ddd0');text(d,(30,48),'Reveal a layer. Keep the context.',29,'#ecf4ef',True)
 text(d,(705,118),'Editorial separation',16,'#eaf4f0',True);text(d,(705,148),str(round(r['reveal']*100))+'%',15,'#79ddd0')
 d.line((710,184,952,184),fill='#42606e',width=5);d.line((710,184,710+242*r['reveal'],184),fill='#79ddd0',width=5);x=710+242*r['reveal'];d.ellipse((x-7,177,x+7,191),fill='#79ddd0')
 text(d,(705,214),'Isolate a source label',16,'#eaf4f0',True)
 for i,(name,c) in enumerate([('enamel','#e0dfc9'),('dentin','#d3a850'),('pulp','#de527e'),('bone','#739194')]):
  x=705+(i%2)*128;y=252+(i//2)*52;sel=r.get('isolate')==name;d.rounded_rectangle((x,y,x+118,y+41),7,fill='#24594f' if sel else '#213f4b',outline='#7bded2' if sel else '#476673');d.ellipse((x+10,y+17,x+17,y+24),fill=c);text(d,(x+24,y+12),name.title(),12,'#edf4ef')
 selection=r.get('isolate');text(d,(705,374),selection.title()+' isolated' if selection else 'All four layers visible',15,'#eaf4f0',True);text(d,(705,401),'Other layers hidden' if selection else 'Source-labelled geometry',13)
 text(d,(705,455),'Fixed camera, unchanged mesh',12,'#7dd3ca');text(d,(705,484),'Prepared T2 specimen.',12);text(d,(705,505),'No clinical validation.',12,'#edc27a')
 text(d,(38,522),f"{r['triangles']:,} source triangles",11,'#98b7c6')
 desc='Reset: source pose, all layers visible' if r['name']=='reset' else 'Show all: separation preserved' if r['name']=='all' else 'Isolate '+selection+' without reframing' if selection else 'Source pose' if not r['reveal'] else 'Editorial separation, not tissue motion'
 text(d,(30,575),desc,18,'#ecf4ef',True)
 text(d,(30,612),'Actual parser + controller + CPU renderer. Browser interaction QA pending.',12,'#9fb9c7')
 frames.append(im)
 if r['name'] in ['source','separated','enamel','dentin','pulp','bone','reset']:im.save(O/('control-'+r['name']+'.jpg'),quality=92)
frames[0].save(O/'FDI31-reveal-isolate-reset.gif',save_all=True,append_images=frames[1:],duration=[r['hold'] for r in j['records']],loop=0,optimize=True)
print(O/'FDI31-reveal-isolate-reset.gif')
