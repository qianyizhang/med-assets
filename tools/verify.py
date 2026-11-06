#!/usr/bin/env python3
"""Local verification with explicit metadata, payload and dental boundaries. No network."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests/review_records'))
from validate_record import reference, validate, validate_structure
from lfs_transport import load_manifest, unique_keys

SNAPSHOT_SHA256 = '903eb7bc1c456e75b9eb3b1246a038f7134046d7c0964b1ebcc9ecfe25c0b821'
IMPORT_MANIFEST_SHA256 = '48953d622e4ea3730185c90452bd3125b14935fa654541f0636e5f69c031cc30'
POINTER = re.compile(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (0|[1-9][0-9]*)\n')
FOUNDATION_PATTERNS = ('reviews/*/2026-10-23-metadata-cleanup-r01/record.json',
                       'reviews/*/2026-10-23-hra-*/record.json')
# Existing package-specific assertions remain authoritative; no schema migration.
PAYLOAD_CHECKS = (
    ('tests/bp3d_glands/verify_bounded_receipt.py',),
    ('assemblies/bladder-pancreas/recipes/verify_bounded_receipt.py',),
    ('tests/thyroid_vagina/verify_receipt.py', '--strict'),
    ('tests/bp3d-head-studies/verify_bounded.py',),
    ('tests/bp3d-body-studies/verify_bounded.py',),
    ('tests/bp3d_bowels/verify_bounded.py',),
    ('tests/joints/verify_bounded.py',),
    ('tools/verify_source_package.py', 'muscle'),
    ('tools/verify_source_package.py', 'breasts_hra'),
    ('tests/hra_lung/verify_bounded.py',),
    ('tests/z_small_studies/verify_bounded.py',),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_bytes(), object_pairs_hook=unique_keys)


def parse_pointer(data):
    match = POINTER.fullmatch(data)
    require(match is not None, 'Malformed LFS pointer')
    return match[1].decode(), int(match[2])


def git(root, *args, data=None):
    return subprocess.run(['git', *args], cwd=root, input=data, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def selected_files(root, *patterns):
    """Include present additions and reject omissions of still-indexed family files."""
    indexed = git(root, 'ls-files', '-z', '--',
                  *(f':(glob){pattern}' for pattern in patterns)).split(b'\0')
    files = {root / name.decode() for name in indexed if name}
    files.update(path for pattern in patterns for path in root.glob(pattern))
    for path in sorted(files):
        require(path.is_file(), 'Selected file missing: ' + str(path.relative_to(root)))
    return sorted(files)


def index_pointers(root):
    entries = {}
    for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            metadata, name = row.split(b'\t', 1)
            mode, oid, stage = metadata.split()
            require(stage == b'0', 'Unmerged index entry: ' + name.decode())
            entries[name] = (mode, oid)
    names = b'\0'.join(entries) + b'\0'
    attrs = git(root, 'check-attr', '--cached', '-z', '--stdin', 'filter', data=names).split(b'\0')[:-1]
    selected = [attrs[i] for i in range(0, len(attrs), 3) if attrs[i+2] == b'lfs']
    require(selected, 'No tracked LFS pointers found; full checkout required')
    oids = b'\n'.join(entries[name][1] for name in selected) + b'\n'
    sizes = git(root, 'cat-file', '--batch-check', data=oids).splitlines()
    require(len(sizes) == len(selected), 'Incomplete Git object inventory')
    for name, row in zip(selected, sizes):
        fields = row.split()
        require(entries[name][0] == b'100644' and len(fields) == 3
                and fields[1] == b'blob' and int(fields[2]) <= 1024,
                'Expected small regular LFS pointer in Git index: ' + name.decode())
    stream = io.BytesIO(git(root, 'cat-file', '--batch', data=oids))
    pointers = {}
    for name in selected:
        size = int(stream.readline().split()[2])
        data = stream.read(size)
        require(stream.read(1) == b'\n', 'Incomplete Git object read')
        try:
            pointers[name.decode()] = parse_pointer(data)
        except ValueError as error:
            raise ValueError(f'{name.decode()}: {error}') from error
        path, _ = reference(root, {'file': name.decode(), 'sha256': pointers[name.decode()][0]})
        with path.open('rb') as file:
            prefix = file.read(1025)
        if prefix.startswith(b'version ') or b'oid sha256:' in prefix:
            require(parse_pointer(prefix) == pointers[name.decode()], 'Working pointer differs from index: ' + name.decode())
    return pointers


def current_import_checks(root, pointers):
    snapshot = root / 'SHA256SUMS'
    require(sha256(snapshot) == SNAPSHOT_SHA256, 'Historical SHA256SUMS changed; preserve import snapshot')
    expected = {}
    for line in snapshot.read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name not in expected, 'Duplicate imported path')
        expected[name] = digest
    require(len(expected) == 591, 'Import snapshot must contain 591 paths')
    manifest_path = root / 'metadata/asset-manifest.json'
    require(sha256(manifest_path) == IMPORT_MANIFEST_SHA256,
            'Historical asset manifest changed; preserve import evidence')
    sizes = {}
    for bundle in read_json(manifest_path)['bundles']:
        for entry in bundle['files']:
            name, digest, size = entry['path'], entry['sha256'], entry['bytes']
            require(name in expected and expected[name] == digest and type(size) is int and size >= 0,
                    'Import manifest/snapshot mismatch: ' + name)
            require(name not in sizes or sizes[name] == size, 'Conflicting import size: ' + name)
            sizes[name] = size
    require(set(sizes) == set(expected), 'Import manifest/snapshot paths differ')
    overrides = read_json(root / 'metadata/current-import-overrides.json')
    for name, row in overrides.items():
        require(name in expected and row['importSha256'] == expected[name], 'Override must bind original import hash: ' + name)
        require(re.fullmatch(r'[0-9a-f]{7,40}', row['changeCommit']) and row['reason'].strip(), 'Override requires change provenance')
        require(row['currentSha256'] != expected[name], 'Redundant import override: ' + name)
        expected[name] = row['currentSha256']
        if name in pointers:
            size = row.get('currentBytes')
            require(type(size) is int and size >= 0, 'LFS import override requires currentBytes: ' + name)
            sizes[name] = size
    tracked = {name.decode() for name in git(root, 'ls-files', '-z').split(b'\0') if name}
    retained = expected.keys() & tracked
    for name in sorted(retained):
        digest = expected[name]
        check_reference(root, pointers, {'file': name, 'sha256': digest})
        if name in pointers:
            require(pointers[name][1] == sizes[name], 'LFS pointer size/import mismatch: ' + name)
    return len(retained), len(retained & overrides.keys())


def check_reference(root, pointers, entry):
    path, digest = reference(root, entry)
    require(path.is_file(), 'Missing reference: ' + entry['file'])
    if entry['file'] in pointers:
        require(pointers[entry['file']][0] == digest, 'LFS pointer OID/reference mismatch: ' + entry['file'])
    else:
        require(sha256(path) == digest, 'Current file SHA-256 mismatch: ' + entry['file'])
    return digest


def run_suite(path, stream=None):
    require(path.is_file(), 'Required suite missing: ' + str(path))
    original_path = sys.path[:]
    module_name = path.stem
    had_module = module_name in sys.modules
    previous_module = sys.modules.get(module_name)
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        # unittest resolves module fixtures through sys.modules.
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        discovered = suite.countTestCases()
        require(discovered > 0, 'Required suite empty: ' + str(path))
        result = unittest.TextTestRunner(stream=stream or sys.stderr, verbosity=1).run(suite)
        require(result.wasSuccessful() and not result.skipped and not result.expectedFailures,
                'Required suite failed, skipped or expected-failed: ' + str(path))
        require(result.testsRun == discovered, 'Required suite execution incomplete: ' + str(path))
        return result.testsRun
    finally:
        sys.path[:] = original_path
        if had_module:
            sys.modules[module_name] = previous_module
        else:
            sys.modules.pop(module_name, None)


def validate_transport_manifests(root, pointers):
    manifests = selected_files(root, 'transport/manifests/*.json')
    sizes = {}
    for path in manifests:
        for obj in load_manifest(root, path.stem)['objects']:
            oid, size = obj['sha256'], obj['bytes']
            require(oid not in sizes or sizes[oid] == size, 'Conflicting transport manifest sizes: ' + oid)
            sizes[oid] = size
    pointer_sizes = {}
    for name, (oid, size) in pointers.items():
        require(oid not in pointer_sizes or pointer_sizes[oid] == size,
                'Conflicting sizes for identical LFS OID: ' + name)
        pointer_sizes[oid] = size
        if oid in sizes:
            require(sizes[oid] == size, 'LFS pointer size/transport mismatch: ' + name)
    return len(manifests)


def foundation_records(root):
    return selected_files(root, *FOUNDATION_PATTERNS)


def offline(root):
    suites = selected_files(root, 'tests/test_*.py', 'tests/review_records/test_*.py')
    require(suites, 'No offline test suites found; full checkout required')
    count = sum(run_suite(path) for path in suites)
    pointers = index_pointers(root)
    imported, updates = current_import_checks(root, pointers)
    manifest_count = validate_transport_manifests(root, pointers)  # No transport call.
    records = foundation_records(root)
    for path in records:
        try:
            validate_structure(read_json(path), lambda entry: check_reference(root, pointers, entry))
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f'{path.relative_to(root)}: {error}') from error
    print(f'PASS offline: {count} tests; {manifest_count} transport manifests; {len(records)} foundation records; '
          f'{imported} import references ({updates} documented updates); {len(pointers)} LFS pointer identities.', flush=True)
    print('Offline phase: media bytes NOT verified. Dental dependencies/payload suite, package payload checks, '
          'replay, visual/anatomy/runtime and remote transport are outside this phase.', flush=True)
    return pointers, records


def payload_integrity(root, pointers, records):
    total = 0
    for name, (digest, size) in pointers.items():
        path, _ = reference(root, {'file': name, 'sha256': digest})
        with path.open('rb') as stream:
            require(not stream.read(100).startswith(b'version https://git-lfs.github.com/spec/'),
                    'Unresolved LFS pointer; fetch payload first: ' + name)
        require(path.stat().st_size == size and sha256(path) == digest, 'Payload size/SHA-256 mismatch: ' + name)
        total += size
    for path in records:
        validate(read_json(path), root)  # Existing strict byte validator, unchanged contract.
    print('Running retained package checks. Their historical status fields do not establish fresh '
          'remote availability or quality approval.', flush=True)
    for command in PAYLOAD_CHECKS:
        subprocess.run([sys.executable, *command], cwd=root, check=True)
    print(f'PASS payload-integrity: {len(pointers)} local LFS files / {total} bytes, '
          f'{len(records)} foundation records, {len(PAYLOAD_CHECKS)} package checks. '
          'No dental suite, reconstruction, visual/anatomy/runtime or remote-availability claim.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('offline', 'payload-integrity', 'dental'))
    args = parser.parse_args()
    require(not sys.flags.optimize, 'Do not use Python -O: package checks require assertions')
    if args.mode == 'dental':
        count = run_suite(ROOT / 'tests/dental/test_uff_tomo1b.py')
        print(f'PASS dental: {count} required tests including actual pinned GLB hash; no source replay or anatomy approval.')
    else:
        pointers, records = offline(ROOT)
        if args.mode == 'payload-integrity':
            payload_integrity(ROOT, pointers, records)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f'FAIL verification: {type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
