"""Label actual CPU app renders; not a rendering of the browser interface."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
source=Path(sys.argv[1]);destination=Path(sys.argv[2])
data=json.loads((source/'presentation-frames.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
sheet=Image.new('RGB',(1290,1600),'#10242e');draw=ImageDraw.Draw(sheet)
draw.text((15,15),'FDI31 | actual app CPU pixels: bounded editorial camera + palette',font=font,fill='white')
draw.text((15,43),'Labels composited for review. Not browser screenshots or physical glTF material fidelity.',font=small,fill='#c1d5de')
for i,record in enumerate(data['records']):
 x=15+(i%2)*645;y=85+(i//2)*490
 draw.text((x,y),record['label'],font=small,fill='white')
 im=Image.frombytes('RGBA',(record['width'],record['height']),(source/(record['name']+'.rgba')).read_bytes()).convert('RGB')
 sheet.paste(im,(x,y+25))
draw.text((660,1100),'Original / palette: same camera, source and lighting.',font=small,fill='white')
draw.text((660,1130),'Camera panels intentionally change only the named view.',font=small,fill='white')
draw.text((660,1160),'Reset after playback: exact Original RGBA equality.',font=small,fill='white')
draw.text((660,1190),'Reopen v2 JSON: exact edited RGBA equality.',font=small,fill='white')
draw.text((660,1240),'Prepared T2 specimen; not healthy anatomy.',font=small,fill='#f2c0ad')
draw.text((660,1270),'No clinical, bite, registration or browser approval.',font=small,fill='#f2c0ad')
draw.text((15,1570),'SWIRendo / Benz, Heck & Walter (2024) · CC BY-SA 4.0 · doi:10.5282/ubm/data.477',font=small,fill='#c1d5de')
destination.parent.mkdir(parents=True,exist_ok=True);sheet.save(destination,quality=94)
