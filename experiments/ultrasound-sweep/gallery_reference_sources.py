"""Package retained Gallery surfaces for independent inspection in the workbench."""

import json
import re
from pathlib import Path

from assetkit import AssetKitError, AssetRegistry
from assetkit.blobs import LFS_HEADER, parse_pointer, read_verified, safe_path
from assetkit.ultrasound import read_gallery_references
from med_assets.glb import decode

from display_body import ROOT, primitive_stream, ras_from_gltf
from prepare_scenes import mesh_bytes


def require_reference(registry, donor, required_nodes):
    """Check the package owner's stored frame and selectors before interpreting positions."""
    _, _, export = registry.require_record_export(donor.ref)
    frame = export.frame
    if (frame is None or frame.convention != 'glb-y-up-m' or frame.units != 'm'
            or not {'right-handed', 'Y-up'} <= set(frame.axes)):
        raise AssetKitError(f'Gallery donor {donor.slot} requires a native metre-valued glTF frame')
    if export.format != 'glb' or export.sha256 is None or export.bytes is None:
        raise AssetKitError(f'Gallery donor {donor.slot} requires an identity-pinned GLB')
    claims = {selector for part in export.parts for selector in part.selectors}
    if missing := set(required_nodes) - claims:
        raise AssetKitError(f'Missing package selectors for Gallery donor {donor.slot}: {sorted(missing)}')
    return export


def load_reference(repo, export, required_nodes, *, optional=False):
    """Validate and decode a selected GLB, or omit optional unavailable bytes."""
    if optional:
        try:
            with safe_path(repo, export.path).open('rb') as stream:
                prefix = stream.read(1025)
        except FileNotFoundError:
            return None
        if prefix.startswith(LFS_HEADER):
            try:
                digest, size = parse_pointer(prefix)
            except ValueError as exc:
                raise AssetKitError(f'Invalid Gallery donor LFS pointer: {export.path}') from exc
            if digest != export.sha256 or size != export.bytes:
                raise AssetKitError(f'Gallery donor pointer identity mismatch: {export.path}')
            return None
    raw = read_verified(repo, export.path, export.sha256, export.bytes)
    doc, binary = decode(raw)
    if any({'matrix', 'translation', 'rotation', 'scale'} & node.keys() for node in doc['nodes']):
        raise ValueError(f'Unexpected transform in Gallery donor: {export.path}')
    nodes = {node['name']: node for node in doc['nodes'] if 'mesh' in node}
    if missing := set(required_nodes) - nodes.keys():
        raise ValueError(f'Missing named part in Gallery donor {export.path}: {sorted(missing)}')
    return doc, binary


def mammary_reference(repo=ROOT, required_nodes=()):
    donor = read_gallery_references(repo).mammary()
    registry = AssetRegistry.load_records(repo, (donor.ref.record,))
    return require_reference(registry, donor, set(donor.nodes) | set(required_nodes))


def srgb_channel(value):
    """Convert a glTF linear color channel to an 8-bit CSS channel."""
    srgb = 12.92 * value if value <= .0031308 else 1.055 * value ** (1 / 2.4) - .055
    return f'{round(srgb * 255):02x}'


def write_gallery_donors(destination, source_root=ROOT):
    """Copy the selected native GLB triangles into the viewer's RAS-mm mesh format."""
    sources = read_gallery_references(source_root).donors
    registry = AssetRegistry.load_records(source_root, (donor.ref.record for donor in sources))
    records = []
    upstream = 'https://github.com/qianyizhang/med-assets/blob/main/'
    for donor in sources:
        part_ids = [part for part, _ in donor.nodes.values()]
        if (not part_ids or len(part_ids) != len(set(part_ids))
                or any(not re.fullmatch(r'[a-z0-9][a-z0-9-]*', part) for part in part_ids)):
            raise ValueError(f'Invalid display part IDs for Gallery donor: {donor.slot}')
    inputs = [(donor, require_reference(registry, donor, donor.nodes)) for donor in sources]
    payloads = [(donor, export, load_reference(source_root, export, donor.nodes, optional=True))
                for donor, export in inputs]
    for donor, export, payload in payloads:
        if payload is None:
            continue
        doc, binary = payload
        nodes = {node['name']: node for node in doc['nodes'] if 'mesh' in node}
        key = donor.runtime_case
        folder = destination / 'development' / 'gallery-sources' / key
        folder.mkdir(parents=True, exist_ok=True)
        guide = donor.guide or Path(export.path).with_name('README.md').as_posix()
        for name, (part, label) in donor.nodes.items():
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
                'assetId': f'library/{donor.slot}', 'assetRevision': donor.edition,
                'assetLabel': donor.label, 'title': donor.label, 'sourceSpace': donor.space,
                'mesh': output.relative_to(destination).as_posix(), 'scale': 1,
                'color': '#' + ''.join(srgb_channel(v) for v in (red, green, blue)), 'opacity': opacity,
                'url': upstream + guide, 'sourceNode': name, 'sourceSha256': export.sha256,
                'credit': donor.credit, 'attribution': upstream + donor.attribution,
            })
    (destination / 'development' / 'gallery-donors.json').write_text(json.dumps(records, indent=2) + '\n')
