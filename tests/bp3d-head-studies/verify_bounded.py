"""Local retained-file checks; no rebuild, network or quality approval."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_source_package import verify_studies, digest

REVIEW = 'reviews/bp3d-head-studies/2026-10-24-bounded-migration'
SOURCE = 'sources/datasets/bp3d-4.0-head-studies/external-source-map.json'


def check_source(files, study, document):
    source = files.json(SOURCE)
    record = files.json(study['reviewRecord'])
    assert len(record['componentIdentityMap']) == record['componentCount']
    for component in record['componentIdentityMap']:
        extras = document['nodes'][component['nodeIndex']]['extras']
        assert extras['source_sha256'] == component['sourceSha256'] == source['members'][component['sourceFileId']]['sha256']
    for evidence in study['evidence']:
        if evidence['format'] == 'WEBP':
            assert evidence['sha256'] != evidence['originalPngSha256']
        elif evidence['format'] == 'PNG':
            additive = files.json(evidence['additiveRecord'])
            assert additive['sourceSha256'] == evidence['sourceSha256'] == study['transport']['decodedSha256']
            assert any(row['sha256'] == evidence['sha256'] and row['sourceSha256'] == evidence['sourceSha256'] for row in additive['evidence'])
            for linked in additive['sourceRecords'] + additive['evidence']:
                raw = files.read(linked['file'])
                assert digest(raw) == linked['sha256']


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(verify_studies(ROOT, REVIEW, check_source)))
