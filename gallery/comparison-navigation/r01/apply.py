"""Apply combined #205/#206 only to the exact v45 review directory; never fetch or publish."""
from pathlib import Path
import argparse
import hashlib
import json
HERE = Path(__file__).resolve().parent
BINDING = json.loads((HERE / 'binding.json').read_text())
def digest(raw):
    return hashlib.sha256(raw).hexdigest()
def apply(directory):
    target = Path(directory)
    for name, expected in BINDING['inputs'].items():
        if digest((target / name).read_bytes()) != expected:
            raise ValueError('Exact v45 input required: ' + name)
    if any((target / name).exists() for name in ('navigation-focus.mjs','comparison-state.mjs')):
        raise ValueError('Navigation module already exists; use a fresh baseline copy')
    outputs = {name: (HERE / name).read_bytes() for name in BINDING['outputs']}
    for name, expected in BINDING['outputs'].items():
        if digest(outputs[name]) != expected:
            raise ValueError('Reviewed output mismatch: ' + name)
    # Validate every guard before modifying any file.
    for name, raw in outputs.items():
        (target / name).write_bytes(raw)
    return {name: digest(raw) for name, raw in outputs.items()}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_dir', type=Path)
    print(json.dumps(apply(parser.parse_args().review_dir), indent=2))
