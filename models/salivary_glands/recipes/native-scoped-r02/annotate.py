from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--renders',required=True);p.add_argument('--baseline-renders');p.add_argument('--out',required=True);a=p.parse_args();R=Path(a.renders);B=Path(a.baseline_renders) if a.baseline_renders else None;O=Path(a.out);assert {x['glb_sha256'] for x in json.loads((R/'bindings.json').read_text())}=={'a53134ec91195f5c42b8be4cde3536343e62857a7ecf5ab5d11bf3eba6ead515', '1764c63011e698b9047d1abe79c647b8b609b7d8f9b18b740b17cdc65db930f8'},'Render model bindings mismatch';assert not O.exists(),'Output file must be new';im=Image.new('RGB',(1700,1120),'#13171c');d=ImageDraw.Draw(im);f=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
d.text((25,20),'Major gland envelopes + selected duct course / 主要腺体外形与选定导管走行',font=f(29),fill='#eee');d.text((25,68),'BOTH submandibular ducts excluded / 两侧下颌下腺导管均已排除',font=f(24),fill='#f3b853')
im.paste(Image.open(R/'glands-ducts-front-source.png').convert('RGB').resize((900,900)),(0,120));im.paste(Image.open(R/'context-side-source.png').convert('RGB').resize((580,580)),(1080,410))
def line(pt,anchor,en,zh):
 d.line((pt,anchor),fill='#cad2dc',width=2);d.ellipse((pt[0]-4,pt[1]-4,pt[0]+4,pt[1]+4),fill='#cad2dc');d.text((anchor[0]+12,anchor[1]-20),en,font=f(23),fill='#eee');d.text((anchor[0]+12,anchor[1]+15),zh,font=f(21),fill='#b6c0cb')
line((200,500),(950,175),'Parotid pair + parotid ducts','双侧腮腺与腮腺导管')
line((300,730),(950,255),'Submandibular gland pair','双侧下颌下腺：仅外形与定位')
line((380,755),(950,335),'Sublingual gland pair','双侧舌下腺：无小导管模型')
d.text((1090,1000),'Source jaw/muscle context / 源颌骨与肌肉参照',font=f(20),fill='#b6c0cb')
d.text((25,1030),'Not complete anatomy: no outlet/lumen validation. Empty sockets are source context, not dental reconstruction. Original still needs revision.',font=f(20),fill='#f3b853');d.text((25,1068),'不是完整唾液腺解剖：未验证口内开口或管腔；空牙槽为源参照，不是牙科模型。原草稿仍需修改。',font=f(21),fill='#f3b853')
im.save(O)
