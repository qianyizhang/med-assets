"""Shared input inventory and identity checks for generated sweep assets."""

import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image

from geometry import FRAME_COUNT, RASTER_SIZE


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def sweep_files(mesh_names):
    return ['sweep.js', *(f'scenes/{name}.mesh' for name in mesh_names),
            *(f'media/{kind}-{i:02}.webp' for kind in ('scan', 'section') for i in range(FRAME_COUNT))]


def detail_files(stops):
    return [f'media/detail-{kind}-{stop["frame"]:02}.webp'
            for stop in stops if stop.get('detail') for kind in ('scan', 'section')]


def write_manifest(root, names):
    inventory = {name: sha256((root / name).read_bytes()) for name in names}
    (root / 'delivery.json').write_text(json.dumps(inventory, indent=2, sort_keys=True) + '\n')


def read_poses(path):
    text = path.read_text().strip()
    if not (text.startswith('const sweep = ') and text.endswith(';')):
        raise ValueError(f'Invalid sweep script: {path}')
    frames = json.loads(text.removeprefix('const sweep = ').removesuffix(';'))
    if not isinstance(frames, list) or len(frames) != FRAME_COUNT:
        raise ValueError(f'Expected {FRAME_COUNT} poses: {path}')
    for i, frame in enumerate(frames):
        try:
            points = np.array([frame[name] for name in ('contact', 'width', 'beam')], dtype=float)
            angle = frame['degrees']
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Invalid pose {i}: {path}') from exc
        if (points.shape != (3, 3) or not np.isfinite(points).all()
                or not isinstance(angle, (int, float)) or not np.isfinite(angle)
                or not np.allclose(points[1:] @ points[1:].T, np.eye(2), atol=1e-5)):
            raise ValueError(f'Invalid pose {i}: {path}')
    return frames


def validate_mesh(raw, path):
    if len(raw) >= 8:
        vertices, faces = struct.unpack_from('<2I', raw)
        if vertices and faces and len(raw) == 8 + 12 * (vertices + faces):
            positions = np.frombuffer(raw, '<f4', count=3 * vertices, offset=8)
            triangles = np.frombuffer(raw, '<u4', count=3 * faces, offset=8 + 12 * vertices)
            if np.isfinite(positions).all() and triangles.max() < vertices:
                return
    raise ValueError(f'Invalid packed mesh: {path}')


def validate_image(path, sweep_frame=False):
    try:
        with Image.open(path) as image:
            if image.format != 'WEBP' or (sweep_frame and image.size != RASTER_SIZE):
                raise ValueError(f'Unexpected WebP format or dimensions: {path}')
            image.load()
    except OSError as exc:
        raise ValueError(f'Cannot decode WebP: {path}') from exc


def verify_inventory(root, names):
    """Read older staging trees structurally; enforce exact hashes when a receipt is present."""
    manifest_path = root / 'delivery.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    if manifest is not None and manifest.keys() != set(names):
        raise ValueError(f'Sweep delivery inventory differs from the configured files: {manifest_path}')
    for name in names:
        path = root / name
        if not path.is_file():
            raise ValueError(f'Missing sweep input: {path}')
        if manifest is not None and sha256(path.read_bytes()) != manifest[name]:
            raise ValueError(f'Sweep delivery identity mismatch: {path}')
        if name == 'sweep.js':
            read_poses(path)
        elif name.endswith('.webp'):
            basename = Path(name).name.removeprefix('press-')
            validate_image(path, sweep_frame=basename.startswith(('scan-', 'section-', 'detail-')))
