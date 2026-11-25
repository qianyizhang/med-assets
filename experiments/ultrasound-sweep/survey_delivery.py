"""Bind the optional bilateral carotid exam to a sealed acquisition and its clinical references."""

import json
from pathlib import Path
import re

from delivery import sha256, validate_image
from skin_display import exterior_mesh

STUDY = 'carotid-survey'
SOURCE = Path(__file__).parent / STUDY
RUNTIME = ('index.html', 'survey.css', 'survey.js', 'survey-visuals.js', 'duplex.js',
           'volume.html', 'volume.css', 'volume.js', 'volume-contours.js', 'caliper-record.js',
           'review/source-vs-stitch.webp', 'review/distal-cca-measurements.webp')


def acquisition_recipe_sha256(source):
    names = ('build_survey.py', 'reconstruction.py', 'bmode_volume.py', 'survey_echo.py', 'branch_geometry.py', 'source-manifest.json',
             '../build_breast.py', '../build_study.py', '../geometry.py', '../prepare_scenes.py')
    return sha256(b''.join((source / name).read_bytes() for name in names))


def survey_files(stage, gallery_references, files):
    folder = stage / STUDY / 'data'
    if not folder.exists():
        return None
    seal = folder / 'delivery.json'
    if not seal.is_file():
        raise ValueError('Incomplete carotid survey acquisition')
    inventory = json.loads(seal.read_text())
    for name, digest in inventory.items():
        if not re.fullmatch(r'protocol-geometry\.json|(?:scenes|media|volumes)/[\w.-]+', name):
            raise ValueError(f'Unexpected carotid survey asset: {name}')
        source = folder / name
        if not source.is_file() or sha256(source.read_bytes()) != digest:
            raise ValueError(f'Carotid survey acquisition identity mismatch: {name}')
        files[f'{STUDY}/data/{name}'] = source

    geometry = json.loads((folder / 'protocol-geometry.json').read_text())
    if geometry.get('acquisitionRecipeSha256') != acquisition_recipe_sha256(SOURCE):
        raise ValueError('Rebuild the carotid survey with the current acquisition recipe')
    wanted = {'protocol-geometry.json', geometry['context']['skinPath']}
    wanted.update(part['path'] for part in geometry['context']['parts'])
    protocol = json.loads((SOURCE / 'protocol.json').read_text())
    if {s['id'] for s in geometry['stations']} != {s['id'] for s in protocol['stations']}:
        raise ValueError('Carotid survey protocol and station geometry disagree')
    sides = {'right', 'left'}
    if any(set(geometry[key]) != sides for key in ('tracking', 'reconstructions', 'volumes')):
        raise ValueError('Carotid survey requires both sides')
    for side in sorted(sides):
        views = list(geometry['tracking'][side])
        if len(views) < 3 or len({p['id'] for p in views}) != len(views):
            raise ValueError(f'Incomplete carotid tracking stack: {side}')
        for station in geometry['stations']:
            if station['side'] == side and station['available']:
                views.extend(station['views'].values())
                if 'measurementView' in station:
                    views.append(station['measurementView'])
                if 'forkEvidence' in station:
                    for labels in station['forkEvidence']['arterialMaskPaths'].values():
                        wanted.update(labels.values())
        for view in views:
            wanted.update([view['path'], view['lumenMaskPath']])
            if 'dopplerMaskPath' in view:
                wanted.add(view['dopplerMaskPath'])
        recon = geometry['reconstructions'][side]
        wanted.update(recon['sourcePaths'].values())
        wanted.update([recon['reconstructionPath'], geometry['volumes'][side]['path']])
    if wanted != inventory.keys():
        raise ValueError('Carotid acquisition inventory differs from its registered geometry')

    sources = json.loads((SOURCE / 'sources.json').read_text())
    for id_, row in sources.items():
        path = f'{STUDY}/media/{id_}.webp'
        source = SOURCE.parent / path
        if id_ in gallery_references or row['path'] != path or sha256(source.read_bytes()) != row['sha256']:
            raise ValueError(f'Unexpected carotid duplex reference: {id_}')
        validate_image(source)
        files[path] = source
    gallery_references.update(sources)
    for station in protocol['stations']:
        if not station['referenceIds'] or set(station['referenceIds']) - gallery_references.keys():
            raise ValueError(f"Missing acquired comparison at {station['id']}")
    for name in RUNTIME:
        files[f'{STUDY}/{name}'] = SOURCE / name
    files[f'{STUDY}/LICENSE.txt'] = SOURCE.parents[2] / 'sources/datasets/z-anatomy/salivary-region/License.txt'
    # Records persist in this tab. Invalidate old measurements if their anatomy,
    # acquisition or velocity model changes.
    protocol['datasetId'] = sha256(seal.read_bytes() + (SOURCE / 'protocol.json').read_bytes()
                                   + (SOURCE / 'duplex.js').read_bytes())
    protocol['displaySkinPath'] = 'skin-display.mesh'
    return protocol, exterior_mesh((folder / geometry['context']['skinPath']).read_bytes())
