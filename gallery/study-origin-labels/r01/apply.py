"""Correct exactly two bilingual presentation expressions; no fetch or publication."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BINDING = json.loads((HERE / 'binding.json').read_text())
EDITS = (
    ("'原始素材 · '+data.assets.length:'Original assets · '+data.assets.length", "'素材条目 · '+data.assets.length:'Asset entries · '+data.assets.length"),
    ("${kind==='current'?(lang==='zh'?'更新版':'Updated version'):(lang==='zh'?'原版':'Original')}", "${kind==='current'?(lang==='zh'?'更新版':'Updated version'):(c.hasBaseline===false?(lang==='zh'?'仅研究条目（无原始基线）':'Study-only entry (no baseline)'):(lang==='zh'?'原版':'Original'))}"),
)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def patched(raw):
    if digest(raw) != BINDING['inputs']['review.js']:
        raise ValueError('Exact v48 renderer required')
    text = raw.decode()
    for old, new in EDITS:
        if text.count(old) != 1:
            raise ValueError('Unique original label expression required')
        text = text.replace(old, new)
    updated = text.encode()
    if digest(updated) != BINDING['output']:
        raise ValueError('Exact reviewed renderer output required')
    return updated

def apply(directory):
    target = Path(directory)
    raw = {name: (target / name).read_bytes() for name in BINDING['inputs']}
    for name, expected in BINDING['inputs'].items():
        if digest(raw[name]) != expected:
            raise ValueError('Exact v48 input required: ' + name)
    updated = patched(raw['review.js'])
    (target / 'review.js').write_bytes(updated)
    return {'review.js': digest(updated)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_directory', type=Path)
    print(json.dumps(apply(parser.parse_args().review_directory), indent=2))
