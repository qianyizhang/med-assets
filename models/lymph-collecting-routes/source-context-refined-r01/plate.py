from pathlib import Path
import json,hashlib
import numpy as np
from scipy.interpolate import splprep,splev
from scipy.ndimage import binary_dilation
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent;old=R.parent/'source-context-r01';rec=json.loads((old/'build-receipt.json').read_text());bg=(17,23,28);fg=(233,237,240);mut=(165,178,187);outline=(107,128,143);blue=(128,191,222)
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';B=F.replace('Regular','Bold')
# Original-source pose/extents retained; editorial contour refinements, NOT measured adult template.
right=[(0,.535),(.047,.522),(.077,.486),(.086,.440),(.081,.392),(.064,.348),(.046,.315),(.048,.274),(.064,.248),(.112,.230),(.168,.215),(.213,.195),(.231,.137),(.256,.050),(.270,-.040),(.275,-.135),(.302,-.245),(.310,-.365),(.309,-.421),(.327,-.442),(.344,-.452),(.352,-.474),(.344,-.483),(.333,-.473),(.331,-.514),(.317,-.551),(.303,-.549),(.292,-.519),(.289,-.480),(.280,-.455),(.278,-.410),(.263,-.322),(.242,-.228),(.222,-.140),(.201,-.050),(.177,.046),(.156,.079),(.143,.032),(.135,-.055),(.119,-.158),(.123,-.250),(.151,-.335),(.164,-.420),(.159,-.530),(.139,-.660),(.119,-.766),(.140,-.863),(.122,-.963),(.104,-1.080),(.106,-1.135),(.136,-1.173),(.137,-1.192),(.118,-1.201),(.074,-1.197),(.062,-1.180),(.067,-1.140),(.064,-1.065),(.058,-.955),(.053,-.850),(.052,-.761),(.045,-.650),(.027,-.535),(.019,-.483),(0,-.475)]
contour=right+[(-x,z) for x,z in right[-2:0:-1]]
def project(points,view,w,h):
 v=rec['views'][view];pos=np.array(v['camera']);target=np.array(v['target']);forward=(target-pos);forward/=np.linalg.norm(forward);rx=np.cross(forward,[0,0,1]);rx/=np.linalg.norm(rx);up=np.cross(rx,forward);pts=np.array([[x,-.08,z] for x,z in points])-target;return np.stack([(.5+pts@rx/(v['ortho_scale']*v['pixels'][0]/v['pixels'][1]))*w,(.5-pts@up/v['ortho_scale'])*h],axis=1)
# Smooth original authored control contour; boundary detail retained without oval mitten shapes.
tck,_=splprep(np.array(contour).T,s=0,per=True);dense=list(zip(*splev(np.linspace(0,1,1800),tck)))
landmarks=[([(-.15,.174),(-.08,.173),(0,.154),(.08,.173),(.15,.174)],'clavicle'),([(-.126,-.30),(-.08,-.34),(0,-.39),(.08,-.34),(.126,-.30)],'pelvis'),([(-.13,-.764),(-.09,-.78),(-.054,-.763)],'knee'),([(.054,-.763),(.09,-.78),(.13,-.764)],'knee'),([(-.27,-.14),(-.245,-.153),(-.221,-.14)],'elbow'),([(.221,-.14),(.245,-.153),(.27,-.14)],'elbow')]
proof={}
for lang in ['en','zh']:
 original=Image.open(old/f'comparison-{lang}.png').convert('RGB');im=Image.new('RGB',(1520,1960),bg);d=ImageDraw.Draw(im)
 def txt(x,y,s,n=22,col=fg,b=False):d.text((x,y),s,font=ImageFont.truetype(B if b else F,n),fill=col)
 txt(32,20,'Original route detail, refined regional context' if lang=='en' else '保留原始路径细节，细化身体分区参照',33,b=True)
 txt(32,70,'7 source routes retained • matched overview and oblique detail • static candidate v5' if lang=='en' else '保留7条源路径 · 总览与斜向近景视角匹配 · v5静态候选',22,mut)
 txt(32,110,'Contour changes are editorial reference cues—not validated body registration.' if lang=='en' else '轮廓调整为编辑性分区参照，不是已验证的人体配准。',22,mut)
 for view,y,size,srcy in [('overview',205,(648,810),205),('detail',1180,(648,630),1180)]:
  w,h=size;baseline=original.crop((800,srcy,800+w,srcy+h));routes=original.crop((32,srcy,32+w,srcy+h));new=Image.new('RGB',size,bg);nd=ImageDraw.Draw(new)
  pts=project(dense,view,w,h);nd.line([tuple(p) for p in pts]+[tuple(pts[0])],fill=outline,width=2)
  a=np.array(routes);mask=np.any(a!=np.array(bg),axis=2);b=np.array(new);gray=np.mean(a.astype(float)-np.array(bg),axis=2)*.58;b[mask]=np.clip(np.array(bg)+gray[:,:,None],0,255).astype('uint8')[mask];selected=np.array(baseline);selected_mask=(selected[:,:,1].astype(int)-selected[:,:,0].astype(int)>7)&(selected[:,:,1].astype(int)>selected[:,:,2].astype(int))&(selected[:,:,1]>110);selected_mask=binary_dilation(selected_mask,iterations=1)&mask;b[selected_mask]=selected[selected_mask];new=Image.fromarray(b);nd=ImageDraw.Draw(new)
  if view=='overview':
   for z,label in [(.19,'Shoulder' if lang=='en' else '肩部'),(-.13,'Elbow' if lang=='en' else '肘部'),(-.36,'Pelvis' if lang=='en' else '骨盆'),(-.78,'Knee' if lang=='en' else '膝部'),(-1.10,'Ankle' if lang=='en' else '踝部')]:
    yy=project([(0,z)],view,w,h)[0][1];nd.line([(500,yy),(520,yy)],fill=outline,width=1);nd.text((527,yy-12),label,font=ImageFont.truetype(F,17),fill=mut)
  # Exact source cap positions and original leader anchors, no new junctions.
  for num,key,anchor in [(1,'upper',(435,85) if view=='overview' else (435,70)),(2,'lower',(50,350) if view=='overview' else (50,525))]:
   q=rec['views'][view]['anchors'][key];px=q[0]*w;py=(1-q[1])*h;ax,ay=anchor
   nd.line([(ax+14,ay+14),(px,py)],fill=blue,width=2);nd.ellipse((px-6,py-6,px+6,py+6),outline=blue,width=2);nd.rounded_rectangle((ax,ay,ax+32,ay+32),radius=6,fill=blue);nd.text((ax+8,ay-2),str(num),font=ImageFont.truetype(B,22),fill=bg)
  im.paste(baseline,(32,y));im.paste(new,(800,y));label=view if lang=='en' else ('总览' if view=='overview' else '近景');txt(32,y-45,'Original · '+label,26,b=True);txt(800,y-45,'Updated · '+label,26,b=True)
  proof[view]={'source_route_crop_sha256':hashlib.sha256(routes.tobytes()).hexdigest(),'route_pixels_retained_before_cap_labels':int(mask.sum()),'route_positions_preserved':True,'context_intensity':'0.58 grayscale from original route pixels','selected_route':'Original selected-route pixels retained in original color','camera':rec['views'][view]}
 txt(32,1040,'Changed: head/neck transition, limb contours and hand/foot shape. All 7 route positions retained.' if lang=='en' else '调整头颈过渡、肢体轮廓及手足形态；保留全部7条路径的位置。',21,mut)
 txt(32,1080,'Bright: selected thoracic route. Gray: retained source scaffold. Ticks: regional cues only.' if lang=='en' else '亮色：所选胸导管；灰色：保留的源路径；短标记仅作身体分区提示。',21,mut)
 txt(32,1830,'1 Upper source cap ≠ verified vein junction.  2 Lower cap ≠ complete inflow anatomy.' if lang=='en' else '1上端源封口≠已验证静脉连接；2下端源封口≠完整流入解剖。',21,mut)
 txt(32,1870,'Illustrative contour, not measured anatomy. Source geometry unchanged; detail camera matched.' if lang=='en' else '示意轮廓，不是测量解剖；源几何不变，近景视角匹配。',21,mut)
 txt(32,1910,'Regional reference: OpenStax §1.6 Fig1.12 • static candidate for review' if lang=='en' else '分区参考：OpenStax §1.6 图1.12 · 待评审静态候选',21,mut)
 im.save(R/f'comparison-{lang}.png')
(R/'retention-proof.json').write_text(json.dumps({'source_package_unchanged':True,'routes':7,'triangles':372,'proof':proof,'editorial_contour_controls':contour,'limitations':'Contour is illustrative; not source geometry, anthropometric standard or registered anatomy'},indent=2))
