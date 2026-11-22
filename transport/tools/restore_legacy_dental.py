"""Restore the legacy Dental Review payloads used by the loopback preview."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SITE = Path(__file__).resolve().parents[2] / 'sites/anatomy-gallery'
sys.path.insert(0, str(SITE / 'tools'))
from gallery_runtime import verified

MANIFEST = SITE / 'app/src/content/assets/legacy-dental-assets.json'
CACHE = SITE / '.local/legacy-dental'


def restore():
    CACHE.mkdir(parents=True, exist_ok=True)
    failures = []
    for file in json.loads(MANIFEST.read_text())['assets']:
        target = CACHE / file['sha256']
        try:
            if target.is_file():
                try:
                    verified(file, target.read_bytes())
                    continue
                except ValueError:
                    pass
            with tempfile.TemporaryDirectory(prefix='restore-', dir=CACHE) as temporary:
                staged = Path(temporary) / target.name
                subprocess.run([
                    'curl', '--fail', '--silent', '--show-error', '--location',
                    '--proto', '=https', '--proto-redir', '=https', '--retry', '2',
                    '--max-time', '25', '--max-filesize', str(file['bytes']),
                    '--output', str(staged), file['source'],
                ], check=True)
                verified(file, staged.read_bytes())
                os.replace(staged, target)
            print(f"Restored {file['path']}")
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            failures.append(f"{file['path']}: {error}")
    return failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if failures := restore():
        parser.exit(1, '\n'.join(failures) + '\n')
    print('Legacy Dental Review payloads verified.')
