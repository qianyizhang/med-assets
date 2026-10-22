"""Shared-model image occupancy: exact analytic chambers/curved ventricular septum and ellipsoid atrial septum, centerline tube approximation.
Vessel lumen voxelization uses nearest piecewise-linear centerline and interpolated radius.
Native tubes use transported cross-section rings: curvature/tips can differ slightly.
"""
from pathlib import Path
import json,numpy as np
import heart_geometry as hg
ROOT=Path(__file__).resolve().parents[1]
def sample_labels(x,y,z):
    x,y,z=np.broadcast_arrays(x,y,z);labels=hg.occupancy_labels(x,y,z)
    for ident,c,s in [(10,(-.22,.40,1.35),(.10,.48,.57))]:
        mask=((x-c[0])/s[0])**2+((y-c[1])/s[1])**2+((z-c[2])/s[2])**2<=1
        labels[mask & ~np.isin(labels,[1,2,3,4])]=ident
    if (ROOT/'vessel_geometry.json').exists():
        for vessel in json.loads((ROOT/'vessel_geometry.json').read_text()):
            pts=np.array(vessel['sampled_centerline_BU']);rmax=pts[:,3].max()
            roi=(x>=pts[:,0].min()-rmax)&(x<=pts[:,0].max()+rmax)&(y>=pts[:,1].min()-rmax)&(y<=pts[:,1].max()+rmax)&(z>=pts[:,2].min()-rmax)&(z<=pts[:,2].max()+rmax)
            q=np.stack([x[roi],y[roi],z[roi]],axis=1);inside=np.zeros(len(q),bool)
            for a,b in zip(pts[:-1],pts[1:]):
                d=b[:3]-a[:3];den=d@d
                if den<1e-12:continue
                t=np.clip((q-a[:3])@d/den,0,1);nearest=a[:3]+t[:,None]*d;rad=a[3]+t*(b[3]-a[3]);inside|=np.sum((q-nearest)**2,axis=1)<=rad**2
            # Clip endpoint hemispheres by terminal ring planes.
            inside&=((q-pts[0,:3])@(pts[1,:3]-pts[0,:3])>=0)
            inside&=((q-pts[-1,:3])@(pts[-1,:3]-pts[-2,:3])<=0)
            region=labels[roi];region[inside & ~np.isin(region,[1,2,3,4])]=int(vessel['label']);labels[roi]=region
    return labels
