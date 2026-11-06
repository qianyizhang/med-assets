from pathlib import Path
import json,html
D=Path(__file__).parent; A=D/'assets'
A.mkdir(exist_ok=True)
# Shared, deliberately stylized cross-section. No patient measurements.
outer='M -26 30 C -54 -13 -111 0 -119 48 C -128 93 -104 123 -91 145 L -79 255 C -76 285 -56 291 -43 262 L -12 185 C -6 170 6 170 12 185 L 43 262 C 56 291 76 285 79 255 L 91 145 C 104 123 128 93 119 48 C 111 0 54 -13 26 30 Q 0 48 -26 30 Z'
dentin='M -21 54 C -49 17 -87 20 -95 57 C -100 90 -83 118 -68 138 L -58 249 L -25 168 C -13 142 13 142 25 168 L 58 249 L 68 138 C 83 118 100 90 95 57 C 87 20 49 17 21 54 Q 0 67 -21 54 Z'
pulp='M -34 101 C -34 79 -17 72 -8 87 Q 0 99 8 87 C 17 72 34 79 34 101 L 24 133 L 50 228 L 12 149 Q 0 130 -12 149 L -50 228 L -24 133 Z'
lesion='M -27 31 Q 0 48 27 31 L 34 50 Q 22 63 0 67 Q -22 63 -34 50 Z'
cavity='M -31 30 Q 0 46 31 30 L 31 60 Q 0 68 -31 60 Z'
COL={'bg':'#10232c','panel':'#173540','muted':'#a1b6be','text':'#f7f6ee','accent':'#64d8c6','enamel':'#eeeade','dentin':'#d9b883','pulp':'#d77e83','lesion':'#82513b','cavity':'#10232c','restoration':'#a7e4d5','line':'#59757e'}
def wrap(body):return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">'+body+'</svg>'
def write(name,body):(A/(name+'.svg')).write_text(wrap(body))
def tooth(path,fill,stroke='none',sw=0):return f'<g transform="translate(700 144)"><path d="{path}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/></g>'
def text(x,y,s,size=20,color=None,weight=400):return f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" font-weight="{weight}" fill="{color or COL["text"]}">{html.escape(s)}</text>'
write('tooth',tooth(outer,COL['enamel'],'#b7c4c3',2)+tooth(dentin,COL['dentin'])+tooth(pulp,COL['pulp']))
write('lesion',tooth(lesion,COL['lesion']))
write('cavity',tooth(cavity,COL['cavity'],COL['accent'],2))
write('restoration',tooth(cavity,COL['restoration'],COL['accent'],2))
write('focus','<ellipse cx="700" cy="200" rx="57" ry="54" fill="none" stroke="#64d8c6" stroke-width="2" stroke-dasharray="7 6"/>')
base=f'<rect width="960" height="540" fill="{COL["bg"]}"/><rect x="534" y="100" width="350" height="360" rx="24" fill="{COL["panel"]}"/>'
base+=text(56,49,'TOOTH RESTORATION',15,COL['accent'],700)+text(56,508,'SCHEMATIC · PATIENT EDUCATION · NOT A PROCEDURE GUIDE',14,COL['muted'])
base+='<line x1="56" y1="474" x2="904" y2="474" stroke="#36515a"/>'
base+=text(554,127,'ILLUSTRATIVE CROSS-SECTION',14,COL['muted'])
write('base',base)
beats=[{'start':0,'end':3,'title':['A cavity changes','tooth structure'],'subtitle':['A simplified view of localized decay.'],'tag':'01 / UNDERSTAND'}, {'start':3,'end':6,'title':['Assess','and plan'],'subtitle':['Treatment depends on assessment.'],'tag':'02 / ASSESS'}, {'start':6,'end':9,'title':['Prepare','and restore'],'subtitle':['Preparation first. Restoration next.'],'tag':'03 / RESTORE'}, {'start':9,'end':12,'title':['Review','and protect'],'subtitle':['Ongoing care remains important.'],'tag':'04 / FOLLOW UP'}]
for i,b in enumerate(beats):
 s=text(56,124,b['tag'],14,COL['accent'],700)
 for j,line in enumerate(b['title']):s+=text(56,196+j*51,line,39,COL['text'],700)
 for j,line in enumerate(b['subtitle']):s+=text(56,296+j*28,line,17,COL['muted'])
 if i==1:s+=text(56,352,'The pulp stays visible in this schematic.',14,COL['muted'])
 if i==3:
  s+=f'<rect x="56" y="335" width="378" height="80" rx="12" fill="{COL["panel"]}"/>'+text(76,365,'REVIEW + PREVENTION',14,COL['accent'],700)+text(76,391,'Personalized with your dental team.',14,COL['text'])
 write('caption'+str(i),s)
manifest={'title':'Tooth restoration: controlled workflow test','width':960,'height':540,'fps':30,'duration':12,'audio':'none','font':'DejaVu Sans','beats':beats,'assets':{n:f'assets/{n}.svg' for n in ['base','tooth','lesion','cavity','restoration','focus','caption0','caption1','caption2','caption3']},'timing':{'tooth_fade':[0,.65],'lesion_fade':[.5,1],'focus_in':[3,3.4],'focus_out':[5.6,6],'lesion_out':[6,6.35],'cavity_in':[6.35,6.65],'restoration_in':[7.6,8.35],'caption_fades':.35},'safety':'Illustrative shape and sequence only. Not an anatomical model, procedure guide, clinical validation, or representation of every cavity treatment. Colors distinguish states, not a named material.','sources':['https://www.nidcr.nih.gov/health-info/tooth-decay','https://www.fda.gov/medical-devices/dental-amalgam-fillings/treatment-options-dental-caries']}
(D/'storyboard.json').write_text(json.dumps(manifest,indent=2))
print('Built',len(list(A.glob('*.svg'))),'shared layers')
