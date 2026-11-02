"""Apply the reviewed knee inspection to a fresh exact v44 review-directory copy."""
from pathlib import Path
import argparse
import hashlib
import json
HERE = Path(__file__).resolve().parent
BINDING = json.loads((HERE / 'binding.json').read_text())
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def patched(raw):
    if digest(raw) != BINDING['inputs']['candidate.js']:
        raise ValueError('Exact v44 candidate required')
    result = (HERE / 'candidate.js').read_bytes()
    if digest(result) != BINDING['outputs']['candidate.js']:
        raise ValueError('Reviewed candidate output mismatch')
    return result
def apply(directory):
    target = Path(directory)
    # Validate all input/dependency bytes and absence before any write.
    for name, expected in BINDING['inputs'].items():
        if digest((target / name).read_bytes()) != expected:
            raise ValueError('Exact v44 input required: ' + name)
    if (target / 'knee-inspection.mjs').exists():
        raise ValueError('Inspection module already exists; use a fresh source copy')
    data = json.loads((target / 'review-data.json').read_text())
    rows = [c for c in data['candidates'] if c['id'] == 'joints__z-knee-r01']
    if len(rows) != 1:
        raise ValueError('Unique knee record required')
    rows[0]['criticalNotes'] = json.loads((HERE / 'note.json').read_text())
    outputs = {'candidate.js': patched((target / 'candidate.js').read_bytes()), 'knee-inspection.mjs': (HERE / 'knee-inspection.mjs').read_bytes()}
    outputs['review-data.json'] = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    for name, raw in outputs.items():
        if digest(raw) != BINDING['outputs'][name]:
            raise ValueError('Reviewed output mismatch: ' + name)
    for name, raw in outputs.items():
        (target / name).write_bytes(raw)
    return {name: digest(raw) for name, raw in outputs.items()}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_dir', type=Path)
    print(json.dumps(apply(parser.parse_args().review_dir), indent=2))
