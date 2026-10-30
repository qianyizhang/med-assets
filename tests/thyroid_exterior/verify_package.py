"""Verify hydrated thyroid derivative/evidence identities without rendering."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

REVIEW = 'reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01'


def require(value, message):
    if not value:
        raise ValueError(message)


def check_file(root, record):
    path = (root / record['file']).resolve()
    require(path.is_relative_to(root.resolve()), 'Reference escapes repository')
    data = path.read_bytes()
    require(len(data) == record['bytes'], f'Wrong byte size: {record["file"]}')
    require(hashlib.sha256(data).hexdigest() == record['sha256'],
            f'Wrong hash: {record["file"]}')
    return data


def glb_json(data):
    require(struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data)), 'GLB header')
    length, kind = struct.unpack_from('<II', data, 12)
    require(kind == 0x4E4F534A and length <= len(data)-20, 'GLB JSON chunk')
    return json.loads(data[20:20+length])


def verify(root):
    review = root / REVIEW
    record = json.loads((review / 'review.json').read_text())
    source = glb_json(check_file(root, record['source']))
    candidate = glb_json(check_file(root, record['artifact']))
    require(source['materials'] == candidate['materials'], 'Material changed')
    require(len(candidate['meshes']) == len(candidate['nodes']) == 1, 'Unexpected structure')
    extras = candidate['nodes'][0]['extras']
    require(extras['source_sha256'] == record['source']['sha256'], 'Wrong source extra')
    require(extras['runtime'] == 'unverified', 'Runtime claim changed')
    for key, value in source['nodes'][0]['extras'].items():
        require(extras[key] == value, f'Lost source metadata: {key}')
    bindings = json.loads((review / 'renders/raster-bindings.json').read_text())
    require(len(bindings) == 10 and len({b['file'] for b in bindings}) == 10,
            'Expected ten distinct images')
    for entry in bindings:
        data = check_file(root, dict(entry, file=f'{REVIEW}/renders/{entry["file"]}'))
        require(data[:8] == b'\x89PNG\r\n\x1a\n', 'Expected actual PNG')
        require(struct.unpack_from('>II', data, 16) == tuple(entry['pixels']), 'PNG dimensions')
        original = entry['file'].startswith('original-')
        require(entry['artifact_sha256'] == record['source' if original else 'artifact']['sha256'],
                'Image bound to wrong model')
    by_name = {b['file']: b for b in bindings}
    for view in ['whole', 'oblique', 'ridge-detail', 'reverse', 'side']:
        a, b = [by_name[f'{label}-{view}.png'] for label in ['original', 'updated']]
        for key in ['camera', 'target', 'orthoscale', 'pixels', 'samples', 'material']:
            require(a[key] == b[key], f'Mismatched comparison: {view}/{key}')
    plate = json.loads((review / 'comparison-binding.json').read_text())
    check_file(root, dict(plate, file=f'{REVIEW}/{plate["file"]}'))
    require(len(plate['source_images']) == 4, 'Expected four source images in comparison')
    for item in plate['source_images']:
        require(item == by_name[item['file']], 'Stale comparison source image')
    require(plate['artifact_sha256'] == record['artifact']['sha256']
            and plate['source_sha256'] == record['source']['sha256'], 'Stale comparison model')
    for receipt in ['build-record.json', 'export-check.json']:
        item = json.loads((review / receipt).read_text())
        actual = item['artifact']['sha256'] if 'artifact' in item else item['artifact_sha256']
        require(actual == record['artifact']['sha256'], 'Stale technical receipt')
    require(record['gates']['runtime']['status'] == 'unverified', 'Runtime gate promoted')
    require(record['gates']['tracheal_relationship']['status'] == 'unverified',
            'Tracheal gate promoted')
    print('PASS: source + derivative + 10 PNGs + comparison, matched views, source extras/material, receipt bindings')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    verify(parser.parse_args().root)
