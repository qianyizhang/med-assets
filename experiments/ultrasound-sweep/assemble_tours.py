"""Assemble the inspected abdominal sweeps and their acquired references for a local gallery."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / 'research'
GALLBLADDER = {
    'id': 'gallbladder', 'title': 'Gallbladder', 'organ': 'gallbladder',
    'region': 'Right upper abdomen', 'exterior': 'fitted-atlas',
    'sectorDepthMm': 133, 'keyframeLabels': ['Long axis', 'Short axis'],
    'phaseLabels': ['Find window', 'Rotate probe'],
    'parts': [
        {'id': 'gallbladder', 'label': 'Gallbladder', 'color': '#3fbf9e', 'opacity': 1},
        {'id': 'liver', 'label': 'Liver', 'color': '#ad6155', 'opacity': .58},
        {'id': 'ribs', 'label': 'Ribs', 'color': '#dacaad', 'opacity': .78},
    ],
    'overlayParts': ['gallbladder', 'liver', 'portal_vein_and_splenic_vein'],
}
GALLBLADDER_REFERENCES = {
    'gallbladder-12': {
        'path': 'media/acquired-long.webp', 'title': 'Gallbladder in long axis',
        'credit': 'Claudia Lucius et al., Life (2025), figure 2', 'url': 'https://doi.org/10.3390/life15060941',
        'license': 'CC BY 4.0', 'licenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
        'note': 'Claudia Lucius’s own collection. Complete still resized and converted to WebP.',
    },
    'gallbladder-48': {
        'path': 'media/acquired-short.webp', 'title': 'Normal Gallbladder, Short Axis',
        'credit': 'Kathryn Pade, MD, Rady Children’s Hospital San Diego · The POCUS Atlas',
        'url': 'https://www.thepocusatlas.com/pedsbiliary', 'license': 'CC BY-NC 4.0',
        'licenseUrl': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'note': 'Adolescent case. Full cine frame at 1.2 seconds converted to WebP.',
    },
}


def assemble(output):
    refs = dict(GALLBLADDER_REFERENCES)
    files = {}
    for source in ('hepatopancreatic.json', 'renal-splenic.json', 'great-vessels.json'):
        for key, ref in json.loads((RESEARCH / source).read_text()).items():
            if key in refs:
                raise ValueError(f'Duplicate reference {key}')
            name = Path(ref['path']).name
            if ref['path'] != 'references/' + name:
                raise ValueError(f'Invalid reference path {key}')
            data = (RESEARCH / 'acquired' / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != ref['sha256']:
                raise ValueError(f'Unexpected acquired image identity: {name}')
            files[ref['path']] = data
            refs[key] = ref

    tracks = json.loads((HERE / 'abdomen-tracks.json').read_text())
    tours = []
    for track in [GALLBLADDER, *tracks]:
        tour = track.copy()
        slug = tour['id']
        root = './' if slug == 'gallbladder' else f'sweeps/{slug}/'
        parts = {part['id']: part for part in tour['parts']}
        if slug == 'gallbladder':
            parts['portal_vein_and_splenic_vein'] = {
                'id': 'portal_vein_and_splenic_vein', 'label': 'Portal and splenic veins', 'color': '#799ac4',
            }
        tour['overlayParts'] = [parts[key] for key in tour['overlayParts']]
        tour['assetRoot'] = root
        tour['title'] += ' sweep'
        tour['sourceNote'] = ('Illustrative BodyParts3D exterior fitted to the s1233 probe-contact window.'
                              if tour.get('exterior') == 'fitted-atlas'
                              else 'External body surface and internal structures sampled from the same s1233 CT.')
        if slug != 'gallbladder':
            receipt = json.loads((output / root / 'verification.json').read_text())
            if (receipt['exterior'] != tour['exterior'] or
                    receipt['sectorDepthMm'] != tour['sectorDepthMm'] or receipt['case'] != 's1233'):
                raise ValueError(f'Rebuild {slug} for the configured exterior, depth and source case.')
        tour['keyframes'] = []
        for frame, label in zip((12, 48), tour.pop('keyframeLabels'), strict=True):
            ref_id = f'{slug}-{frame}'
            if ref_id not in refs:
                raise ValueError(f'Missing acquired comparison: {ref_id}')
            key = {'frame': frame, 'label': label, 'referenceId': ref_id}
            tour['keyframes'].append(key)
        tour['phases'] = [dict(frame=frame, label=label) for frame, label in
                          zip((0, 12), tour.pop('phaseLabels'), strict=True)]
        # Check candidate delivery through the same filenames that the tour reads.
        for kind in ('scan', 'section'):
            for i in range(49):
                if not (output / root / 'media' / f'{kind}-{i:02}.webp').is_file():
                    raise ValueError(f'Missing {slug} {kind} at frame {i}')
        mesh_names = ['torso', *(part['id'] for part in tour['parts'])]
        for name in ['sweep.js', *(f'scenes/{part}.mesh' for part in mesh_names)]:
            if not (output / root / name).is_file():
                raise ValueError(f'Missing {slug} input: {name}')
        tours.append(tour)
    for info in GALLBLADDER_REFERENCES.values():
        if not (output / info['path']).is_file():
            raise ValueError(f'Missing gallbladder comparison: {info["path"]}')
    for path, data in files.items():
        dest = output / path
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(data)
    for name, variable, content in [('references.js', 'abdomenReferences', refs), ('abdomen-tours.js', 'abdomenTours', tours)]:
        (output / name).write_text(f'const {variable} = ' + json.dumps(content, ensure_ascii=False, indent=2) + ';\n')
    for name in ('index.html', 'study.css', 'study.js', 'scene.js'):
        shutil.copyfile(HERE / name, output / name)
    print(f'Assembled {len(tours)} sweeps with {len(refs)} reference bindings.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    assemble(parser.parse_args().output)
