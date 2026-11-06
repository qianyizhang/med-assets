"""Compare actually reimported exterior vertices at every authored sample."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--animated',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.output.exists(): raise ValueError('Refusing existing roundtrip proof')
raw=a.candidate.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+n]);names=sorted(n['name'] for n in doc['nodes'] if 'mesh' in n)
assert len(names)==124
frames=list(range(25)) if a.animated else [0]

def inspect(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects={o.name:o for o in scene.objects if o.type=='MESH' and o.name in names}
    assert set(objects)==set(names)
    hashes=[];reference={};max_motion={n:0.0 for n in ['RA | complete wall','RV | complete wall','LA | complete wall','LV | complete wall']}
    for frame in frames:
        scene.frame_set(frame);bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();hasher=hashlib.sha256();count=0
        for name in names:
            ev=objects[name].evaluated_get(dg);me=ev.to_mesh()
            coords=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',coords)
            coords=coords.reshape(-1,3)
            mat=np.array(ev.matrix_world,dtype=np.float64)
            world=coords.astype(np.float64)@mat[:3,:3].T+mat[:3,3]
            hasher.update(name.encode());hasher.update(world.astype('<f8').tobytes())
            count+=len(world)
            if name in max_motion:
                if frame==0: reference[name]=world.copy()
                max_motion[name]=max(max_motion[name],float(np.linalg.norm(world-reference[name],axis=1).max()))
            ev.to_mesh_clear()
        hashes.append({'frame':frame,'time_seconds':frame/30,'vertices':count,'world_coordinate_sha256':hasher.hexdigest()})
    return {'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':hashes,'max_sampled_wall_displacement_m':max_motion}

source=inspect(a.source);candidate=inspect(a.candidate)
assert source['frames']==candidate['frames'],'Reimported retained geometry or motion differs'
assert source['max_sampled_wall_displacement_m']==candidate['max_sampled_wall_displacement_m']
if a.animated:
    assert all(v>0 for v in candidate['max_sampled_wall_displacement_m'].values())
    assert candidate['frames'][0]['world_coordinate_sha256']==candidate['frames'][-1]['world_coordinate_sha256']
a.output.write_text(json.dumps({'scope':'Actual Blender clean-reimport evaluation of all124 retained exterior mesh nodes; every25 authored clip sample when animated; no physiology, continuous-time or browser claim','blender':bpy.app.version_string,'fps':30,'exact_source_candidate_match':True,'source':source,'candidate':candidate},indent=2)+'\n')
print('PASS',len(names),'exterior mesh nodes;',len(frames),'samples; exact imported world-coordinate identity')
