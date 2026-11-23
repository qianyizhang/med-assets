"""Explain discoverable retention references for exact repository paths."""
from collections import defaultdict
import json
from pathlib import PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit

from med_assets.artifacts import repo_file, source_path, unique_keys
from med_assets.derivatives import DISPLAY_DERIVATIVES
from med_assets.teaching import ASSESSMENTS, SELECTIONS, CurrentTeaching, check_promotion_journal, locked_store
from delivery_catalog import DELIVERY_INDEX, current_paths
from restore_collection import checksum_members
from verify_recipe_dependencies import recipe_roots, verify_graph

GALLERY = 'sites/anatomy-gallery'
GALLERY_ASSETS = f'{GALLERY}/app/src/content/assets'
GALLERY_CONTENT = f'{GALLERY}/app/src/content/gallery'
ARCHIVES = 'transport/collection-archives.json'
IMPORTS = 'sources/imports/asset-manifest.json'
CARDIAC_EXPORTS = PurePosixPath('heart/Cardiac_Atlas/exports/EXPORT_CONTRACT.json')
PUBLICATION = f'{GALLERY}/snapshot-reference.json'
ACTIVE_STATUS = frozenset({'ready', 'wip', 'blocked', 'deferred'})
LINK = re.compile(r'\]\((<?[^\s)>]+>?)(?:\s+"[^"]*")?\)')
CODE_PATH = re.compile(r'`([\w./ -]+)`')
RIGHTS_NAME = re.compile(r'^(licen[sc]e|copying|notice|attribution|credits)([-_.]|$)', re.I)


def read_json(root, relative):
    return json.loads(repo_file(root, str(relative)).read_bytes(), object_pairs_hook=unique_keys)


def values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from values(child)
    elif isinstance(value, list):
        for child in value:
            yield from values(child)


def local_references(markdown, owner):
    for match in LINK.findall(markdown):
        link = urlsplit(match.strip('<>'))
        if not link.scheme and not link.netloc and link.path and not link.path.startswith('/'):
            yield posixpath.normpath(posixpath.join(owner.parent.as_posix(), unquote(link.path)))
    yield from CODE_PATH.findall(markdown)


def explain(root, paths):
    wanted = dict.fromkeys(source_path(path) for path in paths)
    matches = defaultdict(set)
    gaps = []

    def add(path, reason, owner):
        if path in wanted:
            matches[path].add((reason, str(owner)))

    with locked_store(root):
        check_promotion_journal(root)
        current = CurrentTeaching(root)
        maintained = {(selection.path, selection.task_id): selection for selection, _ in current.selected()}
        for path, task in current.entries:
            accepted = current.resolve(path, task)
            owner = accepted.owner.relative_to(root)
            add(path, f'Accepted teaching task {task}', owner)
            add(str(owner), f'Accepted review for {path} · {task}', ASSESSMENTS)
            base = current.entries[path, task]['base']['path']
            add(base, f'Pinned base review for {path} · {task}', ASSESSMENTS)
            if (selection := maintained.get((path, task))) is not None:
                add(path, f'Maintained selection · {selection.family} · {task}', SELECTIONS)
                add(selection.shared_owner, f'Shared family provenance · {selection.family}', SELECTIONS)
            for fields, reason in ((('sources', 'views'), 'Teaching provenance or evidence'),
                                   (('target', 'refinement'), 'Teaching comparison or refinement')):
                for field in fields:
                    for reference in values(accepted.row.get(field)):
                        add(reference.split('#', 1)[0], f'{reason} · {path} · {task}', owner)

        for output, record in current.identities.displays.items():
            master = record['source']['path']
            add(master, f'Display master for {output}', DISPLAY_DERIVATIVES)
            add(output, f'Declared display derivative of {master}', DISPLAY_DERIVATIVES)

    def add_assets(catalog, reason, owner):
        for asset in catalog['assets']:
            route = f"/assets/{asset['sha256']}/{asset['name']}"
            for path in current_paths(asset):
                add(path, f'{reason} {route}', owner)
            for path in asset.get('historicalPaths', []):
                add(path, f'{reason} historical source for {route}', owner)
        for receipt in catalog.get('receipts', []):
            add(receipt['path'], 'Candidate Gallery review receipt', owner)

    for manifest, label in (
        (DELIVERY_INDEX, 'Current public Gallery declaration'),
        (f'{GALLERY_ASSETS}/local-delivery.json', 'Candidate Gallery read declaration'),
        (f'{GALLERY_ASSETS}/legacy-dental-assets.json', 'Optional legacy Dental Review declaration'),
    ):
        add_assets(read_json(root, manifest), label, manifest)

    published = read_json(root, PUBLICATION)['livePublication']
    revision = published['repositoryRevision']
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Published repository revision must be a commit identity')
    frozen = subprocess.run(['git', '--no-lazy-fetch', 'show', f'{revision}:{DELIVERY_INDEX}'],
                            cwd=root, capture_output=True)
    if frozen.returncode == 0:
        add_assets(json.loads(frozen.stdout, object_pairs_hook=unique_keys),
                   f"Recorded v{published['version']} Gallery declaration", f'{revision}:{DELIVERY_INDEX}')
    else:
        gaps.append(f"Recorded v{published['version']} declarations are unavailable in local Git history ({revision}).")

    for name in ('library-packages.json', 'static-reviews.json'):
        owner = f'{GALLERY_CONTENT}/{name}'
        for reference in values(read_json(root, owner)):
            add(reference, 'Named Library or comparison reference', owner)

    roots = recipe_roots(root)
    graph = verify_graph(root, roots)
    for path in wanted:
        if path in roots:
            add(path, 'Maintained recipe entry point or declared input', 'tools/verify_recipe_dependencies.py')
        elif path in graph or any(path.startswith(entry + '/') and (root / entry).is_dir() for entry in roots):
            add(path, 'Dependency of a maintained recipe', 'tools/verify_recipe_dependencies.py')

    for bundle in read_json(root, IMPORTS)['bundles']:
        for entry in bundle['files']:
            add(entry['path'], f"Imported provenance · {bundle['archive']}", IMPORTS)
    for name, digest in read_json(root, CARDIAC_EXPORTS)['sha256'].items():
        path = (CARDIAC_EXPORTS.parent / name).as_posix()
        add(path, f'Exact Cardiac Atlas export · SHA-256 {digest}', CARDIAC_EXPORTS)
        if name.endswith('.json'):
            packed = path + '.gz'
            add(path, f'Cardiac recovery backing path · {packed}', CARDIAC_EXPORTS)
            add(packed, f'Cardiac recovery backing for {path} · SHA-256 {digest} after expansion', CARDIAC_EXPORTS)
    for path in wanted:
        candidate = root / path
        if candidate.resolve() != candidate:
            add(path, 'Linked path · inspect its resolved target before any change', 'local checkout')
        elif candidate.is_file() and RIGHTS_NAME.match(PurePosixPath(path).name):
            add(path, 'License or attribution record', PurePosixPath(path).parent)

    for path in sorted((root / 'records/work-items/items').glob('*.md')):
        owner = path.relative_to(root)
        body = repo_file(root, owner.as_posix()).read_text()
        frontmatter = body.split('---', 2)
        status = re.search(r'^work_status: (\w+)$', frontmatter[1], re.M) if len(frontmatter) == 3 else None
        if status and status[1] in ACTIVE_STATUS:
            for reference in local_references(body, owner):
                add(reference, f'Open work item ({status[1]})', owner)

    for record in sorted((root / 'transport/manifests').glob('*.json')):
        owner = record.relative_to(root)
        for entry in read_json(root, owner)['objects']:
            add(entry['file'], 'Pinned transport or recovery record', owner)
    for archive, record in read_json(root, ARCHIVES).items():
        if 'checksumList' in record:
            checksums = record['checksumList']['path']
            add(checksums, f'Archive membership checksums · {archive}', ARCHIVES)
            for path in checksum_members(root, record):
                add(path, f'Declared recovery member · {archive}', checksums)
            for path in record.get('mediaBytes', {}):
                add(path, 'Optional local Gallery film', ARCHIVES)
        else:
            gaps.append(f'{archive} lists members inside its ZIP. That member list was not inspected.')

    return {path: sorted(matches[path]) for path in wanted}, gaps


def print_explanation(root, paths):
    records, gaps = explain(root, paths)
    for path, reasons in records.items():
        print(path)
        for reason, owner in reasons:
            print(f'  {reason} ({owner})')
        if not reasons:
            print('  No reference found in the inspected sources.')
    for gap in gaps:
        print(f'  Coverage gap: {gap}')
    print('External consumers, dynamic references and archive availability need separate checks. '
          'An empty result does not establish that a path can be deleted.')
