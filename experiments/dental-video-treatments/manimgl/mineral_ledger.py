"""The Mineral Ledger. Authored native vector scene, original ManimGL 1.7.2."""
from manimlib import *
import math
import os
BG='#101a2a'; WHITE='#eef5ec'; TEAL='#62e5c1'; CORAL='#ff7768'; BLUE='#87bff5'; GOLD='#f1c779'; MUTED='#9cabbd'; INK='#18293c'
def p(x,y):return np.array([x,y,0.])
def txt(s,x,y,size=30,col=WHITE):return Text(s,font='DejaVu Sans',font_size=size,color=col).move_to(p(x,y))
def ln(a,b,c=MUTED,w=2):return Line(p(*a),p(*b),stroke_color=c,stroke_width=w)
def smooth(a):return a*a*(3-2*a)
def ramp(t,a,b):return np.clip((t-a)/(b-a),0,1)
def tooth(x=0,y=0,scale=1):
    pts=[(-1.35,1.45),(-1.18,2),(-.55,2.05),(0,1.8),(.55,2.05),(1.18,2),(1.35,1.45),(1.12,.1),(.8,-1.55),(.45,-2.05),(.15,-.45),(0,-.2),(-.15,-.45),(-.45,-2.05),(-.8,-1.55),(-1.12,.1),(-1.35,1.45)]
    def layer(s,c):
        q=VMobject().set_points_smoothly([p(a*s,b*s) for a,b in pts]);q.set_fill(c,1).set_stroke(c,2);return q
    outer=layer(1,WHITE);inner=layer(.8,GOLD);pulp=layer(.43,CORAL)
    return VGroup(outer,inner,pulp).scale(scale).move_to(p(x,y))
def tilefield(x,y,cols=14,rows=5):
    g=VGroup()
    for r in range(rows):
      for c in range(cols):
        g.add(RoundedRectangle(width=.48,height=.37,corner_radius=.055,fill_color=WHITE,fill_opacity=1,stroke_color=BLUE,stroke_width=1).move_to(p(x+(c-(cols-1)/2)*.52,y-r*.41)))
    return g

def bacteria(x,y,s=1):
    body=RoundedRectangle(width=.8,height=.34,corner_radius=.16,fill_color=GOLD,fill_opacity=1,stroke_color=GOLD).rotate(.3)
    g=VGroup(body,Dot(p(-.18,0),radius=.035,color=INK),Dot(p(.15,.04),radius=.035,color=INK))
    for i in [-1,0,1]:g.add(ln((i*.25,-.17),(i*.25-.08,-.3),GOLD,2),ln((i*.25,.18),(i*.25+.08,.3),GOLD,2))
    return g.scale(s).move_to(p(x,y))
def arrow(a,b,c=TEAL):return Arrow(p(*a),p(*b),buff=0,stroke_color=c,stroke_width=3)
def mirror(x,y,s=1):
    return VGroup(ln((-.05,-1),(.5,.2),BLUE,12),Circle(radius=.58,fill_color=INK,fill_opacity=1,stroke_color=BLUE,stroke_width=7).move_to(p(.65,.6)),Arc(start_angle=.3,angle=1.6,radius=.38,stroke_color=WHITE,stroke_width=2).shift(p(.65,.6))).scale(s).move_to(p(x,y))
def brush(x,y,s=1):
    g=VGroup(RoundedRectangle(width=2.7,height=.23,corner_radius=.1,fill_color=TEAL,fill_opacity=1,stroke_width=0),RoundedRectangle(width=.9,height=.35,corner_radius=.1,fill_color=TEAL,fill_opacity=1,stroke_width=0).move_to(p(1.25,0)))
    for i in range(8):g.add(ln((.9+i*.1,.14),(.9+i*.1,.6),WHITE,5))
    return g.scale(s).move_to(p(x,y))

class MineralLedger(Scene):
 def construct(self):
    shots=[];motion=[]
    # Continuous spatial chapter map, 15 world units apart.
    for i in range(6):
      g=VGroup();shots.append(g)
      g.add(txt(['01 / BEFORE THE HOLE','02 / THE ACID LOOP','03 / A WINDOW TO REPAIR','04 / WHEN THE SURFACE BREAKS','05 / ASSESS, THEN RESTORE','06 / CHANGE THE DAILY BALANCE'][i],0,2.9,22,TEAL))
    g=shots[0]
    g.add(txt('THE MINERAL LEDGER',0,2.18,37),txt('Loss and recovery are happening at the surface.',0,-2.7,23,MUTED))
    t0=tooth(-2,-.2,.82);g.add(t0)
    lens=Circle(radius=.64,stroke_color=TEAL,stroke_width=3).move_to(p(-1.62,1.01));g.add(lens)
    g.add(ln((-1.1,1.35),(1.15,1.15),TEAL),ln((-1.05,.7),(1.15,-.75),TEAL))
    zoom=tilefield(3.1,.9,7,4);g.add(zoom)
    g.add(txt('ENAMEL',3.1,-1,22,BLUE),txt('MINERAL OUT',1.75,-1.65,19,CORAL),txt('MINERAL IN',4.4,-1.65,19,TEAL))
    for j in range(8):
      dot=Dot(radius=.065,color=CORAL if j<4 else TEAL);g.add(dot)
      motion.append((0,lambda t,d=dot,j=j:d.move_to(p(1.6+(j%4)*.95,-.15+math.sin(t*1.1+j)*.55))))
    motion.append((0,lambda t:lens.scale(1+.0015*math.sin(t*2))))
    # 2: sugar feeding plaque, then acid stripping mineral tiles.
    g=shots[1];g.add(txt('Sugar → plaque bacteria → acid',0,2.15,32))
    field=tilefield(0,-.15,18,5);g.add(field)
    g.add(RoundedRectangle(width=9.5,height=.6,corner_radius=.2,fill_color=GOLD,fill_opacity=.13,stroke_width=0).move_to(p(0,.78)))
    for j in range(7):
      bug=bacteria(-3.7+j*1.2,.85,.73);g.add(bug)
      motion.append((1,lambda t,b=bug,x=-3.7+j*1.2,j=j:b.move_to(p(x+.12*math.sin(t*2+j),.85+.06*math.sin(t*3+j)))))
    g.add(txt('PLAQUE',-5.25,.75,18,GOLD),txt('ENAMEL',-5.25,-1.05,18,BLUE),txt('Repeated acid exposure can sustain mineral loss.',0,-2.65,23,MUTED))
    for j in range(10):
      cube=Square(side_length=.14,fill_color=GOLD,fill_opacity=1,stroke_width=0);g.add(cube)
      motion.append((1,lambda t,d=cube,j=j:d.move_to(p(-4+j*.9,1.8-((t*.55+j*.17)%1.1))).rotate(.015)))
      acid=Dot(radius=.055,color=CORAL);g.add(acid)
      motion.append((1,lambda t,d=acid,j=j:d.move_to(p(-3.8+j*.82,.6-((t*.65+j*.23)%.9)))))
    for j in [3,6,10,13,16,23,29,32,43,47]:
      obj=field[j];base=obj.get_center().copy()
      motion.append((1,lambda t,o=obj,b=base,j=j:o.move_to(b+p(.12*math.sin(t*2+j),ramp(t,2+j%3,6)*1.45)).set_opacity(1-.8*ramp(t,2+j%3,6))))
    # 3: reverse flow without promising all lesions heal.
    g=shots[2];g.add(txt('Before a cavity: recovery is possible',0,2.15,32))
    recover=tilefield(0,-.15,18,5);g.add(recover)
    g.add(txt('SALIVA',-3.5,1.35,23,BLUE),txt('FLUORIDE',3.5,1.35,23,TEAL),txt('Early decay may stop or reverse.',0,-2.65,26,TEAL))
    g.add(arrow((-3.5,1),(-2.5,.15),BLUE),arrow((3.5,1),(2.5,.15),TEAL))
    for j in range(18):
      dot=Dot(radius=.06,color=TEAL if j%2 else BLUE);g.add(dot)
      motion.append((2,lambda t,d=dot,j=j:d.move_to(p(-4.2+j*.49,1.15-((t*.6+j*.16)%1.4)))))
    for j in [3,6,10,13,16,23,29,32,43,47]:
      obj=recover[j];base=obj.get_center().copy()
      motion.append((2,lambda t,o=obj,b=base,j=j:o.move_to(b+p(0,(1-ramp(t,1+j%3,6))*.85)).set_fill(interpolate_color(BLUE,WHITE,ramp(t,1+j%3,6))).set_opacity(.25+.75*ramp(t,1+j%3,6))))
    g.add(txt('MINERALS RETURN TO ENAMEL',0,-2.2,16,BLUE))
    # 4: intact surface breaks, no operative technique depicted.
    g=shots[3];g.add(txt('A hole changes what comes next',0,2.15,32))
    breach=tilefield(0,.45,18,6);g.add(breach)
    for j in list(range(6,12))+list(range(25,29))+list(range(44,46)):
      obj=breach[j];base=obj.get_center().copy()
      motion.append((3,lambda t,o=obj,b=base,j=j:o.move_to(b+p(.22*math.sin(j),-1.2*ramp(t,.3+j%3*.3,2.6))).set_opacity(1-ramp(t,1,3))))
    g.add(arrow((0,1.3),(0,.65),CORAL),txt('SURFACE BREAKDOWN',0,1.55,21,CORAL))
    g.add(txt('Formed cavity → dental assessment',0,-2.65,28,CORAL))
    for x in [-4.7,4.7]:g.add(ln((x,.5),(x,-1.9),BLUE))
    # 5: tool guides assessment, conditional restoration branches.
    g=shots[4];g.add(txt('Treatment follows assessment',0,2.15,32))
    cross=tooth(-3.4,-.2,.84);g.add(cross)
    hole=Polygon(p(-3.85,1.31),p(-2.95,1.31),p(-3.09,.65),p(-3.67,.65),fill_color=BG,fill_opacity=1,stroke_color=CORAL,stroke_width=2);g.add(hole)
    mir=mirror(-5.1,.1,.8);g.add(mir);motion.append((4,lambda t:mir.move_to(p(-5.05+.14*math.sin(t),.15+.15*math.sin(t*.8)))))
    g.add(arrow((-1.9,.8),(-.7,.8),BLUE),txt('DENTAL\nASSESSMENT',.75,.8,24,BLUE))
    g.add(arrow((2.1,.8),(3.1,1.1),TEAL),arrow((2.1,.5),(3.1,-.65),MUTED))
    g.add(txt('A filling',4.1,1.2,29,TEAL),txt('One common option',4.1,.65,19,MUTED),txt('Other treatment',4.15,-.65,25),txt('As clinically appropriate',4.15,-1.17,18,MUTED))
    fill=hole.copy().set_fill(TEAL,1).set_stroke(TEAL,1);g.add(fill);motion.append((4,lambda t:fill.set_opacity(ramp(t,4.5,6.5))))
    g.add(txt('Restore damaged structure. Keep preventing new decay.',0,-2.65,22,MUTED))
    # 6: props converge on one intact surface, not a slide of headings.
    g=shots[5];g.add(txt('Small habits. A different balance.',0,2.15,34))
    small=tooth(0,-.15,.68);g.add(small)
    br=brush(-3.6,.65,.76).rotate(.25);g.add(br);motion.append((5,lambda t:br.move_to(p(-3.6+.16*math.sin(t*4),.65+.05*math.sin(t*4)))))
    g.add(txt('FLUORIDE TOOTHPASTE',-3.65,-.25,17,TEAL),txt('Twice daily',-3.65,-.72,25))
    spool=VGroup(RoundedRectangle(width=.85,height=.75,corner_radius=.14,fill_color=BLUE,fill_opacity=1,stroke_width=0),Circle(radius=.17,stroke_color=INK,stroke_width=3),Arc(start_angle=0,angle=PI,radius=.4,stroke_color=WHITE,stroke_width=3).shift(p(.45,.55))).move_to(p(3.55,.7));g.add(spool)
    floss=VMobject().set_points_smoothly([p(2.9,.9),p(2.5,.2),p(2.8,-.15),p(3.2,.3)]).set_stroke(WHITE,3);g.add(floss)
    g.add(txt('BETWEEN TEETH',3.65,-.25,18,BLUE),txt('Clean regularly',3.65,-.72,25))
    g.add(mirror(0,-2.1,.34),txt('Regular dental review',0,-2.85,25,TEAL))
    g.add(arrow((-2,-.4),(-1,-.4),TEAL),arrow((2,-.4),(1,-.4),BLUE))
    for j in range(16):
      d=Dot(radius=.035,color=TEAL);g.add(d)
      motion.append((5,lambda t,d=d,j=j:d.move_to(p(1.4*math.cos(j*TAU/16+t*.15),.1+1.65*math.sin(j*TAU/16+t*.15)))))
    # Background grid travels with the actual camera, making the continuous journey explicit.
    grid=VGroup()
    for x in range(-9,85,2):grid.add(ln((x,-4),(x,4),'#1d2b3d',.5))
    for y in range(-4,5,2):grid.add(ln((-9,y),(85,y),'#1d2b3d',.5))
    self.add(grid)
    for i,g in enumerate(shots):g.shift(RIGHT*15*i);self.add(g)
    # Motion functions use local coordinates. Keep each chapter local while applying world offset afterward.
    footer=txt('SCHEMATIC • NOT TO SCALE • EDUCATIONAL, NOT INDIVIDUAL ADVICE',0,-3.66,12,MUTED).fix_in_frame()
    line=ln((-6.5,-3.32),(6.5,-3.32),'#334154',2).fix_in_frame();progress=ln((-6.5,-3.32),(-6.49,-3.32),TEAL,3).fix_in_frame()
    brand=txt('FIELD NOTES / ORAL HEALTH',-4.91,3.55,13,MUTED).fix_in_frame()
    self.add(line,progress,footer,brand)
    starts=[0,6,14,23,31,40]; ends=[6,14,23,31,40,48]
    frame=self.camera.frame
    start=float(os.getenv("LEDGER_START", "0"));duration=float(os.getenv("LEDGER_DURATION", "48"))
    def update(_,alpha):
      t=min(47.999,max(0,start+alpha*duration-1/30));idx=max(i for i,s in enumerate(starts) if t>=s)
      travel=smooth(ramp(t,ends[idx]-.7,ends[idx])) if idx<5 else 0
      frame.move_to(p((idx+travel)*15,0))
      for i,g in enumerate(shots):
        # Restore local coordinates before updating native geometry.
        active=i==idx or (i==idx+1 and travel>0)
        # Camera framing alone controls visibility; preserve native fill/stroke opacities.
        if active:
          g.shift(LEFT*15*i)
          lt=max(0,t-starts[i])
          for si,fn in motion:
            if si==i:fn(lt)
          g.shift(RIGHT*15*i)
      progress.set_points_as_corners([p(-6.5,-3.32),p(-6.5+13*t/48,-3.32)])
    tracker=ValueTracker(0);update(tracker,0)
    self.play(UpdateFromAlphaFunc(tracker,update),run_time=duration,rate_func=linear)
