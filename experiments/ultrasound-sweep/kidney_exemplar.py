"""Bind one worked survey chapter to its separate registered s1233 exemplar."""

import json
import math
from pathlib import Path

from delivery import read_poses, sha256
from geometry import RASTER_SIZE

HERE = Path(__file__).resolve().parent
CONSUMER = HERE / 'cases/organs/consumer.json'


def configure(destination, tours, evidence):
    consumer, = json.loads(CONSUMER.read_text())['consumers']
    tour = next((row for row in tours if row['id'] == consumer['sweep']), None)
    if tour is None:
        return
    case, chapter_id = consumer['case'], consumer['chapter']
    chapter, = [row for row in evidence[case] if row['id'] == chapter_id]
    pin, = consumer['pins']
    part = tour['organ']
    mesh = tour.get('meshPaths', {}).get(part, tour['assetRoot'] + f'scenes/{part}.mesh')
    mesh = mesh.removeprefix('./')
    if sha256((destination / mesh).read_bytes()) != pin['sha256']:
        raise ValueError(f'{case}/{chapter_id}: staged kidney must match the chapter asset pin')
    root = tour['assetRoot']
    pose_path = root + 'sweep.js'
    if sha256((destination / pose_path).read_bytes()) != consumer['poseSha256']:
        raise ValueError(f'{case}/{chapter_id}: saved calipers need the reviewed acquisition pose')
    chord = consumer['savedChord']
    frame = chord['frame']
    poses = read_poses(destination / pose_path)
    if chapter['evidenceFrame'] != frame or frame >= len(poses):
        raise ValueError(f'{case}/{chapter_id}: saved chord does not bind the evidence frame')
    left, right = chord['endpointsPx']
    width, height = RASTER_SIZE
    pitch = max(.41, tour['sectorDepthMm'] / (height - 21))
    if (any(len(point) != 2 or not (0 <= point[0] < width and 0 <= point[1] < height)
            for point in (left, right))
            or not math.isclose(math.dist(left, right) * pitch, chord['millimetres'], abs_tol=.05)):
        raise ValueError(f'{case}/{chapter_id}: invalid pole-to-pole raster calibration')
    tour['savedChord'] = chord
    tour['meshSha256'] = {part: pin['sha256']}
    chapter.update(
        title='Right kidney · s1233 teaching exemplar',
        observation=consumer['observation'],
        measurement=f"Pole-to-pole chord {chord['millimetres']:.1f} mm · across the medial hilar recess",
        sourceSweep=tour['id'],
        reviewMeshes={part: dict(
            path=mesh,
            placement=dict(case='s1233', sweep=tour['id'], frame=frame, chord=chord,
                           export={key: pin[key] for key in ('asset', 'revision', 'export')}),
            inputs=[pose_path, root + f'media/scan-{frame:02}.webp', root + f'media/section-{frame:02}.webp',
                    tour.get('meshPaths', {}).get('torso', root + 'scenes/torso.mesh')],
        )},
    )
