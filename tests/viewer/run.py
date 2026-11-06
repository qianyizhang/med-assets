"""Run incorporated viewer checks with captured source and private per-run staging."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    'lifecycle': ('candidate_lifecycle/lifecycle.test.mjs',),
    'context': ('candidate_context/context.test.mjs',),
    'knee': ('knee_inspection/helper.test.mjs', 'knee_inspection/composition.test.mjs'),
    'eye': ('eye_inspection/eye-inspection.test.mjs', 'eye_inspection/eye-composition.test.mjs'),
}


def read_sources(root=ROOT):
    """Capture exact bytes once; never cache a verified result for a mutable path."""
    binding = json.loads((root / 'tests/viewer/source.json').read_bytes())
    sources = {}
    for name, row in binding['files'].items():
        path = root / row['file']
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Viewer source must stay inside the checkout: ' + name)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Wrong exact viewer source: ' + name)
        sources[name] = raw
    return sources


@contextmanager
def stage(root=ROOT, whole_fixture=None):
    sources = read_sources(root)  # Refuse before staging or executing unbound code.
    with tempfile.TemporaryDirectory(prefix='med-viewer-') as directory:
        target = Path(directory)
        review, tests = target / 'public/review', target / 'tests'
        review.mkdir(parents=True)
        tests.mkdir()
        for name, raw in sources.items():
            (review / name).write_bytes(raw)
        data = json.loads((root / 'tests/eye_inspection/fixtures/records.json').read_bytes())
        data['candidates'] = json.loads((root / 'tests/knee_inspection/fixtures/records.json').read_bytes())['candidates']
        data['candidates'].append(json.loads(sources['eye-record.json']))
        (review / 'review-data.json').write_text(json.dumps(data, ensure_ascii=False))
        (review / 'media').mkdir()
        (review / 'media/models.json').write_bytes(
            (root / 'tests/eye_inspection/fixtures/models.json').read_bytes())
        for paths in SUITES.values():
            for path in paths:
                name = path.replace('/', '-')
                (tests / name).write_bytes((root / 'tests' / path).read_bytes())
        (tests / 'module-harness.mjs').write_bytes(
            (root / 'tests/candidate_lifecycle/module-harness.mjs').read_bytes())
        if whole_fixture:
            raw = whole_fixture.read_bytes()
            if hashlib.sha256(raw).hexdigest() != '73332bb0f1ef491ab0d411fb6cbf39e20b8e466b93d306d73469fb55685b03a7':
                raise ValueError('Exact retained whole fixture required')
            eye = json.loads(sources['eye-record.json'])
            path = target / 'unpublished-source/eye99' / eye['inspectionModes']['whole']['source']['file']
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            (tests / 'eye-payload.test.mjs').write_bytes(
                (root / 'tests/eye_inspection/payload.test.mjs').read_bytes())
        yield target


def run(groups=tuple(SUITES), root=ROOT, whole_fixture=None):
    import os
    with stage(root, whole_fixture) as target:
        files = [str(target / 'tests' / path.replace('/', '-'))
                 for group in groups for path in SUITES[group]]
        if whole_fixture:
            files.append(str(target / 'tests/eye-payload.test.mjs'))
        env = dict(os.environ, EYE_PAYLOAD='1' if whole_fixture else '0')
        result = subprocess.run(['node', '--experimental-vm-modules', '--test',
                                 '--test-reporter=tap', *files], env=env,
                                capture_output=True, text=True, timeout=60)
        counts = dict((key, int(value)) for key, value in re.findall(
            r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$', result.stdout, re.MULTILINE))
        if (result.returncode or not counts.get('tests') or
                counts.get('pass') != counts['tests'] or
                any(counts.get(key) != 0 for key in ('fail', 'cancelled', 'skipped', 'todo'))):
            raise RuntimeError('Viewer suite failed or incomplete:\n' + result.stdout + result.stderr)
        return result.stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', action='append', choices=SUITES)
    parser.add_argument('--whole-fixture', type=Path)
    args = parser.parse_args()
    try:
        print(run(args.suite or tuple(SUITES), whole_fixture=args.whole_fixture))
    except (ValueError, OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
