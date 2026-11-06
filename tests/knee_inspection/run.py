"""Run exact reviewed viewer/helper tests with compact local source fixtures; no network/WebGL."""
from pathlib import Path
import tempfile, shutil, subprocess, json, hashlib
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BINDING = json.loads((ROOT/'gallery/knee-inspection/r01/binding.json').read_text())
DEPENDENCIES = {
    'candidate-contract.mjs': HERE/'fixtures/candidate-contract.mjs',
    'viewer-lifecycle.mjs': ROOT/'gallery/candidate-lifecycle/r01/viewer-lifecycle.mjs',
    'context-loss.mjs': ROOT/'gallery/candidate-context/r01/context-loss.mjs',
}
for name, source in DEPENDENCIES.items():
    if hashlib.sha256(source.read_bytes()).hexdigest() != BINDING['inputs'][name]:
        raise ValueError('Wrong exact v44 dependency fixture: '+name)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory); review = root/'public/review'; tests = root/'tests'
    review.mkdir(parents=True); tests.mkdir()
    for name in ('candidate.js','knee-inspection.mjs'):
        shutil.copyfile(ROOT/'gallery/knee-inspection/r01'/name,review/name)
    for name, source in DEPENDENCIES.items():
        shutil.copyfile(source, review/name)
    shutil.copyfile(HERE/'fixtures/records.json',review/'review-data.json')
    for old,new in [('helper.test.mjs','helper.test.mjs'),('composition.test.mjs','composition.test.mjs')]:
        shutil.copyfile(HERE/old,tests/new)
    raise SystemExit(subprocess.run(['node','--test',str(tests/'helper.test.mjs'),str(tests/'composition.test.mjs')]).returncode)
