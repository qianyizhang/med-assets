from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--renders',required=True);p.add_argument('--baseline-renders');p.add_argument('--out',required=True);a=p.parse_args();R=Path(a.renders);B=Path(a.baseline_renders) if a.baseline_renders else None;O=Path(a.out);assert json.loads((R/'bindings.json').read_text())['original_context_sha256']=='8026bc00d8e19ac1b15d0c24375111f058a9bb182fc172fa1d30b1f6cb9e265c','Diagnostic source binding mismatch';assert not O.exists(),'Output file must be new';im=Image.new('RGB',(1500,1040),'#13171c');d=ImageDraw.Draw(im);f=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
d.text((25,18),'Excluded, not repaired / 排除展示，并未修补源模型',font=f(31),fill='#f3b853');d.text((25,68),'Left submandibular duct crosses the modeled mylohyoid / 左侧下颌下腺导管穿过模型下颌舌骨肌',font=f(23),fill='#e6e9ed')
for i,(name,label) in enumerate([('opaque-oblique','Opaque muscle / 不透明肌肉表面'),('translucent-oblique','Diagnostic transparency / 诊断用透明显示')]):
 x=25+i*750;d.text((x,115),label,font=f(22),fill='#e6e9ed');im.paste(Image.open(R/f'{name}.png').convert('RGB').resize((700,700)),(x,155))
for y,s in [(880,'Gold = source duct; muted pink = source muscle. Geometry unchanged; colors/transparency are diagnostic.'),(915,'金色为源导管，灰粉色为源肌肉。未改动几何；颜色与透明度仅用于显示问题。'),(950,'BOTH submandibular ducts withheld; no complete route, lumen or clinical validation.'),(985,'两侧下颌下腺导管均暂不纳入；不宣称完整走行、管腔或临床验证。')]:d.text((25,y),s,font=f(21),fill='#f3b853' if y>=950 else '#c6ced6')
im.save(O)
