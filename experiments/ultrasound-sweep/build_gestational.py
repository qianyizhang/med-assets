"""Build the modeled mid- and late-trimester transabdominal sweeps."""

import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation, Slerp

from build_abdomen import ImagingGrid, axes, measure_landmark, overlay, section_palette, section_palette_sha256
from build_breast import section_mask
from build_study import fine_scatter
from delivery import sha256, sweep_files, write_manifest
from fit_abdomen import outer_contact_offsets
from geometry import FRAME_COUNT, LENS_RADIUS_MM, RASTER_SIZE, SECTOR_HALF_ANGLE_DEG, VOXEL_MM
from gestational_anatomy import BONES, Gestation
import gestational_anatomy
from prepare_scenes import mesh_bytes

HERE = Path(__file__).resolve().parent
TRACKS = HERE / 'gestational-tracks.json'
FLUIDS = {
    'maternal_bladder', 'stomach', 'renal_pelves', 'fetal_bladder', 'umbilical_vein', 'umbilical_arteries',
    'ventricles', 'cavum', 'cisterna_magna', 'orbits', 'left_atrium', 'right_atrium',
    'left_ventricle', 'right_ventricle', 'aortic_outflow', 'pulmonary_outflow', 'superior_vena_cava', 'trachea',
    'cervical_canal', 'nares',
}
BASE_FIELDS = {'torso', 'uterus', 'amniotic_cavity', 'placenta', 'fetus', 'cord'}
DETAIL_WIDTH_MM = {
    'pregnancy-mid-brain': [87, 91, 91, 69, 99],
    'pregnancy-mid-heart': [51, 49, 49, 49, 49],
    'pregnancy-mid-abdomen': [71, 68, 68, 64],
    'pregnancy-mid-spine-limbs': [125, 70, 52, 65],
    'pregnancy-late-presentation': [None, None, 138],
}


def read_tracks():
    data = json.loads(TRACKS.read_text())
    tracks = []
    for group in data['tracks']:
        track = {**data['shared'], **data['stages'][group['pregnancyStage']], **group}
        track['parts'] = [
            {'id': name, 'label': label, 'color': color,
             'opacity': opacity if name != 'fetus' else track['fetusOpacity']}
            for name in track['parts'] for label, color, opacity in [data['parts'][name]]
        ]
        widths = DETAIL_WIDTH_MM.get(track['id'], ())
        track['detailFrames'] = [stop['frame'] for stop, width in zip(track['stops'], widths) if width]
        tracks.append(track)
    return tracks


def pose_recipe_sha256(slug):
    track = next(track for track in read_tracks() if track['id'] == slug)
    return sha256(json.dumps(track['windows'], separators=(',', ':')).encode())


def model_recipe_sha256():
    return sha256(Path(gestational_anatomy.__file__).read_bytes() + Path(__file__).read_bytes())


def delivery_files(track):
    names = ['torso', *(part['id'] for part in track['parts'])]
    details = [f'media/detail-{kind}-{frame:02}.webp'
               for kind in ('scan', 'section') for frame in track['detailFrames']]
    return sweep_files(names) + details


def poses(track, model, torso):
    windows = track['windows']
    stations = [w['frame'] for w in windows]
    aim = np.array([model.point(w['point'], w['space']) for w in windows])
    key_rotations = Rotation.from_matrix([
        axes(*(model.direction(w[key], w['space'], w['point']) for key in ('outward', 'marker')))
        for w in windows
    ])
    turn = Slerp(stations, key_rotations)
    frames = []
    aims = []
    for i in range(FRAME_COUNT):
        target = np.array([np.interp(i, stations, dimension) for dimension in aim.T])
        rotation = turn(i)
        width, _, beam = rotation.as_matrix().T
        if model.torso(target) >= 0:
            raise ValueError(f'{track["id"]} frame {i} aims outside the maternal exterior')
        distance = brentq(lambda depth: model.torso(target - beam*depth), 0, 450)
        contact = target - beam*distance
        frames.append({
            'contact': (contact/VOXEL_MM).tolist(),
            'width': width.tolist(),
            'beam': beam.tolist(),
            'degrees': round(float(np.rad2deg((rotation*key_rotations[0].inv()).magnitude())), 1),
        })
        aims.append((target, distance))

    contacts, beams = (np.array([f[key] for f in frames]) for key in ('contact','beam'))
    corrections = outer_contact_offsets(*torso, contacts, beams)
    analytic_error = float(np.max(np.abs(corrections)))
    if analytic_error > .8:
        raise ValueError(f'{track["id"]} central skin mismatch: {analytic_error:.3f} mm')
    # Refine the rendered contact on the exported exterior. Translation along
    # the beam preserves the intended plane through the anatomical target.
    contacts += beams*corrections[:,None]/VOXEL_MM
    residual = float(np.max(np.abs(outer_contact_offsets(*torso, contacts, beams))))
    for i, contact in enumerate(contacts):
        frames[i]['contact'] = contact.tolist()
        target, depth = aims[i]
        aims[i] = target, depth-corrections[i]
    travel = np.linalg.norm(np.diff(contacts, axis=0), axis=1) * VOXEL_MM
    if travel.max() > 18 or travel.sum() < 13:
        raise ValueError(f'{track["id"]} discontinuous or static skin path: {travel.sum():.1f} mm total, '
                         f'{travel.max():.1f} mm biggest step')
    return frames, aims, {
        'surfaceMaxOuterContactErrorMm': round(residual, 3),
        'maximumAnalyticToMeshContactAdjustmentMm': round(analytic_error, 3),
        'skinTravelMm': round(float(travel.sum()), 2),
        'maxSkinStepMm': round(float(travel.max()), 2),
    }


def sample_section(model, track, grid, frame):
    """Evaluate the section in the same geometry used to create the scene."""
    xyz = grid.coordinates(frame, grid.x, grid.y)
    names = BASE_FIELDS | {part['id'] for part in track['parts']}
    fields = model.sample(xyz*VOXEL_MM, sorted(names))
    clipped = grid.field & (fields['torso'] <= 0)
    labels = {name: (field <= 0) & clipped for name, field in fields.items()}
    regions = labels.copy()
    in_fetus = labels['fetus']
    occupied = in_fetus | labels['placenta'] | labels['cord']
    regions['amniotic_cavity'] = labels['amniotic_cavity'] & ~occupied
    regions['cord'] = labels['cord'] & ~(in_fetus | labels['placenta'])
    if 'ventricles' in labels:
        regions['ventricles'] = labels['ventricles'] & ~labels['choroid']
    if 'kidneys' in labels:
        regions['kidneys'] = labels['kidneys'] & ~labels['renal_pelves']

    scatter = fine_scatter(xyz)
    broad = fine_scatter(xyz*.32)
    depth_under_skin = -fields['torso']
    fat = np.exp(-((depth_under_skin - 8 - 2*broad)/6.2)**2)
    fascia = np.exp(-((depth_under_skin - 16 - 2*broad)/1.3)**2)
    common = 39 + 85*scatter + 28*broad
    intensity = common*(1-.32*fat)+32*fascia
    intensity = np.where(regions['uterus'], 53+.88*common, intensity)
    intensity = np.where(regions['amniotic_cavity'], 3+.054*common, intensity)
    intensity = np.where(regions['placenta'], 45+.94*common, intensity)
    intensity = np.where(regions['cord'], 46+.86*common, intensity)
    intensity = np.where(in_fetus, 17+.92*common, intensity)
    for name in ('lungs', 'heart', 'kidneys', 'thalami', 'cerebellum', 'choroid', 'upper_lip', 'diaphragm'):
        if name in regions:
            boost = 52 if name in {'lungs','choroid','upper_lip','diaphragm'} else 19
            intensity = np.where(regions[name], boost+1.07*common, intensity)
    for name in sorted(FLUIDS & regions.keys()):
        intensity = np.where(regions[name], 4+.10*common, intensity)
    for name in sorted(BONES & regions.keys()):
        intensity = np.where(regions[name], 152+.57*common, intensity)
    if 'falx' in regions:
        normal = np.cross(frame['width'],frame['beam'])
        direction = model.rotation[:, 0]
        falloff = 1-abs(normal @ direction)
        intensity = np.where(regions['falx'], (36+98*falloff)+.60*common, intensity)
    softened = nd.gaussian_filter(intensity, (.75, .9))
    dy, dx = np.gradient(softened)
    edge = np.abs(dy*np.cos(grid.angle)+dx*np.sin(grid.angle))
    skin = 76*np.exp(-((depth_under_skin-.85)/.9)**2)
    gray = (softened+1.23*edge+skin)*np.exp(-np.maximum(grid.depth,0)/420)
    image = np.where(clipped, np.clip(gray, 0, 248), 0).astype(np.uint8)
    return image, labels, regions


def detail_roi(grid, depth, span):
    width, height = RASTER_SIZE
    pitch = grid.x[0,1]-grid.x[0,0]
    ticks = int(np.round(span/pitch/10))
    area_w, area_h = 10*ticks, 7*ticks
    center_y = (depth-grid.y[0,0])/pitch
    left = (width-area_w)//2
    top = int(np.clip(round(center_y-area_h/2), 0, height-area_h))
    if area_w >= width or area_h >= height or min(area_w,area_h) < 60:
        raise ValueError(f'Invalid comparison detail {area_w} × {area_h} for span {span} mm')
    return [left, top, left+area_w, top+area_h]


def stage_volumes(model):
    # Count nonoverlapping materials on one uniform stage grid in the
    # uterus's native coordinates. Mesh shell volume alone includes fetus,
    # placenta and cord and therefore overstates the fluid.
    pitch = 2.8
    x, y, z = np.meshgrid(np.arange(-91,92,pitch), np.arange(-81,92,pitch),
                          np.arange(-117,231,pitch), indexing='ij', sparse=True)
    local = (x,y,z)
    world = tuple(origin+sum(value*axis for value,axis in zip(local,basis,strict=True))
                  for origin,basis in zip(model.stage.centre,model.rotation,strict=True))
    cavity = model.cavity(world) <= 0
    fetus = model.fetus(local) <= 0
    placental = model.placenta(world) <= 0
    cord = model.cord(world) <= 0
    groups = {
        'cavity': cavity, 'fetus': fetus, 'placentaInsideCavity': placental & cavity,
        'cordInsideCavity': cord & cavity & ~fetus & ~placental,
        'netFluid': cavity & ~(fetus | placental | cord),
    }
    volumes = {name:round(np.count_nonzero(mask)*pitch**3/1000,1) for name,mask in groups.items()}
    min_ml, max_ml = (390, 730) if model.name == 'mid' else (790, 1340)
    if not min_ml < volumes['netFluid'] < max_ml:
        raise ValueError(f'{model.name} net amniotic fluid outside the authored design range: {volumes}')
    return {'modelVolumeGridMm': pitch, 'modelVolumesMl': volumes}


def check_maternal_geometry(model, meshes):
    contents = ('uterus','placenta','fetus','cord')
    clearance = {}
    for name in contents:
        value = -float(model.torso(meshes[name][0].T*VOXEL_MM).max())
        if value < 0:
            raise ValueError(f'{model.name} {name} extends beyond skin by {-value:.1f} field millimetres')
        clearance[name] = round(value,2)
    fetal_shell = meshes['fetus'][0].T*VOXEL_MM
    fetal_in_sac = -float(model.cavity(fetal_shell).max())
    placental_clearance = float(model.placenta(fetal_shell).min())
    if min(fetal_in_sac, placental_clearance) <= 0:
        raise ValueError(f'{model.name} fetus must fit in fluid and clear the placenta: '
                         f'{fetal_in_sac:.2f}, {placental_clearance:.2f}')
    cord_start = float(model.fetus(model.local_coordinates(model.cord_path[0])))
    cord_end = float(model.placenta(model.cord_path[-1]))
    if max(cord_start, cord_end) >= 0:
        raise ValueError(f'{model.name} cord does not enter the fetal and placental boundaries')
    receipt = dict(minMaternalEnvelopeClearanceFieldMm=clearance,
                   minFetalCavityClearanceFieldMm=round(fetal_in_sac,2),
                   placentalClearanceFieldMm=round(placental_clearance,2),
                   cordInsertionSignedFieldMm=[round(cord_start,2),round(cord_end,2)],
                   **stage_volumes(model))
    if model.fluid_span_endpoints is not None:
        lower, upper = model.fluid_span_endpoints
        samples = np.linspace(lower,upper,103)[1:-1].T
        if np.max(model.fluid_constraint(samples)) >= 0 or not 22 < upper[1]-lower[1] < 60:
            raise ValueError('The vertical locator must reach real boundaries across unobstructed fluid')
        receipt['fluidSpanEndpointsRasMm'] = model.fluid_span_endpoints.round(2).tolist()
    return receipt


def write_media(root, stem, gray, labels, palette):
    Image.fromarray(gray).save(root/f'{stem[0]}scan-{stem[1]:02}.webp', quality=91)
    Image.fromarray(overlay(gray, labels, palette)).save(root/f'{stem[0]}section-{stem[1]:02}.webp', quality=88)


def mesh_agreement(mesh, target_mask, grid, frame):
    contact, width, beam = (np.asarray(frame[key]) for key in ('contact', 'width', 'beam'))
    actual = section_mask(mesh, contact, width, beam, grid.x[0], grid.y[:,0]) & grid.field
    return float(2*np.count_nonzero(actual & target_mask)/(actual.sum()+target_mask.sum()))


def build_track(track, output, model, meshes, packed, anatomy):
    frames, aims, report = poses(track, model, meshes['torso'])
    grid = ImagingGrid(track['sectorDepthMm'])
    names = ['torso', *(part['id'] for part in track['parts'])]
    palette = section_palette(track)
    media, scenes = output/'media', output/'scenes'
    media.mkdir()
    scenes.mkdir()
    for name in names:
        (scenes/f'{name}.mesh').write_bytes(packed[name])
    evidence, rois = {}, {}
    checks = {w['frame']: w['minimums'] for w in track['windows'][1:]}
    widths = {stop['frame']:width for stop,width in
              zip(track['stops'], DETAIL_WIDTH_MM.get(track['id'], ())) if width}
    for i, frame in enumerate(frames):
        gray, labels, regions = sample_section(model, track, grid, frame)
        if np.count_nonzero(labels['amniotic_cavity']) < 120:
            raise ValueError(f'{track["id"]} frame {i} does not intersect the uterine cavity')
        write_media(media, ('',i), gray, regions, palette)
        if i in checks:
            target, depth = aims[i]
            values = {name: measure_landmark(labels[name], gray) for name in checks[i]}
            for name, limit in checks[i].items():
                if values[name]['largestSectionPixels'] < limit:
                    raise ValueError(f'{track["id"]} frame {i} misses {name}: {values[name]} (need {limit})')
                agreement = mesh_agreement(meshes[name], labels[name], grid, frame)
                if agreement < .90:
                    raise ValueError(f'{track["id"]} frame {i} {name} mesh Dice is {agreement:.3f}')
                values[name]['meshSectionDice'] = round(agreement, 4)
            if track['id'] == 'pregnancy-mid-brain' and i == 38:
                components, _ = nd.label(labels['nares'])
                if np.count_nonzero(np.bincount(components.ravel())[1:] >= 7) != 2:
                    raise ValueError('The coronal face section must include two distinct nares')
            if track['id'] == 'pregnancy-mid-heart' and i == 48:
                branches = labels['aortic_outflow'] & labels['pulmonary_outflow']
                if np.count_nonzero(branches) < 7:
                    raise ValueError('The aortic and ductal limbs must meet in the three-vessels-and-trachea plane')
                values['vesselJunctionPixels'] = int(np.count_nonzero(branches))
            if i in widths:
                roi = detail_roi(grid, depth, widths[i])
                zoom = ImagingGrid(track['sectorDepthMm'], roi=roi)
                detail, _, regions = sample_section(model, track, zoom, frame)
                write_media(media, ('detail-', i), detail, regions, palette)
                rois[str(i)] = roi
            skin_mm = np.array(frame['contact'])*VOXEL_MM
            depths = np.arange(0., max(depth+25,1), .5)
            ray = skin_mm[:,None]+np.array(frame['beam'])[:,None]*depths
            uterine = np.flatnonzero(model.uterine_contour(ray,6.) <= 0)
            evidence[str(i)] = {
                'landmarks': values,
                'firstUterineWallDepthMm': float(depths[uterine[0]]) if uterine.size else None,
                'contactRasMm': (np.array(frame['contact'])*VOXEL_MM).round(3).tolist(),
                'targetRasMm': target.round(3).tolist(),
                'beam': frame['beam'],
                'width': frame['width'],
            }
    (output/'sweep.js').write_text('const sweep = '+json.dumps(frames, separators=(',',':'))+';\n')
    (output/'verification.json').write_text(json.dumps({
        'case': track['case'],
        'coordinateFrame': 'authored maternal RAS in 1.5 mm scene units',
        'pregnancyStage': track['pregnancyStage'],
        'voxelMm': VOXEL_MM,
        'exterior': track['exterior'],
        'sectorDepthMm': track['sectorDepthMm'],
        'sectorHalfAngleDeg': SECTOR_HALF_ANGLE_DEG,
        'lensRadiusMm': LENS_RADIUS_MM,
        'poseRecipeSha256': pose_recipe_sha256(track['id']),
        'modelRecipeSha256': model_recipe_sha256(),
        'sectionPaletteSha256': section_palette_sha256(track),
        **report, **anatomy,
        'detailRois': rois,
        'frames': evidence,
    }, indent=2)+'\n')
    write_manifest(output, delivery_files(track))
    print(f'{track["id"]}: {len(frames)} poses, {report["skinTravelMm"]:.1f} mm skin travel, '
          f'{report["surfaceMaxOuterContactErrorMm"]:.3f} mm maximum central contact error', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sweeps_dir', type=Path)
    parser.add_argument('--only', action='append', choices=[track['id'] for track in read_tracks()],
                        help='Build selected routes for review in a separate staging directory')
    args = parser.parse_args()
    tracks = [track for track in read_tracks() if not args.only or track['id'] in args.only]
    if any((args.sweeps_dir/track['id']).exists() for track in tracks):
        parser.error('Choose a fresh destination for the staged pregnancy sweeps.')
    args.sweeps_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.sweeps_dir) as stage_path:
        staging = Path(stage_path)
        for phase in dict.fromkeys(track['pregnancyStage'] for track in tracks):
            group = [track for track in tracks if track['pregnancyStage'] == phase]
            model = Gestation(phase)
            names = {'torso', *BASE_FIELDS, *(part['id'] for track in group for part in track['parts'])}
            meshes = {name:model.mesh(name) for name in sorted(names)}
            anatomy = check_maternal_geometry(model, meshes)
            packed = {name:mesh_bytes(*mesh) for name, mesh in meshes.items()}
            for track in group:
                output = staging/track['id']
                output.mkdir()
                build_track(track,output,model,meshes,packed,anatomy)
        for track in tracks:
            (staging/track['id']).rename(args.sweeps_dir/track['id'])


if __name__ == '__main__':
    main()
