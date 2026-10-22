"""Small portable volume writers; no medical-imaging package required."""
import gzip, struct
from pathlib import Path
import numpy as np

def write_nifti(path, data, affine):
    """NIfTI-1 single-file little-endian; data index order (i,j,k), RAS mm sform."""
    data=np.asarray(data)
    if data.dtype==np.uint8: code,bits,dt=2,8,'u1'
    else: code,bits,dt=16,32,'<f4'
    h=bytearray(352)
    struct.pack_into('<i',h,0,348)
    struct.pack_into('<8h',h,40,data.ndim,*data.shape,*([1]*(7-data.ndim)))
    struct.pack_into('<hh',h,70,code,bits)
    spacing=np.linalg.norm(np.asarray(affine)[:3,:3],axis=0)
    struct.pack_into('<8f',h,76,1,*spacing,*([1]*4))
    struct.pack_into('<f',h,108,352)
    struct.pack_into('<f',h,112,1)
    h[123]=2 # spatial units mm
    desc=b'SYNTHETIC teaching geometry; arbitrary intensity; not clinical'
    h[148:148+len(desc)]=desc
    struct.pack_into('<hh',h,252,0,2) # no qform; aligned anatomical (synthetic model) sform
    for row in range(3):struct.pack_into('<4f',h,280+16*row,*affine[row])
    h[344:348]=b'n+1\0'
    with gzip.open(path,'wb') as f:f.write(h);f.write(data.astype(dt).tobytes(order='F'))

def write_nrrd(path,data,affine):
    data=np.asarray(data);dt='uint8' if data.dtype==np.uint8 else 'float'
    directions=' '.join('('+','.join(str(float(v)) for v in affine[:3,j])+')' for j in range(3))
    origin='('+','.join(str(float(v)) for v in affine[:3,3])+')'
    head=f'NRRD0005\n# SYNTHETIC teaching example, not acquired imaging\ntype: {dt}\ndimension: 3\nspace: right-anterior-superior\nsizes: '+ ' '.join(map(str,data.shape))+f'\nspace directions: {directions}\nkinds: domain domain domain\nendian: little\nencoding: gzip\nspace units: "mm" "mm" "mm"\nspace origin: {origin}\n\n'
    raw=data.astype('u1' if dt=='uint8' else '<f4').tobytes(order='F')
    Path(path).write_bytes(head.encode()+gzip.compress(raw))
