"""Serve the gallery and its explicitly referenced local files on loopback."""

import argparse
import json
import mimetypes
from hashlib import sha256
import shutil
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

from gallery_plan import GALLERY, REPO, SOURCE
from report import build, digest
from viewer_catalog import DEFAULT_PORT, GALLERY_URL, relative_url


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("src", "href") and value:
                url = urlsplit(value)
                if not url.scheme and not url.netloc and url.path:
                    self.paths.append(unquote(url.path))


def gallery_files():
    """Index explicit document links, including the linked baseline report."""
    files = {}
    pending = [GALLERY / "index.html"]
    while pending:
        path = pending.pop().resolve()
        if not path.is_relative_to(REPO) or not path.is_file():
            continue
        url = relative_url(path)
        if url in files:
            continue
        files[url] = path
        if path.suffix == ".html" and path.is_relative_to(GALLERY):
            links = References()
            links.feed(path.read_text())
            pending.extend(path.parent / link for link in links.paths)
    return files


def viewer_vendor(fetch):
    fixture = json.loads((SOURCE.parents[1] / "ci/glb-runtime-fixture.json").read_text())
    controls_path = SOURCE.parents[1] / "tests/candidate_camera/vendor-binding.json"
    controls = json.loads(controls_path.read_text())["orbitControls"]
    orbit = "vendor/examples/jsm/controls/OrbitControls.js"
    resources = [item for item in fixture["resources"] if item["path"].startswith("vendor/")]
    resources.append({
        **controls, "path": orbit,
        "url": f"https://raw.githubusercontent.com/mrdoob/three.js/{fixture['threeCommit']}/examples/jsm/controls/OrbitControls.js",
    })
    cache = GALLERY / "viewer-vendor"
    files = {}
    for resource in resources:
        relative = resource["path"]
        wanted = resource["sha256"]
        cached = cache / relative
        paths = [cached, REPO / "lessons/one-breath/.local" / relative]
        if relative == orbit:
            paths.append(REPO / ".artifacts/verification-consolidation/vendor/OrbitControls.js")
        candidate = next((p for p in paths if p.is_file() and digest(p) == wanted), None)
        if candidate is None and fetch:
            with urlopen(resource["url"], timeout=30) as response:
                payload = response.read(resource["bytes"] + 1)
            if sha256(payload).hexdigest() != wanted:
                raise ValueError(f"Downloaded vendor identity differs: {relative}")
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(payload)
            candidate = cached
        if candidate is None:
            raise ValueError(f"Missing pinned {relative}. Start with --fetch-vendor to restore it.")
        files["/viewer/" + relative] = candidate
    return files


def routes(port, fetch):
    vendor = viewer_vendor(fetch)
    catalog = build(viewer_port=port)
    files = gallery_files()
    files.update(vendor)
    for key, relative in catalog.pop("assets").items():
        path = (REPO / relative).resolve()
        if not path.is_relative_to(REPO) or digest(path) != key:
            raise ValueError(f"Invalid local model: {Path(relative).name}")
        files[f"/viewer/assets/{key}.glb"] = path
    viewer = SOURCE / "viewer"
    files.update({"/viewer/": viewer / "index.html", "/viewer/style.css": viewer / "style.css",
                  "/viewer/viewer.mjs": viewer / "viewer.mjs"})
    return files, json.dumps(catalog).encode()


def handler_for(files, catalog, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.reply(send_body=True)

        def do_HEAD(self):
            self.reply(send_body=False)

        def reply(self, send_body):
            if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path == "/":
                self.send_response(302)
                self.send_header("Location", GALLERY_URL)
                self.end_headers()
                return
            if path == "/viewer/catalog.json":
                self.ok("application/json", len(catalog))
                if send_body:
                    self.wfile.write(catalog)
                return
            file = files.get(path)
            if file is None or not file.is_file():
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(file)[0] or "application/octet-stream"
            if file.suffix == ".mjs":
                content_type = "text/javascript"
            with file.open("rb") as source:
                self.ok(content_type, file.stat().st_size)
                if send_body:
                    shutil.copyfileobj(source, self.wfile)

        def ok(self, content_type, length):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; connect-src 'self' blob:; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--fetch-vendor", action="store_true", help="Restore missing pinned Three.js modules")
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), BaseHTTPRequestHandler) as server:
        port = server.server_port
        files, catalog = routes(port, args.fetch_vendor)
        server.RequestHandlerClass = handler_for(files, catalog, port)
        print(f"http://127.0.0.1:{port}/", flush=True)
        server.timeout = 2
        expires = monotonic() + 4 * 3600
        while monotonic() < expires:
            server.handle_request()


if __name__ == "__main__":
    main()
