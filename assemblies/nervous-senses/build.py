"""Build a posterior sensory route and five independent teaching insets in Blender."""
from math import cos, sin, pi, radians
from pathlib import Path
import json
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools'))
from teaching_scene import bounds, colorize, ellipsoid, export, load_meshes, material, tube

INPUTS = json.loads((HERE / 'inputs.json').read_text())
TAU = 2*pi
transforms = {}


def acquire(key, select=lambda name: True):
    return load_meshes(**INPUTS[key], select=select)


def move(key, objs, displacement=(0, 0, 0), *, rotation=0, scale=1, pivot=(0, 0, 0)):
    matrix = (Matrix.Translation(Vector(displacement)) @ Matrix.Rotation(radians(rotation), 4, 'Z')
              @ Matrix.Scale(scale, 4) @ Matrix.Translation(-Vector(pivot)))
    for obj in objs:
        obj.data.transform(matrix)
        obj.data.update()
    transforms[key] = [list(row) for row in matrix]


def clip(obj, plane, normal):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    bmesh.ops.bisect_plane(mesh, geom=list(mesh.verts) + list(mesh.edges) + list(mesh.faces),
                           plane_co=plane, plane_no=normal, dist=.0000001, clear_inner=True)
    mesh.to_mesh(obj.data)
    mesh.free()
    obj.data.update()


def extreme(obj, axis, highest=True):
    verts = (v.co.copy() for v in obj.data.vertices)
    return (max if highest else min)(verts, key=lambda v:v[axis])


def centers(objs):
    lo, hi = bounds(objs)
    return (lo + hi)/2


def central():
    brain = acquire('brain')
    cords = acquire('cord', lambda n:'Authored cord' in n or any(suffix in n for suffix in
                    ['upper 2 side1', 'upper 2 side-1', 'upper 7 side1', 'upper 7 side-1',
                     'descending 2 side-1', 'descending 2 side1']))
    sciatic, = acquire('sciatic', lambda n:n.startswith('Sciatic'))
    sciatic.name = 'Central | Right sciatic source course'
    colorize(sciatic, signal)
    move('sciatic', [sciatic])
    move('cord', cords, (0, -.007, 1.16))
    cord, = [o for o in cords if o.name.startswith('Authored cord')]
    root, = [o for o in cords if 'dorsal root descending 2 side-1' in o.name]
    mixed, = [o for o in cords if 'mixed nerve descending 2 side-1' in o.name]
    # Affine translation alone stages the truncated BP3D medulla at the authored cord tip.
    caudal = min((extreme(o, 2, False) for o in brain if 'medulla' in o.name),key=lambda v:v.z)
    rostral = extreme(cord, 2)
    move('brain', brain, rostral - caudal + Vector((0,0,.005)))
    for obj in brain:
        obj.name = 'Central | Brain ' + obj.name
        colorize(obj, neural if 'medulla' in obj.name else brainmat)
    for obj in cords:
        obj.name = 'Central | ' + obj.name
        colorize(obj, signal if obj in (root, mixed) else neural if obj == cord else pale)
    top = extreme(sciatic, 2)
    end = extreme(mixed, 0, False)
    tube('Central | Ventral ramus and plexus bridge', [top, (top.x-.001,top.y,.986),
         (end.x-.003,end.y+.003,.99), end], .00165, signal)
    bottom = extreme(root, 2)
    # Surface overlay beside the ipsilateral dorsal column, widened at teaching scale.
    route = [bottom]
    for z in [1.13,1.19,1.25,1.32,1.39,1.45,rostral.z]:
        section = [v.co for v in cord.data.vertices if abs(v.co.z - z) < .006 and v.co.x < .0001]
        nearest = max(section, key=lambda v:v.y)
        route.append((-.0022,nearest.y+.00065,z))
    endpoint = caudal + Vector((transforms['brain'][0][3],transforms['brain'][1][3],transforms['brain'][2][3]))
    tube('Central | Dorsal column surface overlay to medulla', route + [endpoint], .00145, signal)
    tube('Central | Cervicomedullary gross bridge', [rostral,endpoint], .0036, neural)
    return [obj.name for obj in (sciatic,mixed,root,cord)]


class Panel:
    """Local panel coordinates in illustrative millimetres at a fixed scene origin."""
    def __init__(self, name, offset, scale=.001, superior=1):
        self.name, self.offset, self.scale = name, Vector(offset), scale
        self.superior = superior

    def point(self, p):
        return self.offset + self.scale*Vector((p[0],p[1],self.superior*p[2]))

    def bead(self, name, center, radii, mat):
        return ellipsoid(self.name+' | '+name, self.point(center), self.scale*Vector(radii), mat)

    def line(self, name, pts, r, mat):
        return tube(self.name+' | '+name, [self.point(p) for p in pts], self.scale*r, mat)


def sensory_cell(panel, name, p, mat):
    x,y,z=p
    panel.bead(name, p, (.65,.48,1.25), mat)
    for j in range(4):
        a=x-.42+j*.25
        panel.line(name+' bundle '+str(j+1),[(a,y,z+.83),(a+.16,y,z+1.59+j*.12)], .075, mat)


def ear():
    panel = Panel('Ear',(.25,0,1.39),.002)
    auricle, = acquire('ear')
    clip(auricle,(0,0,0),(-1,0,0))
    auricle.name='Ear | Right auricle (source)'
    colorize(auricle,skin)
    # Move the medial/central conchal region to the lateral end of the cut meatus.
    anchor = min((v.co.copy() for v in auricle.data.vertices),key=lambda v:(v-Vector((-.078,-.001,1.580))).length)
    move('ear-right', [auricle], panel.point((0,0,0)), pivot=anchor, scale=2, rotation=38)
    # An open-sided canal renders both lumen and drum from the teaching camera.
    vertices, faces = [],[]
    for i in range(35):
        t=i/34
        x,y,z=18*t,1.4*sin(pi*t),-.8*sin(2*pi*t)
        for j in range(30):
            a=pi * j/29
            vertices.append(tuple(panel.point((x,y+2.1*sin(a),z+2.1*cos(a)))))
        if i:
            for j in range(29):
                a=(i-1)*30+j
                faces.append((a,a+1,a+31,a+30))
    mesh=bpy.data.meshes.new('Longitudinal meatus section')
    mesh.from_pydata(vertices,[],faces)
    surface=bpy.data.objects.new('Ear | External acoustic canal (cut)',mesh)
    bpy.context.scene.collection.objects.link(surface)
    colorize(surface,skin)
    panel.bead('Tympanic membrane',(18,.15,0),(.48,2.30,2.38), drum)
    panel.line('Malleus handle',[(18.1,-.15,-1.15),(18.7,-.12,.9),(19.7,0,2.55)],.35,bone)
    panel.bead('Malleus head',(19.7,0,2.55),(.79,.70,.78),bone)
    panel.bead('Incus body',(20.68,0,2.72),(.85,.60,.69),bone)
    panel.line('Incus long process',[(20.7,0,2.72),(21.22,-.18,1.89),(21.53,-.20,.12),(22.17,-.20,-.15)],.31,bone)
    panel.line('Stapes crura',[(23.72,-.22,.70),(22.92,-.38,.68),(22.12,-.2,-.15),
               (22.80,-.26,-.98),(23.72,-.22,-1.0)],.21,bone)
    panel.bead('Stapes footplate at oval window',(23.72,-.22,-.12),(.27,.64,1.12),bone)
    panel.bead('Vestibule at oval window',(25,-.02,-.12),(1.35,1.12,1.65),balance)
    # The two labyrinthine divisions share the vestibule. Coil tapers to its apex.
    path=[]
    for i in range(65):
        t=i/64
        a=pi/2-2.5*TAU*t
        r=3.7*(1-.92*t)
        path.append((27.8+r*cos(a),-.42-1.60*t,-5+r*sin(a)))
    panel.line('Cochlear spiral',[(25.4,-.2,-.95),(26.1,-.3,-2.2)]+path,.62,hearing)
    panel.bead('Organ of Corti marker',(28.55,-1.25,-4.90),(1.0,.75,.80),hearing)
    sensory_cell(panel,'Cochlear hair cell (enlarged)',(28.55,-2.2,-4.65),hearing)
    panel.line('Spiral ganglion afferent',[(28.55,-2.2,-5.60),(29.4,-2.85,-5.75),(31.45,-2.5,-5.1)],.28,signal)
    panel.bead('Spiral ganglion soma',(31.45,-2.5,-5.1),(.73,.48,.5),signal)
    panel.line('Cochlear branch of VIII',[(31.45,-2.5,-5.1),(33.8,-2.5,-3.75),(37,-1.00,-2.35)],.51,signal)
    panel.bead('Utricle',(25.3,0,1.1),(1.66,1.1,1.30),balance)
    panel.bead('Saccule',(25.15,-.8,-.29),(.89,.67,.72),balance)
    # Two vertical canal planes face obliquely in opposite directions.
    # The lateral canal lies near horizontal. All return to the utricle.
    for name, axis, cross_axis in [
            ('Anterior canal', (-1.6,1.6,4.8), (.95,-.95,0)),
            ('Posterior canal', (2.2,2.2,4.1), (-1.18,-1.18,0)),
            ('Lateral canal', (3.2,2.5,.45), (-1.15,1.42,0))]:
        pts=[]
        for i in range(31):
            a=TAU*i/30
            pts.append(Vector((25.4,.15,1.3)) + Vector(axis)*(1-cos(a))/2 + Vector(cross_axis)*sin(a))
        panel.line(name,pts,.29,balance)
    panel.bead('Utricular macula marker',(25.65,-1.06,1.38),(.97,.48,.52),balance)
    sensory_cell(panel,'Vestibular hair cell (enlarged)',(25.55,-1.44,2.29),balance)
    panel.line('Vestibular ganglion afferent',[(25.55,-1.44,1.36),(27,-1.75,1.0),(29.8,-2,1.2)],.26,signal)
    panel.bead('Vestibular ganglion soma',(29.8,-2,1.2),(.7,.46,.5),signal)
    panel.line('Vestibular branch of VIII',[(29.8,-2,1.2),(32.6,-2,.45),(37,-1,-2.35)],.43,signal)
    panel.line('VIII common trunk',[(37,-1,-2.35),(39.3,0,-2.4)],.69,signal)


def vision():
    p=Panel('Vision',(.25,0,1.14),.0018)
    objs=acquire('eye', lambda n:n in ('Sclera.r','Optic nerve (II).r'))
    shell,= [o for o in objs if o.name.startswith('Sclera')]
    nerve,= [o for o in objs if o.name.startswith('Optic')]
    center=centers([shell])
    move('eye-right',objs,p.offset,rotation=-90,scale=1.8,pivot=center)
    clip(shell,p.offset,(0,1,0))
    shell.name='Vision | Sclera (sectioned right globe)'
    nerve.name='Vision | Optic nerve II (source)'
    colorize(shell,bone)
    colorize(nerve,signal)
    target=min((v.co.copy() for v in nerve.data.vertices), key=lambda v:(v-p.offset).length)
    p.line('Retinal strip (posterior cup)',[(4,.3,-10.8),(8,.36,-8.3),(10.55,.5,-5),
           (11.3,.5,-2),(11.7,.55,1)],.55,hearing)
    p.bead('Rod outer segment',(8,-.14,-7.65),(.37,.35,1.05),hearing)
    p.line('Photoreceptor basal ending',[(8,-.22,-7.5),(7.1,-.8,-6.6),(6.9,-.8,-5.9)],.22,hearing)
    p.line('Bipolar relay',[(6.9,-.8,-5.9),(6.65,-1,-4.7),(6.26,-1,-3.5)],.27,signal)
    p.bead('Bipolar soma',(6.65,-1,-4.7),(.55,.46,.62),signal)
    p.bead('Retinal ganglion cell',(6.26,-1,-3.5),(.71,.50,.69),signal)
    tube('Vision | Ganglion axon to optic disc',[p.point((6.26,-1,-3.5)),p.point((8,-1.2,-2)),target],.00065,signal)


def epithelia():
    p=Panel('Smell',(.21,0,.93),.0032, superior=-1)
    p.bead('Superior nasal olfactory epithelium',(0,.85,0),(4.9,1.2,1.5),skin)
    p.bead('Olfactory receptor neuron',(0,-.28,.10),(.49,.4,.71),hearing)
    p.line('Olfactory dendrite and knob',[(0,-.3,.38),(0,-.45,1.25),(0,-.45,1.73)],.19,hearing)
    for i in range(5):
        p.line('Olfactory cilium '+str(i+1),[(0,-.45,1.73),((i-2)*.47,-.5,1.95),((i-2)*.87,-.5,1.80)],.08,hearing)
    p.line('Receptor axon in olfactory filament I',[(0,-.28,-.48),(.1,-.3,-2.1),(1.3,-.55,-3.1),
           (2.65,-.45,-4.3)],.21,signal)
    p.bead('Olfactory bulb glomerulus',(2.65,-.45,-4.3),(1,.64,.83),signal)

    p=Panel('Taste',(.34,0,.93),.0032)
    p.bead('Anterior tongue fungiform papilla section',(0,.83,-.85),(4.9,1.12,2.64),skin)
    p.bead('Taste bud',(0,-.20,.37),(1.21,.62,1.80),bone)
    p.bead('Gustatory receptor cell',(0,-.77,.49),(.40,.35,1.24),hearing)
    for i in range(4):
        x=(i-1.5)*.14
        p.line('Microvillus at pore '+str(i+1),[(x,-.77,1.46),(x*1.6,-.77,2.28)],.065,hearing)
    p.line('Chorda tympani taste afferent VII',[(.03,-.79,-.48),(-.18,-.92,-1.5),
           (.78,-1.08,-2.5),(3.3,-1.1,-3.35),(5.2,-.9,-3.2)],.24,signal)


if __name__=='__main__':
    out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    out.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    brainmat=material('Brain • clay',(.58,.35,.30))
    neural=material('Neural axis • ivory',(.66,.54,.39))
    pale=material('Representative collateral roots • gray',(.38,.45,.48))
    signal=material('Afferent and selected roots • ochre',(.80,.38,.075))
    skin=material('Epithelial context • rose',(.60,.33,.25))
    drum=material('Drum • slate',(.35,.46,.51))
    bone=material('Ossicles and sclera • ivory',(.75,.64,.45))
    hearing=material('Sensory receptor • teal',(.13,.42,.43))
    balance=material('Vestibular apparatus • green',(.27,.50,.27))
    route_nodes=central()
    ear()
    vision()
    epithelia()
    # Give an opening .blend a useful orthographic view of the staged panels.
    bpy.context.scene.unit_settings.system='METRIC'
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_rotation=Vector((0,1,0)).to_track_quat('-Z','Y')
            space.region_3d.view_distance=1.85
            space.region_3d.view_location=(.10,.05,1.1)
            space.shading.color_type='MATERIAL'
    export(out,'nervous-senses')
    (out/'placements.json').write_text(json.dumps(dict(sourceToBlenderMetres=transforms,
         routeNodes=route_nodes),indent=2)+'\n')
