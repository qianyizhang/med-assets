"""Package retained Gallery surfaces for independent inspection in the workbench."""
import json

from display_body import ROOT, atlas, primitive_stream, ras_from_gltf
from prepare_scenes import mesh_bytes


HRA_CREDIT = 'Kristen Browne and Heidi Schlehlein · Human Reference Atlas · CC BY 4.0'


def kidney_source(side, digest):
    asset = f'kidney_{side}'
    suffix = side[0].upper()
    return {
        'asset': asset, 'revision': 'teaching-economy-r01', 'file': asset + '.glb',
        'label': f'{side.title()} renal landmarks · HRA', 'space': f'hra-{asset}-v1.3',
        'sha256': digest, 'credit': HRA_CREDIT, 'attribution': f'models/{asset}/ATTRIBUTION.md',
        'nodes': {
            f'VH_F_outer_cortex_of_kidney_{suffix}': (f'kidney-{side}-cortex', f'{side.title()} outer renal cortex'),
            f'VH_F_hilum_of_kidney_{suffix}': (f'kidney-{side}-hilum', f'{side.title()} renal hilum'),
        },
    }


SOURCES = (
    {
        'asset': 'bladder', 'revision': 'pelvic-base-r01', 'file': 'bladder-pelvic-base.glb',
        'label': 'Bladder base and ureteral entries · HRA', 'space': 'hra-female-pelvic-base',
        'sha256': '07de72fc8f3b152291be30f24e24369a08af1232bb1a18f1cb90cdd2440aa15a',
        'credit': HRA_CREDIT,
        'attribution': 'models/bladder/ATTRIBUTION.md',
        'nodes': {
            'VH_F_right_ureter': ('right-ureter', 'Right ureter'),
            'VH_F_left_ureter': ('left-ureter', 'Left ureter'),
            'VH_F_fundus_of_urinary_bladder_dome': ('dome', 'Bladder dome'),
            'VH_F_urinary_bladder_neck_smooth_muscle': ('neck', 'Bladder neck'),
            'VH_F_fundus_of_urinary_bladder_base': ('base', 'Bladder base'),
            'VH_F_trigone_of_urinary_bladder': ('trigone', 'Trigone'),
            'VH_F_ureteral_orifice_R': ('right-ureteral-orifice', 'Right ureteral orifice'),
            'VH_F_ureteral_orifice_L': ('left-ureteral-orifice', 'Left ureteral orifice'),
        },
    },
    {
        'asset': 'pancreas', 'revision': 'hra-female-context-r04', 'file': 'pancreas_hra_female_context_r04.glb',
        'label': 'Pancreas and adjacent anatomy · HRA', 'space': 'hra-pancreas-context',
        'sha256': 'aa15f9248027c248886a9cf8d4f5f401b2753176c800851f648b03d88d97ebed',
        'credit': HRA_CREDIT, 'attribution': 'models/pancreas/ATTRIBUTION.md', 'guide': 'models/pancreas/README.md',
        'nodes': {
            'VH_F_head_of_pancreas': ('pancreas-head', 'Pancreatic head'),
            'VH_F_ucinate_process1': ('pancreas-uncinate', 'Uncinate process'),
            'VH_F_body_of_pancreas': ('pancreas-body', 'Pancreatic body'),
            'VH_F_tail_of_pancreas': ('pancreas-tail', 'Pancreatic tail'),
            'VH_F_hilum_of_spleen': ('splenic-hilum', 'Splenic hilum'),
            'VH_F_common_bile_duct': ('common-bile-duct', 'Common bile duct surface'),
        },
    },
    kidney_source('left', 'e000c2b4408caf1bbbbf2a5649c5e0e3ceaf94b3c2bf794da3a2f30587bb3778'),
    kidney_source('right', 'fdddbde55104ab9af2b5ebafea7e52692dad7f94aad85d93a2237cbdd371e3eb'),
    {
        'asset': 'diaphragm', 'revision': 'normal-pack-r02', 'file': 'diaphragm.glb',
        'label': 'Diaphragm · Z-Anatomy', 'space': 'z-anatomy-diaphragm',
        'sha256': '9857d670bd761ed28b4ce534594ad6b0ad2fc05636ca2a66a86a62db1d9bb8d7',
        'credit': 'Z-Anatomy, Kousaku Okubo, Gauthier Kervyn, Marcin Zielinski and BodyParts3D/DBCLS · CC BY-SA 4.0 and CC BY-SA 2.1 JP',
        'attribution': 'models/diaphragm/exports/z-native-static-r01/ATTRIBUTION.md',
        'nodes': {'Diaphragm': ('diaphragm', 'Diaphragm')},
    },
)


def srgb_channel(value):
    """Convert a glTF linear color channel to an 8-bit CSS channel."""
    srgb = 12.92 * value if value <= .0031308 else 1.055 * value ** (1 / 2.4) - .055
    return f'{round(srgb * 255):02x}'


def write_gallery_donors(destination, source_root=ROOT):
    """Read the pinned GLBs; copy indexed triangles into the viewer's RAS-mm mesh format."""
    records = []
    upstream = 'https://github.com/qianyizhang/med-assets/blob/main/'
    for source in SOURCES:
        asset, revision = source['asset'], source['revision']
        edition = f'models/{asset}/exports/{revision}'
        path = source_root / edition / source['file']
        if not path.is_file():
            continue
        with path.open('rb') as handle:
            if handle.readline(64).startswith(b'version https://git-lfs.github.com/spec/'):
                continue
        doc, binary = atlas(path, source['sha256'])
        # The pinned exports store their surfaces directly in atlas space.
        # Reject a changed transform contract before interpreting local positions.
        if any({'matrix', 'translation', 'rotation', 'scale'} & node.keys() for node in doc['nodes']):
            raise ValueError(f'Unexpected transform in Gallery donor: {path}')
        nodes = {node['name']: node for node in doc['nodes'] if 'mesh' in node}
        if not source['nodes'].keys() <= nodes.keys():
            raise ValueError(f'Missing named part in Gallery donor: {path}')
        key = f'{asset}-{revision}'
        folder = destination / 'development' / 'gallery-sources' / key
        folder.mkdir(parents=True, exist_ok=True)
        for name, (part, label) in source['nodes'].items():
            primitive, = doc['meshes'][nodes[name]['mesh']]['primitives']
            xyz = primitive_stream(doc, binary, primitive['attributes']['POSITION']).reshape(-1, 3)
            faces = primitive_stream(doc, binary, primitive['indices']).reshape(-1, 3)
            output = folder / f'{part}.mesh'
            output.write_bytes(mesh_bytes(ras_from_gltf(xyz) * 1000, faces))
            material = doc['materials'][primitive['material']]['pbrMetallicRoughness']
            red, green, blue, opacity = material.get('baseColorFactor', [1, 1, 1, 1])
            records.append({
                'source': 'gallery', 'case': key, 'chapter': '', 'occurrence': 1,
                'part': part, 'partId': part, 'label': label, 'partLabel': label,
                'assetId': f'library/{asset}/{revision}', 'assetRevision': revision,
                'assetLabel': source['label'], 'title': source['label'], 'sourceSpace': source['space'],
                'mesh': output.relative_to(destination).as_posix(), 'scale': 1,
                'color': '#' + ''.join(srgb_channel(v) for v in (red, green, blue)), 'opacity': opacity,
                'url': upstream + source.get('guide', edition + '/README.md'), 'sourceNode': name, 'sourceSha256': source['sha256'],
                'credit': source['credit'], 'attribution': upstream + source['attribution'],
            })
    (destination / 'development' / 'abdomen-gallery-donors.json').write_text(json.dumps(records, indent=2) + '\n')
