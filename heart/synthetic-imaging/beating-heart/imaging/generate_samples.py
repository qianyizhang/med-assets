#!/usr/bin/env python3
"""Generate registered synthetic labels/intensity examples from exact shared heart geometry.
Run from any directory: python imaging/generate_samples.py
Dependencies: Python, numpy, scipy, matplotlib. No patient data or imaging simulator.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.ndimage import gaussian_filter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import heart_geometry as hg
from occupancy import sample_labels
from volume_io import write_nifti,write_nrrd
from render_examples import render_all
OUT=ROOT/'imaging'; WEB=OUT/'web';WEB.mkdir(exist_ok=True)
# 1 mm isotropic voxels covering the entire stylized heart and great-vessel field.
origin=np.array([-80.,-80.,-70.]);shape=(161,161,181);spacing=1.
affine=np.eye(4);affine[:3,:3]*=spacing;affine[:3,3]=origin
x=origin[0]+np.arange(shape[0])[:,None,None];y=origin[1]+np.arange(shape[1])[None,:,None];z=origin[2]+np.arange(shape[2])[None,None,:]
labels=sample_labels(-x/25,-y/25,z/25)
# Shared occupancy is authoritative; never construct a separate lookalike heart.
spec=json.loads((ROOT/'geometry_spec.json').read_text())
short={1:'LV',2:'RV',3:'LA',4:'RA',5:'LV wall',6:'RV wall',7:'LA wall',8:'RA wall',9:'V septum',10:'A septum',11:'Aorta',12:'PA',13:'VC',14:'PV'}
definitions={str(k):{'name':v,'short':short[int(k)],'class':'blood_pool' if int(k) in (1,2,3,4,11,12,13,14) else 'wall'} for k,v in spec['labels'].items()}
ct_lut=np.array([0,.82,.82,.82,.82,.43,.43,.43,.43,.43,.43,.82,.82,.82,.82],np.float32)
mri_lut=np.array([0,.91,.91,.91,.91,.29,.29,.29,.29,.29,.29,.91,.91,.91,.91],np.float32)
ct=gaussian_filter(ct_lut[labels],.55).astype(np.float32);mri=gaussian_filter(mri_lut[labels],.9).astype(np.float32)
# Presets deliberately avoid noise that could look like acquired scanner evidence.
for name,arr in [('structure_labels',labels),('ct_like_arbitrary_contrast',ct),('mri_like_bright_blood',mri)]:
    write_nifti(OUT/f'{name}.nii.gz',arr,affine)
    write_nrrd(OUT/f'{name}.nrrd',arr,affine)
np.savez_compressed(OUT/'synthetic_volumes.npz',labels=labels,ct_like=ct,mri_like=mri,voxel_to_RAS_mm=affine)
for name,arr in [('labels',labels),('ct',np.rint(ct*255).astype(np.uint8)),('mri',np.rint(mri*255).astype(np.uint8))]:
    # X is fastest, same ordering as NIfTI/NRRD and JS i + nx*(j+ny*k).
    (WEB/f'{name}.uint8.raw').write_bytes(arr.tobytes(order='F'))
params=hg.CHAMBERS['LV']['inner'];lv_apex=np.array(hg.point(params,0,0))*[-25,-25,25];lv_base=np.array(hg.point(params,1,0))*[-25,-25,25]
counts={str(k):int((labels==k).sum()) for k in np.unique(labels)}
meta={'status':'SYNTHETIC ILLUSTRATIVE ONLY; not acquired CT/MRI/US, not a validated scanner simulation','source':'../heart_geometry.py exact analytic chambers and curved ventricular septum, plus ellipsoid atrial septum; ../vessel_geometry.json centerline tube approximation. Vessel cross-section transport/curvature and voxelization can differ near edges.','source_sha256':hashlib.sha256((ROOT/'heart_geometry.py').read_bytes()).hexdigest(),'vessel_sha256':hashlib.sha256((ROOT/'vessel_geometry.json').read_bytes()).hexdigest() if (ROOT/'vessel_geometry.json').exists() else None,'shape_ijk':shape,'spacing_mm':[1,1,1],'voxel_center_to_RAS_mm':affine.tolist(),'Blender_to_RAS_mm':spec['coordinates']['RAS_mm_from_blender'],'array_axis_order':['R+','A+','S+'],'raw_storage':'uint8; i fastest; index=i+nx*(j+ny*k); length=nx*ny*nz bytes','raw_files':{'labels':'labels.uint8.raw','ct':'ct.uint8.raw','mri':'mri.uint8.raw'},'phase':{'frame':1,'name':'reference end-diastole'},'labels':definitions,'present_label_voxel_counts':counts,'absent_defined_labels':[int(k) for k in definitions if k not in counts],'intensity':{'units':'arbitrary normalized teaching units [0,1]; web uint8 is value*255','ct_like_LUT':ct_lut.tolist(),'mri_like_LUT':mri_lut.tolist(),'gaussian_sigma_voxels':{'ct':.55,'mri':.9},'physics':'none; no HU, T1/T2, pulse sequence, X-ray projection/reconstruction or acoustic propagation'},'LV_apex_RAS_mm':lv_apex.tolist(),'LV_base_RAS_mm':lv_base.tolist(),'registration':'Identity in model RAS reference space only. Not registration to any patient or real scan. Real data requires its own affine, segmentation and phase-aware registration.'}
(OUT/'metadata.json').write_text(json.dumps(meta,indent=2));(WEB/'manifest.json').write_text(json.dumps(meta,indent=2))
render_all(OUT,labels,ct,mri,affine,definitions,lv_apex,lv_base)
print(json.dumps({'shape':shape,'counts':counts,'out':str(OUT)},indent=2))
