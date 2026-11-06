"""Restore the ignored current seed from either exact retained snapshot, offline."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]


def restore(source, output):
    reference = json.loads((SITE / 'snapshot-reference.json').read_text())
    current = reference['livePublication']
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in (reference['snapshot']['sha256'], current['snapshotSha256']):
        raise ValueError('Input is neither verified snapshot; output was not changed.')
    data = json.loads(raw)
    if data['id'] != reference['artifactId']:
        raise ValueError('Artifact identity differs; output was not changed.')
    if digest == reference['snapshot']['sha256']:
        manifest = json.loads((SITE / 'app/src/content/assets/r2-trial.json').read_text())
        assets = {a['sha256']: a for a in manifest['assets']}
        for image in data['previewGallery'].values():
            for kind in ('image', 'thumb'):
                payload = base64.b64decode(image[kind].split(',', 1)[1], validate=True)
                sha = hashlib.sha256(payload).hexdigest()
                asset = assets[sha]
                if len(payload) != asset['bytes'] or asset['mediaType'] != 'image/webp':
                    raise ValueError('Image binding differs; output was not changed.')
                image[kind] = f"{reference['siteUrl']}/assets/{sha}/{asset['name']}"
        # Match the indexed snapshot response ordering retained by the publication.
        queries = data.pop('queries')
        for query in queries.values():
            rows = query.pop('rows')
            query['rows'] = rows
        data['queries'] = queries
        raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    if (hashlib.sha256(raw).hexdigest() != current['snapshotSha256']
            or len(raw) != current['snapshotBytes']):
        raise ValueError('Reconstructed seed differs; output was not changed.')
    if output.exists():
        if output.read_bytes() != raw:
            raise ValueError('Output has other data; refusing to overwrite it.')
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves any file created by another writer meanwhile.
    with output.open('xb') as handle:
        handle.write(raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--output', type=Path, default=SITE / 'app/src/data.json')
    args = parser.parse_args()
    try:
        restore(args.snapshot, args.output)
    except (ValueError, KeyError) as error:
        parser.exit(1, f'{error}\n')
    print('Verified current seed restored; image payloads remain outside source Git.')
