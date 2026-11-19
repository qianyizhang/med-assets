"""Bind local viewer launches to the same source and view plans as the gallery."""

from pathlib import Path
from urllib.parse import quote, urlencode

from gallery_plan import GALLERY, REPO

DEFAULT_PORT = 8847
GALLERY_URL = "/" + quote((GALLERY / "index.html").relative_to(REPO).as_posix())
STOMACH = {
    "path": "body/anatomy-workshop-r1/meshes/stomach.glb",
    "sha256": "cc4a9c4bee03d921b9985fa39b8a96021e31dade3237a285a2cac20ff670a8a6",
}


def relative_url(path):
    return "/" + quote(path.relative_to(REPO).as_posix())


class Catalog:
    def __init__(self, port, jobs):
        self.port = port
        self.plans = {job["id"]: job for job in jobs}
        self.scenes = {}
        self.assets = {}

    def input(self, source):
        path, digest = source["path"], source["sha256"]
        existing = self.assets.setdefault(digest, path)
        # Identical bytes served once. Their labels and material groups still belong to the view.
        if not (REPO / existing).is_file():
            raise ValueError(f"Missing local viewer input: {Path(existing).name}")
        return {**source, "url": f"/viewer/assets/{digest}.glb"}

    def register(self, folder, view, title, system, *, whole=False):
        job = self.plans[folder.name]
        planned_view = next(item for item in job["views"] if item["id"] == view["id"])
        key = f"{job['id']}/{'model' if whole else view['id']}"
        return self.add(key, folder, view, title, system, job["inputs"],
                        None if whole else planned_view.get("include"))

    def add(self, key, folder, view, title, system, inputs, include):
        straight = view["images"][1]
        x, y, z = straight["direction"]
        self.scenes[key] = {
            "title": title,
            "system": system,
            "inputs": [self.input(source) for source in inputs],
            "include": include,
            "direction": [x, z, -y],
            "fallback": relative_url(folder / straight["file"]),
        }
        return self.url(key)

    def url(self, key):
        return f"http://127.0.0.1:{self.port}/viewer/?" + urlencode({"scene": key})

    def data(self):
        raw = self.scenes.get("digestive-s1233/assembly")
        comparison = [raw["inputs"][0], self.input(STOMACH)] if raw and (REPO / STOMACH["path"]).is_file() else None
        return {
            "gallery": GALLERY_URL, "scenes": self.scenes,
            "comparison": comparison, "assets": self.assets,
        }
