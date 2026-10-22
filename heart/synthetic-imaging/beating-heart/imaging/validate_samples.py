"""Round-trip structural checks without third-party medical file dependencies."""
from pathlib import Path
import gzip,json,struct,sys
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parent))
import heart_geometry as hg
from occupancy import sample_labels
meta=json.loads((ROOT/'metadata.json').read_text());npz=np.load(ROOT/'synthetic_volumes.npz');shape=tuple(meta['shape_ijk']);A=np.array(meta['voxel_center_to_RAS_mm'])
checks={}
for name,key in [('structure_labels','labels'),('ct_like_arbitrary_contrast','ct_like'),('mri_like_bright_blood','mri_like')]:
    b=gzip.decompress((ROOT/f'{name}.nii.gz').read_bytes());typ=struct.unpack_from('<h',b,70)[0];dt='u1' if typ==2 else '<f4';dims=struct.unpack_from('<8h',b,40)
    assert dims[0]==3 and tuple(dims[1:4])==shape
    B=np.eye(4)
    for row in range(3):B[row]=struct.unpack_from('<4f',b,280+row*16)
    assert np.allclose(A,B) and b[123]==2 and b[344:348]==b'n+1\0'
    arr=np.frombuffer(b,dt,offset=352).reshape(shape,order='F');assert np.array_equal(arr,npz[key]);assert np.isfinite(arr).all()
    h,data=(ROOT/f'{name}.nrrd').read_bytes().split(b'\n\n',1);nr=np.frombuffer(gzip.decompress(data),dt).reshape(shape,order='F');assert np.array_equal(nr,arr)
    checks[name]='NIfTI/NRRD/NPZ round-trip equal; correct shape, RAS affine, mm units; finite'
labels=npz['labels'];raw=np.fromfile(ROOT/'web/labels.uint8.raw',dtype='u1').reshape(shape,order='F');assert np.array_equal(raw,labels)
rng=np.random.default_rng(44);idx=np.stack([rng.integers(0,n,10000) for n in shape]);ras=A[:3,:3]@idx+A[:3,3,None];expected=sample_labels(-ras[0]/25,-ras[1]/25,ras[2]/25);actual=labels[tuple(idx)]
assert np.array_equal(expected,actual);checks['registration']='10,000 random voxel centers agree exactly with shared-derived geometry occupancy; web labels byte-identical'
checks['boundary']='Foreground touches voxel bounds: '+str(any(np.any(np.take(labels,i,axis=ax)) for ax in range(3) for i in (0,-1)))
import itertools
x=np.arange(shape[0])[:,None,None]+A[0,3];y=np.arange(shape[1])[None,:,None]+A[1,3];z=np.arange(shape[2])[None,None,:]+A[2,3]
pools={k:hg.inside(-x/25,-y/25,z/25,c['inner']) for k,c in hg.CHAMBERS.items()}
checks['analytical_pool_overlap_voxels']={a+'_'+b:int((pools[a]&pools[b]).sum()) for a,b in itertools.combinations(pools,2)}
checks['RV_pool_intersection_LV_outer_envelope_voxels']=int((pools['RV']&hg.inside(-x/25,-y/25,z/25,hg.CHAMBERS['LV']['outer'])).sum())
(ROOT/'validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
