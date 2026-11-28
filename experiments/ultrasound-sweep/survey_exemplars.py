"""Bind worked survey chapters to their separately registered teaching subjects."""

import json
import math
from html import escape
from urllib.parse import urlencode
from pathlib import Path

from delivery import read_poses, sha256
from geometry import RASTER_SIZE

CASES = Path(__file__).with_name('cases')


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
    for path in sorted(CASES.glob('*/consumer.json')):
        for consumer in json.loads(path.read_text())['consumers']:
            if 'sweep' in consumer:
                bind_consumer(destination, by_id, evidence, consumer)


def bind_consumer(destination, by_id, evidence, consumer):
    tour = by_id.get(consumer['sweep'])
    if tour is None:
        return
    case, chapter_id = consumer['case'], consumer['chapter']
    chapter, = [row for row in evidence[case] if row['id'] == chapter_id]
    pin, = consumer['pins']
    presentation = consumer.get('presentation', 'primary')
    if presentation not in ('primary', 'companion'):
        raise ValueError(f'{case}/{chapter_id}: unknown exemplar presentation {presentation!r}')
    companion = presentation == 'companion'
    part = consumer['part'] if companion else tour['organ']
    slots = {item['id'] for item in tour['parts']}
    if pin['requirement'] != f'part:{part}' or part not in slots:
        raise ValueError(f'{case}/{chapter_id}: chapter pin must identify a declared sweep part')
    subject = tour.get('case', 's1233')
    requirement, = consumer['requirements']
    if requirement['subject'] != subject or pin['registration'] != 'native':
        raise ValueError(f'{case}/{chapter_id}: expected native registration on {subject}')
    if companion:
        port = {key: pin[key] for key in ('asset', 'revision', 'export', 'registration')}
        if tour.get('sceneAssets', {}).get(part) != port:
            raise ValueError(f'{case}/{chapter_id}: chapter pin differs from the registered scene port')
    root = tour['assetRoot'].removeprefix('./')
    mesh = tour.get('meshPaths', {}).get(part, root + f'scenes/{part}.mesh')
    if sha256((destination / mesh).read_bytes()) != pin['sha256']:
        raise ValueError(f'{case}/{chapter_id}: staged mesh must match the chapter asset pin')
    pose_path = root + 'sweep.js'
    frame = consumer['frame']
    worked_frame = consumer['workedFrame'] if companion else frame
    if (sha256((destination / pose_path).read_bytes()) != consumer['poseSha256']
            or chapter['evidenceFrame'] != worked_frame or not 0 <= frame < len(read_poses(destination / pose_path))):
        raise ValueError(f'{case}/{chapter_id}: chapter must use the reviewed acquisition and frame')
    placement = dict(case=subject, sweep=tour['id'], frame=frame,
                     export={key: pin[key] for key in ('asset', 'revision', 'export')})
    measurement = None
    if chord := consumer.get('savedChord'):
        placement['chord'] = chord
        measurement = bind_chord(tour, chord, frame)
    tour.setdefault('meshSha256', {})[part] = pin['sha256']
    inputs = [pose_path, root + f'media/scan-{frame:02}.webp', root + f'media/section-{frame:02}.webp',
              tour.get('meshPaths', {}).get('torso', root + 'scenes/torso.mesh')]
    if companion:
        exemplar = dict(subject=subject, sweep=tour['id'], frame=frame, part=part, observation=consumer['observation'])
        if 'exemplar' in chapter:
            raise ValueError(f'{case}/{chapter_id}: duplicate companion')
        chapter['exemplar'] = exemplar
        placement['exemplar'] = exemplar
        # The companion displays the whole sweep. A visible neighbor can change
        # the orientation task even while the target mesh and scan stay identical.
        placement['render'] = {key: tour[key] for key in ('focus', 'focusRadius', 'voxelMm', 'parts',
                              'overlayParts', 'sectorDepthMm', 'probeType', 'fieldShape', 'fieldWidthMm') if key in tour}
        inputs += ['scene.js', 'study.js']
        for item in sorted(slots - {part}):
            inputs.append(tour.get('meshPaths', {}).get(item, root + f'scenes/{item}.mesh'))
    else:
        chapter.update(title=consumer['title'], observation=consumer['observation'], measurement=measurement,
                       sourceSweep=tour['id'])
    chapter.setdefault('reviewMeshes', {})[part] = dict(path=mesh, placement=placement, inputs=inputs)


def companion_html(chapter):
    exemplar = chapter.get('exemplar')
    if exemplar is None:
        return ''
    query = urlencode({'sweep': exemplar['sweep'], 'frame': exemplar['frame'], 'embed': 1, 'layout': 'probe-scan'})
    label = escape(f"CT anatomy · {exemplar['subject']} · separate subject")
    url = escape('../../index.html?' + query, quote=True)
    return (f'<details class="ct-exemplar"><summary>{label}</summary><p>{escape(exemplar["observation"])}</p>'
            f'<iframe loading="lazy" title="{label}" data-src="{url}"></iframe></details>')
