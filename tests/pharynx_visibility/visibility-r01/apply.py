"""Apply the bounded viewer patch to an independent copy of verified v40 source.

No source retrieval, dataset rewrite, GLB change, Git mutation or publication.
"""
from pathlib import Path
import argparse
import hashlib
import json

BASE_SHA = '9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b'
MODULES = ('pharynx-inspection.mjs', 'pharynx-inspection.css')


def apply(review_dir):
    target = Path(review_dir)
    path = target / 'candidate.js'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_SHA:
        raise ValueError('candidate.js does not match the verified v40 baseline')
    if any((target / name).exists() for name in MODULES):
        raise ValueError('Inspection files already exist; use a fresh source copy')
    text = raw.decode('utf-8')
    replacements = (
        ("let lang='en',data,record", "let inspectionUI=null;\nlet lang='en',data,record"),
        ('function paint(){', 'function paint(){inspectionUI?.paint(lang);'),
        ('const originalVisibility=new Map();',
         'inspectionUI=mountInspection(record,model.scene,wrap,{fitVisible:()=>fitVisibleParts(model.scene,camera,controls,THREE)});const originalVisibility=new Map();'),
        ("}catch(err){cleanup();state='blocked';",
         "}catch(err){cleanup();document.querySelector('.pharynx-inspection')?.remove();state='blocked';"),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Expected exactly one integration anchor: ' + old)
        text = text.replace(old, new, 1)
    text = "import {mountInspection,fitVisibleParts} from './pharynx-inspection.mjs';\n" + text
    # Read all payloads before writing; baseline/anchor failures leave the copy untouched.
    payloads = {name: (Path(__file__).parent / name).read_bytes() for name in MODULES}
    payloads['candidate.js'] = text.encode('utf-8')
    for name, content in payloads.items():
        (target / name).write_bytes(content)
    return {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_dir', type=Path, help='Independent local copy of dist/review')
    args = parser.parse_args()
    print(json.dumps(apply(args.review_dir), indent=2))
