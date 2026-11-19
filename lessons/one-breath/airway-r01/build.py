"""Build the portable route from the same glTF-space routes consumed by One Breath."""
import json
from math import cos, pi, sin
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'tools'))
from teaching_scene import bounds, colorize, export, load_meshes, material, tube

def xyz(p):
    return Vector((p[0],-p[2],p[1]))


def side_wall(name, profile, x, thickness, mat):
    # Sagittal landmark in anterior-height coordinates, two parallel side faces.
    verts = [(offset,-forward,up) for offset in (x,x+thickness) for forward,up in profile]
    n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    colorize(obj,mat)


def alveolus(name, p, radius, mat):
    # Spherical cup open to the teaching view. The collection is an enlarged distal inset.
    rings=[]
    for j in range(14):
        elevation=-.5*pi+.05+ j*(pi*.70)/13
        rings.append([xyz(p)+Vector((radius*cos(elevation)*cos(i*2*pi/32),
                      -radius*sin(elevation),radius*cos(elevation)*sin(i*2*pi/32))) for i in range(32)])
    mesh=bpy.data.meshes.new(name)
    faces=[(j*32+i,j*32+(i+1)%32,(j+1)*32+(i+1)%32,(j+1)*32+i)
           for j in range(13) for i in range(32)]
    faces.append(tuple(reversed(range(32))))
    mesh.from_pydata([v for ring in rings for v in ring],[],faces)
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    colorize(obj,mat)
    for face in mesh.polygons:
        face.use_smooth=True


def main():
    target=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    target.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    inputs=json.loads((HERE/'inputs.json').read_text())
    lesson=json.loads((HERE.parent/'assets.json').read_text())
    route=lesson['airwayExtension']
    skin=material('Mucosal section • peach',(.56,.32,.26))
    tan=material('Cartilage • ochre',(.66,.55,.38))
    tissue=material('Tracheal wall • rose',(.53,.31,.27))
    air=material('Air path • teal',(.12,.43,.46))
    bronchiole=material('Distal passage • sage',(.32,.56,.47))
    distal=material('Alveolar wall • coral',(.65,.38,.33))
    larynx=load_meshes(**inputs['larynx'],select=lambda name:name.startswith(('FJ2769','FJ2770','FJ2808')))
    cricoid,=[o for o in larynx if o.name.startswith('FJ2769')]
    lo,hi=bounds([cricoid])
    foundation=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    translation=xyz(lesson['ports']['proximal']['position'])-foundation
    for obj in larynx:
        obj.location=translation
        obj.name='Larynx | '+obj.name
        colorize(obj,tan)
    for obj in load_meshes(**inputs['trachea']):
        obj.name='V7 | '+obj.name
        colorize(obj,tissue if 'shell' in obj.name else tan)
    lobar,=load_meshes(**inputs['bronchi'],select=lambda n:n=='lung_upper_lobe_left lobar bronchus')
    lobar.name='Branch | Left upper lobar bronchus (Workshop)'
    colorize(lobar,tan)
    paths=[
        ('Nasal | Passage','nasal',.0026,air),('Pharynx | Nasal to laryngeal route','pharynx',.0028,air),
        ('Larynx | Laryngeal passage','larynx',.0029,air),('Branch | Main to lobar bridge','bronchialBridge',.0027,air),
        ('Branch | Smaller airway generations','distal',.0019,bronchiole),
        ('Terminal | Terminal bronchiole','terminal',.00155,bronchiole),
        ('Terminal | Respiratory bronchiole and alveolar duct','alveolar',.0016,air)]
    for name,key,radius,mat in paths:
        tube(name,[xyz(p) for p in route[key]],radius,mat)
    for key in ('main','left','right'):
        tube('V7 guide | '+key+' centreline',[xyz(p) for p in lesson['route'][key]],.0018,air)
    side_wall('Nasal | Schematic sagittal wall',[(.077,.279),(.068,.296),(.052,.307),(.021,.309),(.007,.302),
        (.004,.287),(.013,.281),(.044,.280),(.064,.277)],-.005,.0035,skin)
    for i,(low,high,width) in enumerate([(.288,.292,.045),(.295,.300,.036),(.302,.305,.020)]):
        side_wall('Nasal | Conchal shelf '+str(i+1),[(.012,low),(.016+width,low+.002),(.011+width,high),(.021,high)],
                  -.0014,.004, tan)
    # The route enters one enlarged cluster; omit intervening real airway generations.
    sacs=[(.128,.133,0),(.134,.141,-.002),(.140,.132,-.001),(.134,.124,-.002),(.126,.144,-.004)]
    for index,(x,y,z) in enumerate(sacs):
        alveolus('Terminal | Alveolar cup '+str(index+1),(x,y,z),.0058,distal)
        if index:
            tube('Terminal | Duct opening '+str(index),[xyz(sacs[0]),xyz((x,y,z))],.00155,air)
    for obj in bpy.context.scene.objects:
        obj['lessonRegion'] = obj.name.split(' | ')[0]
    bpy.context.scene.unit_settings.system='METRIC'
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_rotation=Vector((-.55,1,-.13)).to_track_quat('-Z','Y')
            area.spaces.active.region_3d.view_distance=.48
            area.spaces.active.region_3d.view_location=(.055,0,.188)
            area.spaces.active.shading.color_type='MATERIAL'
    export(target,'airway-route')
    (target/'placement.json').write_text(json.dumps(dict(laryngealTranslationBlenderMetres=list(translation),
       trachea='identity',lobarBranch='identity',coordinates='glTF +X left, +Y superior, +Z anterior; authored routes from assets.json'),indent=2)+'\n')


if __name__=='__main__':
    main()
