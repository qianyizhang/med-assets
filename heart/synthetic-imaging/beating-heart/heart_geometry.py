"""Shared exact analytic chamber shells. Coordinates: BU=25 mm, +X left,+Y posterior,+Z superior.
Occupancy matches cross-sectional mesh surface except polygon discretization.
"""
import math
CHAMBERS={
 'LV': {'label_pool':1,'label_wall':5,'color':(0.66,0.055,0.075), 'inner':(-2.02,.94,.86,.43,-.18,.20,.65,.50,.56,1.0), 'outer':(-2.30,1.08,.86,.43,-.18,.20,.93,.77,.56,1.0)},
 'RV': {'label_pool':2,'label_wall':6,'color':(0.035,.24,.62), 'inner':{'type':'crescent','z0':-1.78,'z1':1.08,'width':.30,'span':1.57}, 'outer':{'type':'crescent','z0':-1.96,'z1':1.19,'width':.43,'span':1.67}},
 'LA': {'label_pool':3,'label_wall':7,'color':(.86,.16,.19), 'inner':(.70,2.02,.58,.45,.56,.63,.69,.56,.51,1.0), 'outer':(.62,2.10,.58,.45,.56,.63,.78,.65,.51,1.0)},
 'RA': {'label_pool':4,'label_wall':8,'color':(.07,.43,.74), 'inner':(.63,2.10,-.95,-1.00,-.02,.08,.61,.59,.53,1.0), 'outer':(.54,2.19,-.95,-1.00,-.02,.08,.70,.68,.53,1.0)},
}
def crescent_section(params,t):
 z=params['z0']+(params['z1']-params['z0'])*t
 # RV wraps the right/anterior LV free-wall in an elliptical polar crescent.
 lt=max(.015,min(.985,(z+2.30)/3.38));lvshape=math.sin(math.pi*lt)**.56
 cx=.86+(.43-.86)*lt;cy=-.18+(.20+.18)*lt
 s=max(0.,math.sin(math.pi*t))**.56
 return cx,cy,z,1.21*lvshape+.05,params['width']*s,params['span']*s

def cross_section(params,t):
 z0,z1,x0,x1,y0,y1,rx,ry,power,right=params
 s=max(0.,math.sin(math.pi*t))**power
 return x0+(x1-x0)*t,y0+(y1-y0)*t,z0+(z1-z0)*t,rx*s,ry*s,right

def point(params,t,theta):
 if isinstance(params,dict):
  cx,cy,z,mid,width,span=crescent_section(params,t)
  angle=math.radians(225)+span*math.cos(theta)
  r=mid-.35*(max(0.,math.sin(math.pi*t))**.56)*(math.cos(theta)**2)-width*math.sin(theta)
  return cx+r*math.cos(angle),cy+.88*r*math.sin(angle),z
 cx,cy,z,rx,ry,r=cross_section(params,t)
 co=math.cos(theta)
 return (cx+rx*co*(r if co>0 else 1),cy+ry*math.sin(theta),z)

def inside(x,y,z,params):
 """Numpy-broadcast-compatible exact point-in-volume predicate."""
 import numpy as np
 if isinstance(params,dict):
  t=(z-params['z0'])/(params['z1']-params['z0']);tc=np.clip(t,1e-8,1-1e-8)
  lt=np.clip((z+2.30)/3.38,.015,.985);lvshape=np.sin(np.pi*lt)**.56
  cx=.86+(.43-.86)*lt;cy=-.18+(.20+.18)*lt
  s=np.sin(np.pi*tc)**.56;mid=1.21*lvshape+.05;width=params['width']*s;span=params['span']*s
  xx=x-cx;yy=(y-cy)/.88;r=np.sqrt(xx*xx+yy*yy)
  a=(np.arctan2(yy,xx)-np.deg2rad(225)+np.pi)%(2*np.pi)-np.pi
  mid=mid-.35*s*(a/span)**2
  return (t>=0)&(t<=1)&((a/span)**2+((r-mid)/width)**2<=1)
 z0,z1,x0,x1,y0,y1,rx,ry,power,right=params
 t=(z-z0)/(z1-z0); tc=np.clip(t,1e-8,1.-1e-8)
 s=np.sin(np.pi*tc)**power
 xx=x-(x0+(x1-x0)*t); yy=y-(y0+(y1-y0)*t)
 xx=xx/(rx*s*np.where(xx>0,right,1.))
 yy=yy/(ry*s)
 return (t>=0)&(t<=1)&((xx*xx+yy*yy)<=1)

SEPTUM={'z0':-1.75,'z1':.85,'theta0':math.radians(135),'theta1':math.radians(297)}
def septum_inside(x,y,z):
 import numpy as np
 outer=CHAMBERS['LV']['outer'];t=(z-outer[0])/(outer[1]-outer[0]);cx=outer[2]+(outer[3]-outer[2])*t;cy=outer[4]+(outer[5]-outer[4])*t
 # Elliptical angular coordinate matches point() for both nested LV surfaces;
 # use outer radial axes to classify the shared muscular septal sector.
 angle=np.arctan2((y-cy)/outer[7],(x-cx)/outer[6])%(2*np.pi)
 return inside(x,y,z,outer)&~inside(x,y,z,CHAMBERS['LV']['inner'])&(z>=SEPTUM['z0'])&(z<=SEPTUM['z1'])&(angle>=SEPTUM['theta0'])&(angle<=SEPTUM['theta1'])

def occupancy_labels(x,y,z):
 import numpy as np
 labels=np.zeros(np.broadcast(x,y,z).shape,np.uint8)
 for name in ('LA','RA','LV','RV'):
  c=CHAMBERS[name]; labels[inside(x,y,z,c['outer'])]=c['label_wall']
 labels[septum_inside(x,y,z)]=9
 for name in ('LA','RA','LV','RV'):
  c=CHAMBERS[name]; labels[inside(x,y,z,c['inner'])]=c['label_pool']
 return labels
