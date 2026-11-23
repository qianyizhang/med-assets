"""Restore a pinned collection or named subset to its original repository paths."""
import argparse
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'lib'))
from med_assets.artifacts import HEX64, install_verified, repo_file, source_path, unique_keys, verify_bytes, verify_payload

CATALOG = ROOT / "transport/collection-archives.json"
ENDPOINT = "https://r2-object-library.landy123007.chatgpt.site/download"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def checksum_members(repo, row):
    """Read the exact external SHA256SUMS used by recovery and film assembly."""
    record = row['checksumList']
    raw = verify_bytes(repo_file(repo, record['path']).read_bytes(), record)
    members = {}
    for line in raw.decode().splitlines():
        digest, name = line.split('  ', 1)
        source_path(name)
        if name in members or not HEX64.fullmatch(digest):
            raise ValueError(f'Invalid or duplicate archive checksum: {name}')
        members[name] = {'path': name, 'sha256': digest, 'role': 'payload'}
    if len(members) != row['payloads']:
        raise ValueError('Archive checksum list count differs')
    for name, size in row.get('mediaBytes', {}).items():
        members[name]['bytes'] = size
    return members


def manifest(archive, row, repo):
    infos = {}
    for info in archive.infolist():
        source_path(info.filename.rstrip('/') if info.is_dir() else info.filename)
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError(f'Linked archive member: {info.filename}')
        if info.filename in infos:
            raise ValueError(f'Duplicate archive member: {info.filename}')
        infos[info.filename] = info
    files = {name for name, entry in infos.items() if not entry.is_dir()}
    if 'checksumList' in row:
        members = checksum_members(repo, row)
    else:
        if 'members.json' not in files:
            raise ValueError('Collection ZIP is missing its member manifest')
        files.remove('members.json')
        members = json.loads(archive.read('members.json'), object_pairs_hook=unique_keys)
    if set(members) != files:
        raise ValueError('Archive files differ from its member manifest')
    for name, record in members.items():
        record['path'] = name
        size = infos[name].file_size
        if record.setdefault('bytes', size) != size:
            raise ValueError(f'Archive member size differs: {name}')
    return members


def restore(row, root, local_zip=None, *, subset=None, repo=ROOT):
    prefix = None
    if subset is not None:
        prefix = row.get('subsets', {}).get(subset)
        if prefix is None:
            raise ValueError(f'Unknown collection subset: {subset}')
        prefix = source_path(prefix) + '/'
    if local_zip:
        data = local_zip.read_bytes()
    else:
        url = ENDPOINT + "?" + urlencode({"key": row["key"]})
        request = Request(url, headers={"User-Agent": "ObjectLibraryCLI/1.1"})
        with build_opener(NoRedirect()).open(request, timeout=180) as response:
            data = response.read(row["bytes"] + 1)
    verify_bytes(data, {**row, 'path': row['file']})
    with ZipFile(io.BytesIO(data)) as archive:
        members = manifest(archive, row, repo)
        selected = 0
        pending = []
        for name, identity in members.items():
            if prefix and not name.startswith(prefix):
                continue
            verify_bytes(archive.read(name), identity)
            if identity['role'] != 'payload':
                continue
            selected += 1
            path = repo_file(root, name, exists=False)
            if path.exists():
                verify_payload(path, identity)
            else:
                pending.append((path, identity))
        if not selected:
            raise ValueError('No payloads match the selected collection or subset')
        for path, identity in pending:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent) as staged:
                staged.write(archive.read(identity['path']))
                staged.flush()
                install_verified(Path(staged.name), path, identity)
    return len(pending)


if __name__ == "__main__":
    catalog = json.loads(CATALOG.read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection", choices=sorted(catalog))
    parser.add_argument("--from-zip", type=Path)
    parser.add_argument("--subset", help="Named subset from the collection catalog")
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        count = restore(catalog[args.collection], args.output.resolve(), args.from_zip, subset=args.subset)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, f'Restore refused: {error}\n')
    print(f"{args.collection}: verified; restored {count} files")
