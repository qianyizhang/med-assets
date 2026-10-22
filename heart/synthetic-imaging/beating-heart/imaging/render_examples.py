"""Reproducible spatial reslicing and arbitrary teaching contrast presets."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter, distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

DISCLAIMER='SYNTHETIC TEACHING EXAMPLE • not acquired imaging • not a validated scanner simulation'
COLORS=['#070d18','#ed655a','#488dd4','#ef9390','#7bbae8','#a94748','#355f91','#ad6d70','#507c9e','#db8e92','#efd494','#ed655a','#488dd4','#7bbae8','#ef9390']

def normalize(x):return np.asarray(x,float)/np.linalg.norm(x)

def render_all(out,labels,ct,mri,affine,definitions,lv_apex,lv_base):
    out=Path(out); out.mkdir(exist_ok=True)
    lv_apex=np.array(lv_apex);lv_base=np.array(lv_base)
    mid=(lv_apex+lv_base)/2
    axis=normalize(lv_base-lv_apex)
    # Projection of patient-right onto plane perpendicular to LV long axis.
    short_u=normalize(np.array([1,0,0])-axis*axis[0]);short_v=normalize(np.cross(axis,short_u))
    long_u=short_u;long_v=axis
    planes=[('Patient axial',mid,[1,0,0],[0,1,0],110),('Patient coronal',mid,[1,0,0],[0,0,1],145),('Patient sagittal',mid,[0,1,0],[0,0,1],145),('LV oblique long axis*',mid,long_u,long_v,145),('LV mid short axis*',mid,short_u,short_v,95),('LV apical short axis*',lv_apex+.28*(lv_base-lv_apex),short_u,short_v,85)]
    inv=np.linalg.inv(affine)
    plane_meta=[]
    def reslice(volume,center,u,v,width,n=240,order=1):
        s=np.linspace(-width/2,width/2,n); xx,yy=np.meshgrid(s,s)
        xyz=np.asarray(center)[:,None,None]+np.asarray(u)[:,None,None]*xx+np.asarray(v)[:,None,None]*yy
        ijk=np.einsum('ij,jhw->ihw',inv[:3,:3],xyz)+inv[:3,3,None,None]
        return map_coordinates(volume,ijk,order=order,mode='constant',cval=0),s
    def direction(vec):
        vec=np.asarray(vec); pairs=[('L','R'),('P','A'),('I','S')]
        return ''.join(pairs[j][int(vec[j]>0)] for j in np.argsort(-abs(vec)) if abs(vec[j])>.2)
    def setup(fig,axes,title):
        fig.patch.set_facecolor('#0b1424');fig.suptitle(title,color='white',fontsize=20,y=.98)
        fig.text(.5,.925,DISCLAIMER,ha='center',color='#ffc477',fontsize=10)
        fig.text(.5,.045,'Frame 1 / reference end-diastole • RAS world coordinates in mm • arbitrary contrast units',ha='center',color='#b4c7d9',fontsize=10)
        fig.text(.5,.018,'*LV-relative illustrative planes; not prescribed clinical 2CH/4CH acquisitions. No patient torso is modeled.',ha='center',color='#9aaec4',fontsize=9)
    for mode,vol in [('CT',ct),('MRI',mri),('Labels',labels)]:
        fig,axes=plt.subplots(2,3,figsize=(13.8,9.2));setup(fig,axes, {'CT':'CT-like contrast preset | matched geometry','MRI':'MRI-like bright-blood preset | matched geometry','Labels':'Structure-label reslices | exact same planes'}[mode])
        for ax,(title,center,u,v,width) in zip(axes.flat,planes):
            arr,s=reslice(vol,center,u,v,width,order=0 if mode=='Labels' else 1)
            args=dict(cmap=ListedColormap(COLORS),norm=BoundaryNorm(np.arange(-.5,len(COLORS)+.5),len(COLORS))) if mode=='Labels' else dict(cmap='gray',vmin=0,vmax=1)
            ax.imshow(arr,origin='lower',extent=[s[0],s[-1],s[0],s[-1]],**args)
            ax.set_title(title,color='white',fontsize=12);ax.set_facecolor('#070d18');ax.set_xticks([]);ax.set_yticks([])
            for x,y,t in [(.03,.5,direction(-np.array(u))),(.97,.5,direction(u)),(.5,.97,direction(v)),(.5,.03,direction(-np.array(v)))]:ax.text(x,y,t,transform=ax.transAxes,ha='center',va='center',color='#71d5f8',fontsize=10)
            if mode=='Labels':
                for ident,d in definitions.items():
                    ident=int(ident);pix=np.argwhere(arr==ident)
                    if len(pix)>50 and d.get('class')=='blood_pool':
                        iy,ix=np.unravel_index(np.argmax(distance_transform_edt(arr==ident)),arr.shape);iy=int(np.clip(iy,12,len(s)-13));ix=int(np.clip(ix,12,len(s)-13));ax.text(s[ix],s[iy],d.get('short',d['name']),ha='center',fontsize=8,color='white',bbox=dict(facecolor='black',alpha=.6,pad=2,edgecolor='none'))
        plt.subplots_adjust(left=.03,right=.97,top=.88,bottom=.085,hspace=.17,wspace=.08)
        fig.savefig(out/f'{mode.lower()}_orthogonal_and_cardiac_planes.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(14,5.6));fig.patch.set_facecolor('#0b1424')
    fig.suptitle('One slice. The same two pumping chambers.',color='white',fontsize=23,y=.98)
    fig.text(.5,.89,'Color identifies the anatomy. Grayscale presets show how the same shape can be displayed.',ha='center',color='#b4c7d9',fontsize=12)
    for ax,vol,title in zip(axs,[ct,labels,mri],['CT-like teaching contrast','Anatomy color guide','MRI-like teaching contrast']):
        arr,s=reslice(vol,mid,[1,0,0],[0,1,0],105,order=0 if vol is labels else 1)
        kw=dict(cmap=ListedColormap(COLORS),norm=BoundaryNorm(np.arange(-.5,len(COLORS)+.5),len(COLORS))) if vol is labels else dict(cmap='gray',vmin=0,vmax=1)
        ax.imshow(arr,origin='lower',**kw);ax.set_title(title,color='white',fontsize=13);ax.axis('off')
        if vol is labels:
            for ident,text in [(1,'Left ventricle'),(2,'Right ventricle')]:
                iy,ix=np.unravel_index(np.argmax(distance_transform_edt(arr==ident)),arr.shape);ax.text(ix,iy,text,ha='center',color='white',fontsize=8,bbox=dict(facecolor='black',alpha=.6,edgecolor='none',pad=2))
    fig.text(.5,.10,'The ring is muscle wall. The middle is the space containing blood. Patient left appears on image left here.',ha='center',color='#b4c7d9',fontsize=10)
    fig.text(.5,.035,DISCLAIMER,ha='center',color='#ffc477',fontsize=9)
    plt.subplots_adjust(left=.025,right=.975,top=.80,bottom=.15,wspace=.08)
    fig.savefig(out/'start_here_same_slice.png',dpi=150,facecolor=fig.get_facecolor())
    for ax in axs:ax.invert_xaxis()
    for text in fig.texts:
        if 'Patient left appears' in text.get_text():text.set_text('The ring is muscle wall. The middle contains blood. Radiological display: patient right is on image left.')
    fig.savefig(out/'start_here_radiological_display.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
    for title,c,u,v,w in planes:plane_meta.append(dict(name=title,center_RAS_mm=np.asarray(c).tolist(),horizontal_positive_RAS=np.asarray(u).tolist(),vertical_positive_RAS=np.asarray(v).tolist(),field_width_mm=w,pixels=240,pixel_center_convention='linspace(-width/2,+width/2,240); bottom row negative v; PNG origin displayed lower'))
    # US-style fan is an explicit geometric sampling plane, no wave propagation.
    width=130;n=360;xx,zz=np.meshgrid(np.linspace(-65,65,n),np.linspace(0,135,n))
    probe=lv_apex-18*axis
    xyz=probe[:,None,None]+long_u[:,None,None]*xx+axis[:,None,None]*zz
    ijk=np.einsum('ij,jhw->ihw',inv[:3,:3],xyz)+inv[:3,3,None,None]
    tissue=map_coordinates(labels.astype(float),ijk,order=0,mode='constant',cval=0).astype(np.uint8)
    dist=np.hypot(xx,zz);sector=(abs(np.arctan2(xx,zz+1e-9))<=np.deg2rad(45))&(dist<=130)&(dist>=5)
    tissue_mask=tissue>0
    # Boundary emphasis and smoothed random texture are graphic effects only.
    boundary=np.hypot(*np.gradient(tissue_mask.astype(float)))
    blood_ids=[int(k) for k,d in definitions.items() if d.get('class')=='blood_pool']
    blood=np.isin(tissue,blood_ids)
    rng=np.random.default_rng(2031);texture=gaussian_filter(rng.rayleigh(.35,tissue.shape),.6)
    us=np.clip((.035+.37*tissue_mask-.33*blood+.48*gaussian_filter(boundary,.65))*texture*2,0,1)
    us=np.where(sector,us,np.nan)
    fig,ax=plt.subplots(figsize=(10,9));fig.patch.set_facecolor('#0b1424');ax.set_facecolor('#0b1424')
    ax.imshow(us,cmap='gray',vmin=0,vmax=1,extent=[-65,65,135,0]);ax.set_title('Ultrasound-style fan | geometric plane demonstration',color='white',fontsize=16,pad=40)
    ax.set_xlabel('Lateral distance in prescribed plane (mm)',color='white');ax.set_ylabel('Distance along plane from virtual apex-side probe (mm)',color='white');ax.tick_params(colors='#b4c7d9')
    fig.text(.5,.9,DISCLAIMER,ha='center',color='#ffc477',fontsize=8)
    fig.text(.5,.025,'Stylized boundary/texture contrast only. Not an echocardiogram; no acoustics, Doppler or tissue motion inferred.',ha='center',color='#b4c7d9',fontsize=8)
    fig.subplots_adjust(bottom=.14)
    fig.savefig(out/'ultrasound_style_fan.png',dpi=150,facecolor=fig.get_facecolor())
    overlay=np.where(sector & (tissue>0),tissue,np.nan)
    ax.imshow(overlay,cmap=ListedColormap(COLORS),norm=BoundaryNorm(np.arange(-.5,len(COLORS)+.5),len(COLORS)),alpha=.48,extent=[-65,65,135,0])
    for ident,d in definitions.items():
        mask=(tissue==int(ident))&sector
        if d.get('class')=='blood_pool' and mask.sum()>100:
            iy,ix=np.unravel_index(np.argmax(distance_transform_edt(mask)),mask.shape)
            ax.text(-65+130*ix/(n-1),135*iy/(n-1),d['short'],color='white',ha='center',bbox=dict(facecolor='black',alpha=.7,edgecolor='none',pad=2))
    ax.set_title('Same ultrasound-style fan | structure-color guide',color='white',fontsize=16,pad=40)
    fig.savefig(out/'ultrasound_labeled_fan.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
    plane_meta.append(dict(name='Ultrasound-style geometric fan',virtual_probe_RAS_mm=probe.tolist(),horizontal_positive_RAS=long_u.tolist(),depth_positive_RAS=axis.tolist(),sector_half_angle_degrees=45,max_radius_mm=130,pixels=[360,360],display_vertical='depth increases downward',physics_simulated=False))
    (out/'slice_planes.json').write_text(json.dumps(plane_meta,indent=2))
    return plane_meta
