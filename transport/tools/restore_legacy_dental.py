"""Restore the legacy Dental Review payloads used by the loopback preview."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'lib'))
from med_assets.artifacts import claim_identity, install_verified, regular_path, verify_payload

SITE = ROOT / 'sites/anatomy-gallery'

MANIFEST = SITE / 'app/src/content/assets/legacy-dental-assets.json'
CACHE = SITE / '.local/legacy-dental'


def restore():
    CACHE.mkdir(parents=True, exist_ok=True)
    failures = []
    for file in json.loads(MANIFEST.read_text())['assets']:
        try:
            digest, _ = claim_identity(file)
            target = regular_path(CACHE / digest, exists=False)
            if target.is_file():
                try:
                    verify_payload(target, file)
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
                install_verified(staged, target, file, replace=True)
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
