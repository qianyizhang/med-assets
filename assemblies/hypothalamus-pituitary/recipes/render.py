"""Matched clean-reimport Cycles views; offline pixels only, not browser evidence."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(paths):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for path in paths:bpy.ops.import_scene.gltf(filepath=str(path))
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH':
            for f in ob.data.polygons:f.use_smooth=True
def mat(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.68;return m
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if a.out.exists():raise FileExistsError('Use new render directory')
    a.out.mkdir(parents=True)
    sources=[a.root/'models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb',a.root/'models/pituitary/exports/source-candidate-01/pituitary_source_frame.glb']
    views={'whole':{'target':[-.00065,-.103,1.5375],'offset':[.055,-.10,.030],'scale':.037},'junction':{'target':[-.00065,-.106,1.5339],'offset':[.055,-.10,.015],'scale':.0115},'junction-side':{'target':[-.00065,-.106,1.5339],'offset':[.11,-.018,.008],'scale':.0115}}
    bindings=[]
    for label,paths in [('original',sources),('updated',[a.candidate])]:
        if label=='original' and not a.baseline:continue
        load(paths)
        if label=='original':
            for ob in bpy.context.scene.objects:
                if ob.type=='MESH':
                    color=(.22,.49,.50) if 'pituitary' in ob.name else (.59,.29,.27)
                    ob.data.materials.clear();ob.data.materials.append(mat(ob.name+' illustrative',color))
        for name,cfg in views.items():
            for ob in list(bpy.context.scene.objects):
                if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
            target=Vector(cfg['target'])
            for off,energy,size in [((.05,-.06,.07),.25,.06),((-.06,-.02,.02),.125,.07),((.02,.05,.05),.1875,.05)]:
                bpy.ops.object.light_add(type='AREA',location=target+Vector(off));lamp=bpy.context.object;lamp.data.energy=energy;lamp.data.size=size;lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
            bpy.ops.object.camera_add(location=target+Vector(cfg['offset']));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=cfg['scale'];cam.data.clip_start=.001;cam.data.clip_end=10
            s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.film_transparent=False;s.world.color=(.18,.18,.18);s.view_settings.view_transform='AgX'
            path=a.out/(label+'-'+name+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
            bindings.append({'file':path.name,'sha256':digest(path),'bytes':path.stat().st_size,'artifacts':[{'file':p.name,'sha256':digest(p)} for p in paths],'camera':list(cam.location),'target':cfg['target'],'orthoscale':cfg['scale'],'pixels':[900,1000],'samples':32,'note':'Clean GLB reimport. Original source colors matched; inferred junction amber appears only on derivative. Offline Cycles, not browser screenshot.'})
            (a.out/'raster-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
if __name__=='__main__':main()
