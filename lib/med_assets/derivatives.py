"""Declared display master and output bindings for assessment evidence."""
import json
from pathlib import Path

from .artifacts import claim_identity, declared_identity, repo_file, source_path, unique_keys

DISPLAY_DERIVATIVES = 'sources/display-derivatives.json'


def display_derivatives(repo: Path) -> dict:
    """Load explicit masters, output identities and recipes without publication data."""
    path = repo_file(repo, DISPLAY_DERIVATIVES, exists=False)
    if not path.exists():
        return {}
    document = json.loads(path.read_text(), object_pairs_hook=unique_keys)
    if type(document['schemaVersion']) is not int or document['schemaVersion'] != 1:
        raise ValueError('Unsupported display derivative schema')
    derivatives = {}
    for record in document['derivatives']:
        source, output = record['source'], record['output']
        source_name, output_name = source_path(source['path']), source_path(output['path'])
        claim_identity(source)
        claim_identity(output)
        if (source_name == output_name or output_name in derivatives
                or not isinstance(record['recipe'], str) or not record['recipe'].strip()):
            raise ValueError(f'Invalid display derivative: {output_name}')
        derivatives[output_name] = record
    if any(record['source']['path'] in derivatives for record in derivatives.values()):
        raise ValueError('Display derivatives require a canonical source file')
    return derivatives


class AssessmentIdentities:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.displays = display_derivatives(self.repo)

    def check(self, claim):
        """Validate a review claim from a file declaration or explicit display binding."""
        path = claim['path']
        if binding := self.displays.get(path):
            source = binding['source']
            if declared_identity(self.repo, source['path']) != claim_identity(source):
                raise ValueError(f"Display source identity mismatch for {source['path']}")
            digest, size = claim_identity(binding['output'])
        else:
            digest, size = declared_identity(self.repo, path)
        if digest != claim.get('sha256') or (claim.get('bytes') is not None and size != claim['bytes']):
            raise ValueError(f'Identity mismatch for {path}')
        return digest, size
