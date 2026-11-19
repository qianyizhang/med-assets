"""Check intended contacts between the named surfaces of a clean GLB import."""
from pathlib import Path
import json
import sys

import bpy
from mathutils.bvhtree import BVHTree

# Joined surface boundaries may overlap. Each limit is in display metres.
CHAINS = {
    'Central': [
        ['Right sciatic source course', 'Ventral ramus and plexus bridge', 'Representative mixed nerve descending 2 side-1',
         'Representative dorsal root descending 2 side-1', 'Dorsal column surface overlay to medulla'],
        ['Authored cord with two enlargements and one conus', 'Cervicomedullary gross bridge'],
    ],
    'Ear': [
        ['Right auricle (source)', 'External acoustic canal (cut)', 'Tympanic membrane', 'Malleus handle',
         'Malleus head', 'Incus body', 'Incus long process', 'Stapes crura', 'Stapes footplate at oval window',
         'Vestibule at oval window', 'Cochlear spiral', 'Organ of Corti marker', 'Cochlear hair cell (enlarged)',
         'Spiral ganglion afferent', 'Spiral ganglion soma', 'Cochlear branch of VIII', 'VIII common trunk'],
        ['Vestibule at oval window','Utricle','Utricular macula marker','Vestibular hair cell (enlarged)',
         'Vestibular ganglion afferent','Vestibular ganglion soma','Vestibular branch of VIII','VIII common trunk'],
        ['Anterior canal','Utricle','Posterior canal'],['Lateral canal','Utricle','Saccule'],
    ],
    'Vision': [['Retinal strip (posterior cup)','Rod outer segment','Photoreceptor basal ending','Bipolar relay',
                'Retinal ganglion cell','Ganglion axon to optic disc','Optic nerve II (source)']],
    'Smell': [['Olfactory dendrite and knob','Olfactory receptor neuron','Receptor axon in olfactory filament I',
               'Olfactory bulb glomerulus']],
    'Taste': [['Microvillus at pore 1','Gustatory receptor cell','Chorda tympani taste afferent VII']],
}


def main():
    path=Path(sys.argv[sys.argv.index('--')+1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    trees, vertices = {}, {}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':
            continue
        obj.data.calc_loop_triangles()
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        vertices[obj.name]=points
        trees[obj.name]=BVHTree.FromPolygons(points, [tri.vertices for tri in obj.data.loop_triangles],all_triangles=True)
    def distance(a,b):
        if trees[a].overlap(trees[b]):
            return 0.
        return min(min(trees[first].find_nearest(v)[3] for v in vertices[second])
                   for first,second in [(a,b),(b,a)])
    pairs={}
    for group,chains in CHAINS.items():
        for chain in chains:
            for first,second in zip(chain,chain[1:]):
                a,b=group+' | '+first,group+' | '+second
                pairs[a+' → '+second]=distance(a,b)
    medulla=[name for name in trees if name.startswith('Central | Brain medulla')]
    if len(medulla)!=2:
        raise ValueError('Missing medulla atlas halves')
    for segment in ['Cervicomedullary gross bridge','Dorsal column surface overlay to medulla']:
        name='Central | '+segment
        pairs[name+' → medulla']=min(distance(name,b) for b in medulla)
    print(json.dumps(dict(meshes=len(trees),surfaceGapsMetres=pairs),indent=2))
    # 0.12 mm in the 2x ear inset, below a quarter of the narrowest ossicular shaft.
    # Intentional synaptic and epithelial boundaries are simplified as contacts.
    failures={name:gap for name,gap in pairs.items() if gap>.00012}
    if failures:
        raise ValueError('Non-contacting path links: '+str(failures))


if __name__=='__main__':
    main()
