"""Load local before/after evidence from explicitly named render receipts."""

from hashlib import file_digest
import json
import math
from pathlib import Path

from gallery_plan import REFINEMENT, REPO, SOURCE, load


def local_path(relative, root=REPO):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes its directory: {relative}")
    return path


def verify_file(path, expected):
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"Evidence hash differs: {path.name}")


def evidence(spec, plates):
    """Return a view, its inputs, and the directory containing the exact images."""
    expected_input = spec.get("model")
    if "scene" in spec:
        folder, view = plates.get((spec["scene"], spec["view"]), (None, None))
        if folder is None:
            raise FileNotFoundError(f"Missing gallery view {spec['scene']}/{spec['view']}")
        receipt = json.loads((folder / "renders.json").read_text())
    else:
        path = local_path(spec["receipt"])
        folder = path.parent
        receipt = json.loads(path.read_text())
        matches = [entry for entry in receipt["views"] if entry["id"] == spec["view"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one view called {spec['view']} in {path}")
        view = matches[0]

    if "inputs" in receipt:
        inputs = receipt["inputs"]
    else:
        model = view.get("glb") or {"file": receipt["glb"], "sha256": receipt["sha256"]}
        if not expected_input or Path(expected_input).name != model["file"]:
            raise ValueError(f"Missing model identity for {folder.name}/{view['id']}")
        inputs = [{"path": expected_input, "sha256": model["sha256"]}]
    if not inputs:
        raise ValueError(f"Missing model inputs in {folder.name}")
    for source in inputs:
        verify_file(local_path(source["path"]), source["sha256"])
    if [Path(item["file"]).stem.rsplit("-", 1)[-1] for item in view["images"]] != ["iso", "ortho"]:
        raise ValueError(f"Expected isometric and orthographic evidence in {folder.name}")
    for image in view["images"]:
        verify_file(local_path(image["file"], folder), image["sha256"])
    return folder, view, inputs


def comparable(before, after):
    a, b = before[1], after[1]
    return math.isclose(a["orthographicScale"], b["orthographicScale"], abs_tol=1e-6) and all(
        math.isclose(x, y, abs_tol=1e-6)
        for left, right in zip(a["images"], b["images"], strict=True)
        for field in ("direction", "camera")
        for x, y in zip(left[field], right[field], strict=True)
    )


def definitions():
    for manifest in sorted((SOURCE / "refinements").glob("*.json")):
        yield from json.loads(manifest.read_text())
    for item in load("regional-views.json"):
        prefix = (REFINEMENT / "regional-renders").relative_to(REPO)
        yield {
            **item,
            "matched": True,
            "before": {"receipt": f"{prefix}/{item['id']}-original/renders.json", "view": item["view"]},
            "after": {"receipt": f"{prefix}/{item['id']}-updated/renders.json", "view": item["view"]},
        }
