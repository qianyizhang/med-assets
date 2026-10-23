import vtk,json,pathlib,hashlib,numpy as np
from vtk.util.numpy_support import vtk_to_numpy
D=pathlib.Path(__file__).resolve().parent.parent/'replay-reference';D.mkdir(exist_ok=False);p=D.parent/'sources/BMLPL_001_REF_17_SEG_SUB.nii'
r=vtk.vtkNIFTIImageReader();r.SetFileName(str(p));r.Update();im=r.GetOutput();a=vtk_to_numpy(im.GetPointData().GetScalars());vals,c=np.unique(a,return_counts=True);print('dims spacing values',im.GetDimensions(),im.GetSpacing(),vals,c)
assert len(vals)==2
mc=vtk.vtkFlyingEdges3D();mc.SetInputData(im);mc.SetValue(0,float(vals.mean()));mc.ComputeNormalsOn();mc.Update();surf=mc.GetOutput()
w=vtk.vtkPLYWriter();w.SetFileName(str(D/'measured-reference-unsmoothed.ply'));w.SetInputData(surf);w.SetFileTypeToBinary();w.Write()
h=r.GetNIFTIHeader();info={'sourceFile':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'vtkVersion':vtk.vtkVersion.GetVTKVersion(),'dimensions':im.GetDimensions(),'spacingHeader':im.GetSpacing(),'values':vals.tolist(),'counts':c.tolist(),'niftiXYZTUnits':h.GetXYZTUnits(),'description':h.GetDescrip(),'sformCode':h.GetSFormCode(),'qformCode':h.GetQFormCode(),'method':'vtkFlyingEdges3D at midpoint of two segmentation labels; no smoothing, no decimation, no filling crop boundaries','surfacePoints':surf.GetNumberOfPoints(),'surfacePolygons':surf.GetNumberOfPolys(),'surfaceBoundsHeaderUnits':surf.GetBounds(),'referenceOnly':True,'notEstablished':'Bone site, donor age/health, registration to BP3D femur; not marrow tissue segmentation'}
(D/'extraction.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))
