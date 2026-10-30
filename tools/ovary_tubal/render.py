"""Clean-import source/export comparisons with source materials and matched cameras."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build


def geometry(obj):
    mesh=obj.data;mesh.calc_loop_triangles()
    points=[obj.matrix_world@v.co for v in mesh.vertices]
    packed=b''.join(struct.pack('<fff',*p) for p in points)
    packed+=b''.join(struct.pack('<III',*t.vertices) for t in mesh.loop_triangles)
    normals=b''.join(struct.pack('<fff',*n.vector) for n in mesh.corner_normals)
    return {'name':obj.name,'vertices':len(points),'triangles':len(mesh.loop_triangles),
            'worldGeometrySha256':build.sha(packed),'cornerNormalsSha256':build.sha(normals),
            'matrixWorld':[list(r) for r in obj.matrix_world],
            'parent':obj.parent.name if obj.parent else None,
            'materials':[m.name for m in mesh.materials]}


def load(paths):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build.require(not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Autoexec must be disabled')
    for path in paths:bpy.ops.import_scene.gltf(filepath=str(path),merge_vertices=False)
    bpy.context.view_layer.update()
    meshes={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
    signature={'meshes':{n:geometry(o) for n,o in sorted(meshes.items())},'materials':{}}
    for mat in bpy.data.materials:
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            signature['materials'][mat.name]={'baseColor':list(bsdf.inputs['Base Color'].default_value),
                'roughness':bsdf.inputs['Roughness'].default_value,'metallic':bsdf.inputs['Metallic'].default_value}
    build.require(len(meshes)==10,'Reimport mesh inventory differs')
    return meshes,signature


def positions(objects):
    return [o.matrix_world@v.co for o in objects for v in o.data.vertices]


def center(objects):
    points=positions(objects)
    return Vector([(min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)])


def render(meshes,output,variant):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
    scene.cycles.seed=0;scene.cycles.use_denoising=False;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
    scene.world=bpy.data.worlds.new('Editorial display world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.035,.045,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    full=list(meshes.values());mid=center(full)
    lights=[('key',(-.15,-.16,.18),.36,.14),('fill',(.15,-.08,.05),.16,.14),('rim',(.04,.13,.10),.22,.12)]
    for name,offset,power,size in lights:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=mid+Vector(offset)
        obj.rotation_euler=(mid-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Matched source/export camera');data.type='ORTHO'
    camera=bpy.data.objects.new('Matched source/export camera',data);scene.collection.objects.link(camera);scene.camera=camera
    settings=[('overview',full,.165,(1200,800),None)]
    for side,name in [('L','VH_F_left_ovary'),('R','VH_F_right_ovary')]:
        selected=[o for n,o in meshes.items() if n==name or n.endswith('_'+side)]
        settings.append(('detail-'+side,selected,.064,(900,900),side))
    rows=[]
    for view,selected,scale,resolution,side in settings:
        for obj in full:obj.hide_render=obj not in selected
        target=center(selected);camera.location=target+Vector((0,-.35,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
        bpy.context.view_layer.update()
        def project(point):
            p=world_to_camera_view(scene,camera,point);return [p.x*resolution[0],(1-p.y)*resolution[1]]
        pixels=[project(p) for p in positions(selected)]
        margins={'left':min(p[0] for p in pixels),'right':resolution[0]-max(p[0] for p in pixels),
                 'top':min(p[1] for p in pixels),'bottom':resolution[1]-max(p[1] for p in pixels)}
        build.require(min(margins.values())>=40,'Selected source surfaces touch the frame')
        anchors={}
        if side:
            names={'ovary':'VH_F_left_ovary' if side=='L' else 'VH_F_right_ovary','fimbria':'VH_F_fibria_of_uterine_tube_'+side}
            direction=(target-camera.location).normalized();deps=bpy.context.evaluated_depsgraph_get()
            for role,name in names.items():
                pts=positions([meshes[name]]);px=[project(p) for p in pts];mean=[sum(p[a] for p in px)/len(px) for a in range(2)]
                ordered=sorted(zip(pts,px),key=lambda item:sum((item[1][a]-mean[a])**2 for a in range(2)))
                for point,pixel in ordered:
                    hit,loc,normal,index,obj,matrix=scene.ray_cast(deps,point-direction*.5,direction,distance=1)
                    if hit and obj.name==name:
                        anchors[role]={'sourceNode':name,'pixel':pixel,'rayHitNode':obj.name};break
                build.require(role in anchors,'No visible source anchor: '+name)
        path=output/(variant+'-'+view+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        raw=path.read_bytes();rows.append({'variant':variant,'view':view,'file':path.name,'bytes':len(raw),'sha256':build.sha(raw),
            'resolution':list(resolution),'cameraWorldMatrix':[list(r) for r in camera.matrix_world],
            'orthoScaleM':scale,'visibleSourceNodes':sorted(o.name for o in selected),'frameMarginsPx':margins,'anchors':anchors})
    return rows,lights


def run(root,candidate,output):
    build.require(not output.exists(),'Output already exists');output.mkdir(parents=True)
    manifest,sources=build.read_sources(root);candidate_bytes=candidate.read_bytes();build.validate(sources,candidate_bytes)
    originals,first=load([root/s['file'] for s in sources]);baseline,lights=render(originals,output,'source')
    current,second=load([candidate]);build.require(first==second,'Clean reimport source geometry/normals/transforms/hierarchy/materials differ')
    updated,unused=render(current,output,'export')
    for a,b in zip(baseline,updated):
        for key in ('view','resolution','cameraWorldMatrix','orthoScaleM','visibleSourceNodes','frameMarginsPx','anchors'):
            build.require(a[key]==b[key],'Matched render condition differs: '+key)
    after={n:geometry(o) for n,o in sorted(current.items())};build.require(after==second['meshes'],'Render modified imported geometry')
    build.read_sources(root);build.require(candidate.read_bytes()==candidate_bytes,'Candidate changed during reimport')
    result={'candidateSha256':build.sha(candidate_bytes),'candidateBytes':len(candidate_bytes),'blender':bpy.app.version_string,
        'cleanReimportExact':True,'sourceSignature':first,'candidateSignature':second,'views':baseline+updated,
        'display':{'engine':'Cycles CPU','samples':32,'seed':0,'denoising':False,'sourceMaterialsPreserved':True,'lights':lights,'view':'native glTF +Z; source labels, not independently established patient orientation'},
        'geometryAndSourceBytesUnchanged':True,'runtime':'unverified','anatomyClinical':'unverified'}
    (output/'reimport-render.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cleanReimportExact':True,'candidateSha256':result['candidateSha256'],'frames':len(result['views']),
                      'margins':[{k:r[k] for k in ('view','frameMarginsPx')} for r in updated]},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);run(args.root,args.candidate,args.output)
