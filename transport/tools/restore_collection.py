"""Restore cold payloads to their original repository paths from a pinned ZIP."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "transport/collection-archives.json"
ENDPOINT = "https://r2-object-library.landy123007.chatgpt.site/download"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(data, row, name):
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError(f"Byte identity mismatch: {name}")


def target(root, name):
    relative = PurePosixPath(name)
    if not relative.parts or relative.is_absolute() or relative.as_posix() != name or ".." in relative.parts:
        raise ValueError(f"Unsafe archive member: {name}")
    path = root / relative
    if path.resolve() != path:
        raise ValueError(f"Symlink in restore path: {name}")
    return path


def restore(row, root, local_zip=None):
    if local_zip:
        data = local_zip.read_bytes()
    else:
        url = ENDPOINT + "?" + urlencode({"key": row["key"]})
        request = Request(url, headers={"User-Agent": "ObjectLibraryCLI/1.1"})
        with build_opener(NoRedirect()).open(request, timeout=180) as response:
            data = response.read(row["bytes"] + 1)
    check(data, row, row["file"])
    with ZipFile(io.BytesIO(data)) as archive:
        members = json.loads(archive.read("members.json"))
        pending = []
        for name, identity in members.items():
            payload = archive.read(name)
            check(payload, identity, name)
            if identity["role"] != "payload":
                continue
            path = target(root, name)
            if path.exists():
                check(path.read_bytes(), identity, name)
            else:
                pending.append((name, path))
        for name, path in pending:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent) as staged:
                staged.write(archive.read(name))
                staged.flush()
                try:
                    os.link(staged.name, path)
                except FileExistsError:
                    check(path.read_bytes(), members[name], name)
    return len(pending)


if __name__ == "__main__":
    catalog = json.loads(CATALOG.read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection", choices=sorted(catalog))
    parser.add_argument("--from-zip", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    count = restore(catalog[args.collection], args.output.resolve(), args.from_zip)
    print(f"{args.collection}: verified; restored {count} files")
