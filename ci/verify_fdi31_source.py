#!/usr/bin/env python3
"""Download-only check for the exact retained FDI31 package; no LFS operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from lfs_transport import Stop, download_source, validate_manifest, verify_bytes, require
from eye_teaching.build import unpack, accessor

MANIFEST_SHA256 = 'ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118'
MANIFEST = ROOT / 'ci/fdi31-source/manifest.json'


def consume(folder, manifest):
    """Parse the actual materialized GLB using the existing reader, not a render."""
    for obj in manifest['objects']:
        verify_bytes((folder / Path(obj['file']).name).read_bytes(), obj)
    model = folder / Path(manifest['objects'][0]['file']).name
    doc, binary = unpack(model.read_bytes())
    mesh_nodes = [n for n in doc['nodes'] if 'mesh' in n]
    expected = {'SWIRendo_31_T2/' + name for name in ('bone', 'pulp', 'dentin', 'enamel')}
    require({n.get('name') for n in mesh_nodes} == expected, 'Unexpected FDI31 layers')
    triangles = 0
    for node in mesh_nodes:
        for prim in doc['meshes'][node['mesh']]['primitives']:
            require(prim.get('mode', 4) == 4, 'Expected triangles')
            for i in [prim['indices'], *prim['attributes'].values()]:
                accessor(doc, binary, i)  # Existing parser checks the referenced byte range.
            count = doc['accessors'][prim['indices']]['count']
            require(count % 3 == 0, 'Incomplete triangle indices')
            triangles += count // 3
    require(triangles == 1328980, 'Unexpected retained triangle count')
    return {'glbParsed': True, 'meshLayers': sorted(expected),
            'triangles': triangles, 'imagesHashVerified': 4,
            'scope': 'GLB parse/layout and byte identity only; not rendering or anatomy'}


def verify(raw, output=None):
    manifest = validate_manifest(raw, MANIFEST_SHA256)
    if output is not None:
        output = Path(output)
        require(not output.exists() and not output.is_symlink(), 'Output must be a fresh directory')
        require(output.parent.is_dir(), 'Output parent must already exist')
    rows, payloads = [], []
    for obj in manifest['objects']:
        data = download_source(obj)
        if output is not None:
            payloads.append((Path(obj['file']).name, data))
        rows.append({'file': obj['file'], 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
    consumed = None
    if output is not None:
        output.mkdir()  # Exclusive: never overwrite existing review material.
        try:
            for name, data in payloads:
                with (output / name).open('xb') as target:
                    target.write(data)
            (output / 'README.md').write_text((ROOT / 'ci/fdi31-source/README.md').read_text())
            consumed = consume(output, manifest)
        except Exception:
            shutil.rmtree(output)
            raise
    return {'sourceOnly': True, 'materialized': output is not None, 'consumer': consumed, 'lfsHydrated': False,
            'manifestSha256': MANIFEST_SHA256, 'objects': rows,
            'totalBytes': manifest['totalBytes']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New directory under an existing parent; never repository media hydration')
    args = parser.parse_args()
    try:
        receipt = verify(MANIFEST.read_bytes(), args.output)
    except Stop as error:
        raise SystemExit('STOP: ' + str(error)) from None
    receipt['commit'] = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    receipt['eventCommit'] = os.environ.get('GITHUB_SHA')
    receipt['runId'] = os.environ.get('GITHUB_RUN_ID')
    encoded = json.dumps(receipt, sort_keys=True, indent=2)
    print(encoded)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as out:
            out.write('## FDI31 source download: passed\n\n'
                      '5 staged objects verified; no LFS upload/hydration or clinical acceptance.\n\n'
                      '```json\n' + encoded + '\n```\n')


if __name__ == '__main__':
    main()
