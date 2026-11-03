"""Run actual reviewed eye source with compact fixtures; no network or WebGL."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--whole-fixture', type=Path, help='Optional exact retained whole gzip for three additional composition cases')
args = parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    review = stage / 'public/review'
    tests = stage / 'tests'
    review.mkdir(parents=True)
    tests.mkdir()
    for name in ('candidate.js', 'inspection-modes.mjs'):
        shutil.copyfile(ROOT / 'gallery/eye-inspection/r01' / name, review / name)
    for name, source in {
        'candidate-contract.mjs': ROOT / 'tests/knee_inspection/fixtures/candidate-contract.mjs',
        'viewer-lifecycle.mjs': ROOT / 'gallery/candidate-lifecycle/r01/viewer-lifecycle.mjs',
        'model-media.mjs': HERE / 'fixtures/model-media.mjs',
        'review-data.json': HERE / 'fixtures/records.json',
    }.items():
        shutil.copyfile(source, review / name)
    (review / 'media').mkdir()
    shutil.copyfile(HERE / 'fixtures/models.json', review / 'media/models.json')
    lines = (HERE / 'eye-inspection.test.mjs').read_text().splitlines(True)
    # Byte/preservation cases remain in retained source; offline coverage does not claim them.
    code = ''.join(line for line in lines if not line.startswith("for(const key of ['whole','cutaway'])") and not line.startswith("test('exact v47 records"))
    (tests / 'eye-inspection.test.mjs').write_text(code)
    code = (HERE / 'eye-composition.test.mjs').read_text()
    if args.whole_fixture:
        import hashlib
        raw = args.whole_fixture.read_bytes()
        if hashlib.sha256(raw).hexdigest() != '73332bb0f1ef491ab0d411fb6cbf39e20b8e466b93d306d73469fb55685b03a7':
            raise ValueError('Exact retained whole fixture required')
        record = json.loads((review / 'review-data.json').read_text())['candidates'][0]
        fixture = stage / 'unpublished-source/eye99' / record['inspectionModes']['whole']['source']['file']
        fixture.parent.mkdir(parents=True)
        fixture.write_bytes(raw)
    else:
        code = ''.join(line for line in code.splitlines(True) if not line.startswith("test('actual eye"))
    (tests / 'eye-composition.test.mjs').write_text(code)
    raise SystemExit(subprocess.run(['node', '--test', '--test-reporter=tap', str(tests / 'eye-inspection.test.mjs'), str(tests / 'eye-composition.test.mjs')]).returncode)
