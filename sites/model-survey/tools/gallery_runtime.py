"""Prepare the gallery's existing, hash-verified Three.js modules and rubric."""
import hashlib
import json
import os
from pathlib import Path
import shutil


def prepare_gallery(repo: Path, target: Path):
    fixture = json.loads((repo / 'ci/glb-runtime-fixture.json').read_text())
    files = [entry for entry in fixture['resources'] if entry['path'].startswith('vendor/')]
    orbit = json.loads((repo / 'tests/candidate_camera/vendor-binding.json').read_text())['orbitControls']
    files.append({**orbit, 'path': 'vendor/examples/jsm/controls/OrbitControls.js'})
    for resource in files:
        name = Path(resource['path'])
        candidates = [repo / 'lessons/one-breath/.local' / name,
                      repo / '.artifacts/body-systems-survey-2026-11-19/viewer-vendor' / name,
                      repo / '.artifacts/verification-consolidation/vendor' / name.name]
        source = next((p for p in candidates if p.is_file()
                       and hashlib.sha256(p.read_bytes()).hexdigest() == resource['sha256']), None)
        if source is None:
            raise ValueError(f'Missing pinned {name}. Restore the Body Systems viewer vendor inputs.')
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if 'examples' in name.parts:
            module = os.path.relpath(target / 'vendor/build/three.module.js', dest.parent)
            dest.write_text(source.read_text().replace("from 'three';", f"from '{module}';"))
        else:
            shutil.copyfile(source, dest)
    shutil.copyfile(repo / 'guideline/asset-quality.md', target / 'rubric.md')
