"""Replay the reviewed cervicovaginal export from the shared pelvic model."""

import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'assemblies/hra-female-pelvis'))
from build import VAGINA_FILE, build, read_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = build(*read_inputs())[VAGINA_FILE]
    with args.output.open('xb') as stream:
        stream.write(result)
    print(hashlib.sha256(result).hexdigest(), len(result), args.output)


if __name__ == '__main__':
    main()
