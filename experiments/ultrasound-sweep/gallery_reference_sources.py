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
        'asset': 'breasts_hra', 'revision': 'teaching-economy-r01', 'file': 'breasts_hra_native_frame.glb',
        'label': 'Mammary anatomy · HRA', 'space': 'hra-mammary-native',
        'sha256': '2a7d6d05e06fa8d86adffdf0fd324389cf23ac736b3b659f7c227b96e499fe51',
        'credit': 'Heidi Schlehlein · Human Reference Atlas · CC BY 4.0',
        'attribution': 'models/breasts_hra/exports/source-candidate-02/ATTRIBUTION.md',
        'nodes': {'VH_F_' + name + '_L': ('breast-left-' + key, 'Left ' + label)
                  for name, key, label in [('mammary_lobes', 'lobes', 'mammary lobes'),
                                            ('main_lactiferous_ducts', 'ducts', 'lactiferous ducts'),
                                            ('fat', 'fat', 'breast fat'), ('areola', 'areola', 'areola'),
                                            ('nipple', 'nipple', 'nipple')]},
    },
    {
        'asset': 'vagina_hra', 'revision': 'context-r02', 'file': 'vagina_hra_same_atlas_context_r02.glb',
        'label': 'Female pelvic reference · HRA', 'space': 'hra-pelvis-native',
        'sha256': 'c649de4db766ba00020315029c922de1d018061c1a34bd95c850a05255ab3037',
        'credit': HRA_CREDIT, 'attribution': 'models/vagina_hra/provenance/context-r02/migration-2026-10-24/ATTRIBUTION.md',
        'guide': 'models/vagina_hra/provenance/context-r02/migration-2026-10-24/README.md',
        'nodes': {'VH_F_body_of_uterus': ('uterus-body', 'Uterine body'), 'VH_F_cervix': ('cervix', 'Cervix'),
                  'VH_F_internal_cervical_os': ('internal-os', 'Internal cervical os'),
                  'VH_F_external_cervical_os': ('external-os', 'External cervical os'),
                  'VH_F_vagina': ('vagina', 'Vagina'), 'VH_F_rectum': ('rectum', 'Rectum')},
    },
    {
        'asset': 'ovaries', 'revision': 'hra-ovary-tubal-r01', 'file': 'ovary-tubal-context.glb',
        'label': 'Ovary and tubal landmarks · HRA', 'space': 'hra-ovary-tubal-native',
        'sha256': '465a44b18df91ece95a236372a8cbe3e1a0de0207525955290e6b0fa519195d1',
        'credit': HRA_CREDIT, 'attribution': 'sources/datasets/hra/ovary-tubal-context/ATTRIBUTION.md',
        'nodes': {'VH_F_left_ovary': ('ovary-left', 'Left ovary'), 'VH_F_right_ovary': ('ovary-right', 'Right ovary'),
                  'VH_F_ampulla_of_uterine_tube_L': ('uterine-tube-left', 'Left tubal ampulla'),
                  'VH_F_ampulla_of_uterine_tube_R': ('uterine-tube-right', 'Right tubal ampulla')},
    },
    {
        'asset': 'placenta', 'revision': 'hra-v1.1-r02', 'file': 'placenta_full_term.glb',
        'label': 'Full-term placenta and cord · HRA', 'space': 'hra-term-placenta-native',
        'sha256': '7f9f215f810003fddc76ede225f051dc7014c67216e804403a4632d628ad82aa',
        'credit': 'Heidi Schlehlein · Human Reference Atlas · CC BY 4.0', 'attribution': 'models/placenta/ATTRIBUTION.md',
        'guide': 'models/placenta/README.md',
        'nodes': {'VH_F_umbilical_artery_1': ('umbilical-artery-1', 'First umbilical artery'),
                  'VH_F_umbilical_artery_2': ('umbilical-artery-2', 'Second umbilical artery'),
                  'VH_F_umbilical_vein': ('term-umbilical-vein', 'Umbilical vein'),
                  'VH_F_umbilical_cord': ('term-cord', 'Umbilical cord surface'),
                  'VH_F_basal_plate': ('basal-plate', 'Basal plate'),
                  'VH_F_chorionic_plate': ('chorionic-plate', 'Chorionic plate')},
    },
    {
        'asset': 'lymph_node', 'revision': 'tissue-color-pack-r02', 'file': 'lymph-node.glb',
        'label': 'Lymph node layers · HRA', 'space': 'hra-lymph-node-native',
        'sha256': 'd0b8ac731f187c10e1c7f23a15d6f4ec285b7727cc98bf9feed26fb97e5ee692',
        'credit': HRA_CREDIT, 'attribution': 'models/lymph_node/ATTRIBUTION.md',
        'nodes': {'Yao_capsule_of_lymph_node': ('lymph-node-capsule', 'Lymph node capsule'),
                  'Yao_paracortex': ('lymph-node-paracortex', 'Paracortex'),
                  'Yao_medulla_of_lymph_node': ('lymph-node-medulla', 'Lymph node medulla')},
    },
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
                'assetId': f'library/{asset}', 'assetRevision': revision,
                'assetLabel': source['label'], 'title': source['label'], 'sourceSpace': source['space'],
                'mesh': output.relative_to(destination).as_posix(), 'scale': 1,
                'color': '#' + ''.join(srgb_channel(v) for v in (red, green, blue)), 'opacity': opacity,
                'url': upstream + source.get('guide', edition + '/README.md'), 'sourceNode': name, 'sourceSha256': source['sha256'],
                'credit': source['credit'], 'attribution': upstream + source['attribution'],
            })
    (destination / 'development' / 'gallery-donors.json').write_text(json.dumps(records, indent=2) + '\n')
