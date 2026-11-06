"""Local retained-file checks; no rebuild, network or quality approval."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_source_package import verify_studies

REVIEW = 'reviews/bp3d-body-studies/2026-10-24-bounded-migration'
SOURCE = 'sources/datasets/bp3d-4.0-body-studies/external-source-map.json'


def check_source(files, study, document):
    source = files.json(SOURCE)
    record = files.json(study['reviewRecord'])
    assert len(record['componentIdentityMap']) == record['componentCount']
    assert record['evidence'] == study['evidence']
    files.read(record['sourceDependencies'])
    for component in record['componentIdentityMap']:
        extras = document['nodes'][component['nodeIndex']]['extras']
        assert extras['source_file_id'] == component['sourceFileId']
        assert extras.get('source_concept_id') == component['nodeConceptId']
        assert component['sourceSha256'] == source['members'][component['sourceFileId']]['sha256']
        assert component['sourceHashEmbeddedInGLB'] is False
        name, fragment = component['sourceIdentityRef'].split('#members/')
        files.read(name)
        assert fragment in source['members']
    for reference in record['externalHistoricalRecords']:
        assert reference['bundled'] is False and len(reference['sha256']) == 64
    for evidence in study['evidence']:
        assert evidence['sha256'] != evidence['originalPngSha256']
        assert evidence['originalPngExternal']['bundled'] is False
        assert evidence['originalPngExternal']['sha256'] == evidence['originalPngSha256']


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(verify_studies(ROOT, REVIEW, check_source)))
