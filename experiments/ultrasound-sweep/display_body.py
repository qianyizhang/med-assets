"""Fit the illustrative atlas exterior around the measured s1233 contact window."""
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree

from assetkit import AssetKitError, AssetRegistry
from assetkit.blobs import read_verified
from assetkit.ultrasound import read_exterior_atlas
from med_assets.glb import decode
from med_assets.glb_projection import stream
from geometry import VOXEL_MM

ROOT = Path(__file__).resolve().parents[2]
RIBS = {f'right {n} rib' for n in ('sixth', 'seventh', 'eighth', 'ninth', 'tenth')}
ATLAS_SUBJECT = 'BodyParts3D 4.0 reference atlas'
ATLAS_AXES = ('right-handed', 'Y-up', '+X atlas left', '+Y superior', '+Z anterior')


@dataclass(frozen=True)
class AtlasMesh:
    path: str
    sha256: str
    document: dict
    binary: bytes


@dataclass(frozen=True)
class BodyAtlas:
    skin: AtlasMesh
    skeleton: AtlasMesh
    rib_bounds: tuple[np.ndarray, np.ndarray]

    def source_digests(self):
        return source_digests(self.skin.sha256, self.skeleton.sha256)


def source_digests(skin, skeleton):
    return {'atlasSkinSha256': skin, 'atlasBonesSha256': skeleton}


def exterior_exports(repo):
    catalogue = read_exterior_atlas(repo)
    registry = AssetRegistry.load_records(repo, (ref.record for ref in catalogue.inputs()))
    exports = []
    for slot, ref in (('skin', catalogue.skin), ('skeleton', catalogue.skeleton)):
        _, revision, export = registry.require_record_export(ref)
        frame = export.frame
        if (frame is None or frame.convention != 'glb-y-up-m' or frame.units != 'm'
                or frame.axes != ATLAS_AXES or revision.provenance.subject != ATLAS_SUBJECT):
            raise AssetKitError(f'Exterior atlas {slot} requires the native BodyParts3D frame: {export.path}')
        if export.format != 'glb' or export.sha256 is None or export.bytes is None:
            raise AssetKitError(f'Exterior atlas {slot} requires an identity-pinned GLB: {export.path}')
        exports.append(export)
    return tuple(exports)


def load_body_atlas(repo=ROOT):
    skin_export, skeleton_export = exterior_exports(repo)

    def load(export):
        raw = read_verified(repo, export.path, export.sha256, export.bytes)
        document, binary = decode(raw)
        nodes = document['nodes']
        if any(any(key in node for key in ('matrix', 'rotation', 'scale', 'translation', 'children'))
               for node in nodes):
            raise AssetKitError(f'Exterior atlas expects flat native coordinates: {export.path}')
        return AtlasMesh(export.path, export.sha256, document, binary)

    skin = load(skin_export)
    skeleton = load(skeleton_export)
    skin_selectors = {selector for part in skin_export.parts if part.id == 'skin' for selector in part.selectors}
    if len(skin.document['nodes']) != 1 or skin.document['nodes'][0].get('mesh') != 0 or (
            skin.document['nodes'][0].get('name') not in skin_selectors):
        raise AssetKitError(f'Exterior atlas skin must bind the sole first mesh: {skin.path}')
    return BodyAtlas(skin, skeleton, atlas_rib_bounds(skeleton.document))


def expected_source_digests():
    skin, skeleton = exterior_exports(ROOT)
    return source_digests(skin.sha256, skeleton.sha256)


def atlas(path, digest):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f'Unexpected atlas input: {path}')
    return decode(raw)


def primitive_stream(doc, binary, index):
    acc = doc['accessors'][index]
    dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[acc['componentType']]
    return np.frombuffer(stream(doc, binary, acc), dtype=dtype)


def ras_from_gltf(xyz):
    return xyz[..., [0, 2, 1]] * [-1, 1, 1]


def atlas_rib_bounds(doc):
    bounds = {}
    for node in doc['nodes']:
        name = node['name'].partition(' ')[2]
        if name in RIBS:
            primitive = doc['meshes'][node['mesh']]['primitives'][0]
            accessor = doc['accessors'][primitive['attributes']['POSITION']]
            if name in bounds:
                raise ValueError(f'Duplicate atlas rib landmark: {name}')
            bounds[name] = accessor['min'], accessor['max']
    if bounds.keys() != RIBS:
        raise ValueError('Incomplete atlas rib landmarks')
    points = ras_from_gltf(np.asarray(list(bounds.values())).reshape((-1, 3)))
    return points.min(0), points.max(0)


def anterior_surface(ct_vertices, contacts):
    # Only the anterior branch of the CT envelope can define the abdominal patch.
    center = contacts.mean(0)
    in_window = (np.abs(ct_vertices[:, 0] - center[0]) < 90) & (np.abs(ct_vertices[:, 2] - center[2]) < 85)
    front = ct_vertices[in_window & (ct_vertices[:, 1] > center[1] - 45)]
    return LinearNDInterpolator(front[:, [0, 2]], front[:, 1])


def smooth_atlas(vertices, faces):
    """Soften the close-up silhouette with a 2 mm displacement limit in atlas metres."""
    edges = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    start, end = np.unique(np.concatenate((edges, edges[:, ::-1])), axis=0).T
    count = np.maximum(np.bincount(start, minlength=len(vertices)), 1)
    smooth = vertices.copy()
    for _ in range(5):
        average = np.column_stack([np.bincount(start, weights=axis[end], minlength=len(vertices)) / count
                                   for axis in smooth.T])
        smooth += .5 * (average-smooth)
    delta = smooth - vertices
    weight = .002 / np.maximum(.002, np.linalg.norm(delta, axis=1))
    return vertices + weight[:, None] * delta


def registered_atlas(rib_vertices, source):
    doc, binary = source.skin.document, source.skin.binary
    prim = doc['meshes'][0]['primitives'][0]
    vertices = ras_from_gltf(primitive_stream(doc, binary, prim['attributes']['POSITION']).reshape(-1, 3))
    faces = primitive_stream(doc, binary, prim['indices']).reshape(-1, 3)
    vertices = smooth_atlas(vertices, faces)
    low, high = source.rib_bounds
    scale = np.ptp(rib_vertices, axis=0) / (high-low)
    return (vertices-low) * scale + rib_vertices.min(0), faces


def fitted_surface(torso_vertices, rib_vertices, contacts, source):
    vertices, faces = registered_atlas(rib_vertices, source)
    front = anterior_surface(torso_vertices, contacts)
    projected = vertices[:, [0, 2]]
    distance, _ = cKDTree(contacts[:, [0, 2]]).query(projected)
    # The central footprint follows the measured CT surface. Smoothly fade the
    # displacement into the atlas trunk outside the probe neighborhood.
    fade = np.clip((distance - 23) / (78 - 23), 0, 1)
    weight = 1 - fade * fade * (3 - 2*fade)
    anterior = np.clip((vertices[:, 1] - contacts[:, 1].mean() + 58) / 22, 0, 1)
    weight *= anterior * anterior * (3 - 2*anterior)
    roi = weight > 0
    height = front(projected[roi])
    valid = np.flatnonzero(roi)[np.isfinite(height)]
    vertices[valid, 1] += weight[valid] * (height[np.isfinite(height)] - vertices[valid, 1])
    return vertices, faces


def check_contacts(vertices, faces, contacts, beams):
    """Intersect each central beam line with the fitted mesh at the contact window."""
    triangles = vertices[faces]
    centers = cKDTree(triangles.mean(axis=1))
    errors = []
    for contact, beam in zip(contacts, beams, strict=True):
        # Möller–Trumbore intersections in the local footprint (case voxel units).
        a, b, c = triangles[centers.query_ball_point(contact, 32)].transpose(1, 0, 2)
        ab, ac = b - a, c - a
        h = np.cross(beam, ac)
        det = np.einsum('ij,ij->i', ab, h)
        valid = np.abs(det) > 1e-9
        det = det[valid]
        offset = contact - a[valid]
        cross = np.cross(offset, ab[valid])
        u = np.einsum('ij,ij->i', offset, h[valid]) / det
        v = np.einsum('ij,j->i', cross, beam) / det
        distances = np.einsum('ij,ij->i', ac[valid], cross) / det
        hits = distances[(u >= 0) & (v >= 0) & (u + v <= 1)]
        if not hits.size:
            raise ValueError('Central probe ray misses the fitted abdominal surface.')
        errors.append(np.abs(hits).min() * VOXEL_MM)
    if max(errors) > 1:
        raise ValueError(f'Probe contact differs from the fitted surface by {max(errors):.2f} mm.')
    return max(errors)
