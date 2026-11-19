"""Check the named structures and intended joins on the clean portable GLB."""
from pathlib import Path
import json
import sys

import bpy
from mathutils.bvhtree import BVHTree


def main():
    source=Path(sys.argv[sys.argv.index('--')+1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    meshes={}
    points={}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':
            continue
        obj.data.calc_loop_triangles()
        points[obj.name]=[obj.matrix_world@v.co for v in obj.data.vertices]
        meshes[obj.name]=BVHTree.FromPolygons(points[obj.name],
            [t.vertices for t in obj.data.loop_triangles],all_triangles=True)
    chain=['Nasal | Passage','Pharynx | Nasal to laryngeal route','Larynx | Laryngeal passage',
           'V7 guide | main centreline','V7 guide | left centreline','Branch | Main to lobar bridge',
           'Branch | Left upper lobar bronchus (Workshop)','Branch | Smaller airway generations',
           'Terminal | Terminal bronchiole','Terminal | Respiratory bronchiole and alveolar duct']
    pairs=[*zip(chain,chain[1:]),(chain[3],'V7 guide | right centreline')]
    # The terminal path ends at the centre of the cup, surrounded by its curved wall.
    for i in range(1,5):
        pairs.append((chain[-1],'Terminal | Duct opening '+str(i)))
    expected={'Nasal | Schematic sagittal wall','Larynx | FJ2769 Cricoid cartilage',
              'Larynx | FJ2770 Epiglottis','Larynx | FJ2808 Thyroid cartilage',
              'V7 | Trachea | authored cutaway teaching shell'}
    if required:=expected-meshes.keys():
        raise ValueError('Missing airway landmarks: '+str(required))
    gaps={}
    for a,b in pairs:
        if meshes[a].overlap(meshes[b]):
            gap=0.
        else:
            gap=min(min(meshes[first].find_nearest(p)[3] for p in points[second])
                    for first,second in ((a,b),(b,a)))
        gaps[a+' → '+b]=gap
    # A cup's bounding interval must surround its terminal duct endpoint in x and height.
    from mathutils import Vector
    route=json.loads((Path(__file__).resolve().parent.parent/'assets.json').read_text())['airwayExtension']
    endpoint=route['alveolar'][-1]
    center=Vector((endpoint[0],-endpoint[2],endpoint[1]))
    hits=[meshes['Terminal | Alveolar cup 1'].ray_cast(center,Vector(direction),.007)[0] is not None
          for direction in ((1,0,0),(-1,0,0),(0,0,1),(0,0,-1))]
    print(json.dumps(dict(meshes=len(meshes),surfaceGapsMetres=gaps,alveolarWallHits=hits),indent=2))
    if not all(hits) or any(g>.00012 for g in gaps.values()):
        raise ValueError('Continuity or alveolar enclosure failed')


if __name__=='__main__':
    main()
