#!/usr/bin/env python3
"""Prepare immutable preview files and references locally; never transfer or delete assets."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.parse


def prepare(app: Path, output: Path, site_url: str) -> dict:
    origin = urllib.parse.urlsplit(site_url)
    if (origin.scheme != 'https' or not origin.hostname or origin.username or origin.password
            or origin.path not in ('', '/') or origin.query or origin.fragment):
        raise ValueError('Use the exact canonical HTTPS Site origin')
    site_url = site_url.rstrip('/')
    snapshot = app / 'src/data.json'
    index = app / 'src/content/assets/r2-trial.json'
    manifest = json.loads(index.read_text())
    originals = {item['sha256']: item for item in manifest['assets']}
    images = {}

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, str) and value.startswith('data:image/'):
            prefix, encoded = value.split(',', 1)
            extensions = {'data:image/png;base64': ('png', 'image/png'),
                          'data:image/webp;base64': ('webp', 'image/webp'),
                          'data:image/jpeg;base64': ('jpg', 'image/jpeg')}
            if prefix not in extensions:
                raise ValueError('Unsupported embedded image encoding')
            data = base64.b64decode(encoded, validate=True)
            if not 0 < len(data) <= 40_000_000:
                raise ValueError('Preview exceeds the trial object limit')
            digest = hashlib.sha256(data).hexdigest()
            extension, media = extensions[prefix]
            name = 'preview.' + extension
            images[digest] = data
            originals.setdefault(digest, {'name': name, 'sha256': digest, 'bytes': len(data),
                'mediaType': media, 'source': site_url,
                'attribution': 'Survey preview. Preserve the source-specific provenance, notices and quality limits in the corresponding report row; no new blanket license.'})
            return site_url + '/assets/' + digest + '/' + name
        return value

    data = replace(json.loads(snapshot.read_text()))
    output.mkdir(parents=True, exist_ok=False)
    for digest, payload in images.items():
        (output / digest).write_bytes(payload)
    manifest['assets'] = list(originals.values())
    index.write_text(json.dumps(manifest, indent=2) + '\n')
    snapshot.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return {'preparedObjects': len(images), 'preparedBytes': sum(map(len, images.values())),
            'transferred': False, 'publicationRequired': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path(__file__).resolve().parents[1] / 'app')
    parser.add_argument('--output', type=Path, required=True, help='Fresh local directory for prepared image bytes')
    parser.add_argument('--site-url', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.app, args.output, args.site_url)))


if __name__ == '__main__':
    main()
