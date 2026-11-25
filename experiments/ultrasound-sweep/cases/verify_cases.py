"""Check authored cases, deterministic image replay and case-reader failure paths."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from case_library import finding_comparisons, load_cases


def verify_replay():
    families = load_cases(ROOT)
    finding_comparisons(ROOT, families)
    for cases in families.values():
        for case in cases:
            for view in case['views']:
                for key in ('title', 'caption'):
                    assert view[key].strip(), f"{case['id']}: empty {key}"
    with tempfile.TemporaryDirectory() as tmp:
        for package, build in [('echo', ['node', 'build.mjs']), ('vascular', [sys.executable, 'build_cases.py']),
                               ('organs', [sys.executable, 'build.py', '--check']),
                               ('pregnancy', [sys.executable, 'build.py', '--check'])]:
            folder = ROOT / package
            if '--check' in build:
                subprocess.run(build, cwd=folder, check=True)
            else:
                replay = Path(tmp) / package
                subprocess.run([*build, str(replay)], cwd=folder, check=True)
                assert (replay / 'cases.json').read_bytes() == (folder / 'cases.json').read_bytes()
                for image in folder.rglob('*.svg'):
                    assert (replay / image.relative_to(folder)).read_bytes() == image.read_bytes(), image
            for image in folder.rglob('*.svg'):
                assert ET.parse(image).getroot().tag == '{http://www.w3.org/2000/svg}svg', image


def verify_rejections():
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / 'cases'
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('acquired', '__pycache__'))
        data = source / 'echo/cases.json'
        original = data.read_text()
        def reject(edit, expected):
            cases = json.loads(original)
            edit(cases)
            data.write_text(json.dumps(cases))
            try:
                load_cases(source)
            except ValueError as exc:
                assert expected in str(exc), exc
            else:
                raise AssertionError(f'Accepted invalid records: {expected}')
        reject(lambda cases: cases.append(cases[0]), 'Invalid case identity')
        reject(lambda cases: cases.pop(), 'Missing case pathway')
        reject(lambda cases: cases[0]['views'][0].update(image='../cases.css'), 'invalid case image')
        reject(lambda cases: cases[0]['views'][0].update(image='missing.svg'), 'invalid case image')
        reject(lambda cases: cases[0].update(sources=[]), 'Missing worked case evidence')
        data.write_text(original)
        groups = load_cases(source)
        shutil.copytree(ROOT / 'acquired', source / 'acquired')
        manifest = source / 'acquired/references.json'
        records = json.loads(manifest.read_text())
        record = next(iter(records.values()))
        image = source / 'acquired' / record['path']
        original_image = image.read_bytes()
        image.write_bytes(original_image[:100])
        try:
            finding_comparisons(source, groups)
        except ValueError as exc:
            assert 'image identity' in str(exc), exc
        else:
            raise AssertionError('Truncated acquired source passed assembly validation')
        image.write_bytes(original_image)
        record['afterView'] = 'other-case.svg'
        manifest.write_text(json.dumps(records))
        try:
            finding_comparisons(source, groups)
        except ValueError as exc:
            assert 'no matching case view' in str(exc), exc
        else:
            raise AssertionError('Acquired source could attach to an unrelated view')



if __name__ == '__main__':
    verify_replay()
    verify_rejections()
    print('Worked case replay, SVG parsing, family coverage and invalid-input checks passed.')
