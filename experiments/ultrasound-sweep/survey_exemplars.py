"""Bind worked survey chapters to their separately registered teaching subjects."""

import json
import math
from pathlib import Path

from delivery import read_poses, sha256
from geometry import RASTER_SIZE

CONSUMER = Path(__file__).with_name('cases') / 'organs/consumer.json'


def bind_chord(tour, chord, frame):
    if chord['frame'] != frame:
        raise ValueError('Saved chord does not bind the chapter evidence frame')
    left, right = chord['endpointsPx']
    width, height = RASTER_SIZE
    pitch = max(.41, tour['sectorDepthMm'] / (height - 21))
    if (any(len(point) != 2 or not (0 <= point[0] < width and 0 <= point[1] < height)
            for point in (left, right))
            or not math.isclose(math.dist(left, right) * pitch, chord['millimetres'], abs_tol=.05)):
        raise ValueError('Invalid pole-to-pole raster calibration')
    tour['savedChord'] = chord
    return f"Pole-to-pole chord {chord['millimetres']:.1f} mm · across the medial hilar recess"


def configure(destination, tours, evidence):
    by_id = {tour['id']: tour for tour in tours}
    for consumer in json.loads(CONSUMER.read_text())['consumers']:
        tour = by_id.get(consumer['sweep'])
        if tour is None:
            continue
        case, chapter_id = consumer['case'], consumer['chapter']
        chapter, = [row for row in evidence[case] if row['id'] == chapter_id]
        pin, = consumer['pins']
        part = tour['organ']
        if pin['requirement'] != f'part:{part}':
            raise ValueError(f'{case}/{chapter_id}: chapter pin must identify the sweep target')
        root = tour['assetRoot'].removeprefix('./')
        mesh = tour.get('meshPaths', {}).get(part, root + f'scenes/{part}.mesh')
        if sha256((destination / mesh).read_bytes()) != pin['sha256']:
            raise ValueError(f'{case}/{chapter_id}: staged mesh must match the chapter asset pin')
        pose_path = root + 'sweep.js'
        frame = chapter['evidenceFrame']
        if (sha256((destination / pose_path).read_bytes()) != consumer['poseSha256']
                or frame != consumer['frame'] or not 0 <= frame < len(read_poses(destination / pose_path))):
            raise ValueError(f'{case}/{chapter_id}: chapter must use the reviewed acquisition and frame')
        placement = dict(case='s1233', sweep=tour['id'], frame=frame,
                         export={key: pin[key] for key in ('asset', 'revision', 'export')})
        measurement = None
        if chord := consumer.get('savedChord'):
            placement['chord'] = chord
            measurement = bind_chord(tour, chord, frame)
        tour.setdefault('meshSha256', {})[part] = pin['sha256']
        inputs = [pose_path, root + f'media/scan-{frame:02}.webp', root + f'media/section-{frame:02}.webp',
                  tour.get('meshPaths', {}).get('torso', root + 'scenes/torso.mesh')]
        chapter.update(title=consumer['title'], observation=consumer['observation'], measurement=measurement,
                       sourceSweep=tour['id'], reviewMeshes={part: dict(path=mesh, placement=placement, inputs=inputs)})
