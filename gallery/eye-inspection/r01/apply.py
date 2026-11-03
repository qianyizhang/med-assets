"""Apply the bounded eye inspection to an exact v47 source copy; no transport."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BINDING = json.loads((HERE / 'binding.json').read_text())

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def apply(directory):
    target = Path(directory)
    raw = {name: (target / name).read_bytes() for name in BINDING['inputs']}
    for name, expected in BINDING['inputs'].items():
        if digest(raw[name]) != expected:
            raise ValueError('Exact v47 source required: ' + name)
    for name in ('inspection-modes.mjs', 'eye-r03-changelog.md'):
        if (target / name).exists():
            raise ValueError('Fresh source copy required: ' + name)
    record_raw = (HERE / 'record.json').read_bytes()
    if digest(record_raw) != BINDING['recordSha256']:
        raise ValueError('Reviewed record identity required')
    record = json.loads(record_raw)
    data = json.loads(raw['review-data.json'])
    if any(c['id'] == record['id'] for c in data['candidates']):
        raise ValueError('Duplicate eye inspection record')
    data['candidates'].append(record)
    outputs = {name: (HERE / name).read_bytes() for name in BINDING['outputs'] if name != 'review-data.json'}
    outputs['review-data.json'] = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    # Complete preflight before the first write; dependency files are never rewritten.
    for name, content in outputs.items():
        if digest(content) != BINDING['outputs'][name]:
            raise ValueError('Reviewed output identity required: ' + name)
    for name, content in outputs.items():
        (target / name).write_bytes(content)
    return {name: digest(content) for name, content in outputs.items()}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_directory', type=Path)
    print(json.dumps(apply(parser.parse_args().review_directory), indent=2))
