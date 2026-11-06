"""Local retained-file checks; no rebuild, network or quality approval."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_source_package import verify_studies

REVIEW = 'reviews/joints/2026-10-24-bounded-migration'


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(verify_studies(ROOT, REVIEW, None)))
