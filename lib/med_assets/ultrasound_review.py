"""Validate retained ultrasound workbench review packages and assembled recipe identities."""

import json
from hashlib import sha256

from .artifacts import HEX64, POINTER_PREFIX, parse_pointer, repo_file, unique_keys


def recipe_hashes(destination, owners, records, *, rubric):
    """Invalidate scores if the modeled family, a fitted surface or the rubric changes."""
    destination = destination.resolve()
    hashes = {}

    def digest(paths):
        for path in paths:
            if path not in hashes:
                relative = path.relative_to(destination).as_posix()
                hashes[path] = sha256(repo_file(destination, relative).read_bytes()).hexdigest()
        return sorted((str(path.relative_to(destination)), hashes[path]) for path in paths)

    regional_meshes = {}
    if owners - {"echo"}:
        for path in destination.rglob("*.mesh"):
            relative = path.relative_to(destination)
            group = relative.parts[1] if relative.parts[0] == "sweeps" else relative.parts[0]
            regional_meshes.setdefault(group, []).append(path)

    result = {}
    for owner in sorted(owners):
        modules = list((destination / "cases" / owner).glob("playable*.js"))
        inputs = [destination / "case-scene.js", destination / "scene.js"]
        if owner == "echo":
            inputs += list((destination / "cardiac").rglob("*.js"))
            inputs += list((destination / "cardiac/torso").glob("*.raw"))
        else:
            groups = {
                "organs": ("scenes", "liver", "breast", "axilla", "thyroid", "carotid", "kidney"),
                "vascular": ("thyroid", "carotid", "scenes"),
                "pregnancy": ("pregnancy", "scenes"),
            }[owner]
            for group, paths in regional_meshes.items():
                if group.startswith(groups):
                    inputs.extend(paths)
            if owner == "vascular":
                inputs.append(destination / "cases/organs/playable-scene-skin.js")
        fingerprint = dict(
            modules=digest(set(modules + inputs)),
            rubric=sha256(rubric.read_bytes()).hexdigest(),
            cases=[row["record"] for row in records if row["owner"] == owner],
        )
        result[owner] = sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    return result


AXES = frozenset({"fidelity", "form", "readability", "economy"})
MAX_AXIS_SCORE = 4
RUBRIC_PATH = "docs/guides/asset-quality.md"


def chapter_mesh_bindings(destination, evidence, *, validate_mesh):
    """Fingerprint files declared by the player for a specific chapter part."""
    bindings = {}
    digests = {}

    def digest(path, *, mesh=False):
        if (path, mesh) not in digests:
            raw = repo_file(destination, path).read_bytes()
            if mesh:
                validate_mesh(raw, path)
            digests[path, mesh] = sha256(raw).hexdigest()
        return digests[path, mesh]

    for case, chapters in evidence.items():
        for chapter in chapters:
            for part, binding in chapter.get("reviewMeshes", {}).items():
                path = binding["path"]
                fingerprint = {
                    "case": case,
                    "chapter": chapter["id"],
                    "part": part,
                    "frame": chapter["evidenceFrame"],
                    "observation": chapter["observation"],
                    "measurement": chapter.get("measurement"),
                    "placement": binding["placement"],
                    "inputs": {name: digest(name) for name in binding["inputs"]},
                }
                chapter_sha = sha256(
                    json.dumps(fingerprint, sort_keys=True, allow_nan=False).encode()
                ).hexdigest()
                parts = bindings.setdefault(case, {}).setdefault(chapter["id"], {})
                parts[part] = {
                    "path": path,
                    "meshSha256": digest(path, mesh=True),
                    "chapterSha256": chapter_sha,
                }
    return bindings


def review_images(record):
    """Return the witnesses named in a workbench review's matched views."""
    comparison = record.get("comparison", {})
    return tuple(
        dict.fromkeys(
            view[field]
            for view in [comparison, *comparison.get("views", [])]
            for field in ("baseline", "candidate", "original")
            if field in view
        )
    )


def validate_reviews(path, *, allow_lfs_pointers=False):
    """Validate retained assessments and their witnesses, independent of qualification status."""
    document = json.loads(path.read_text(), object_pairs_hook=unique_keys)
    if document.get("version") != 1 or not isinstance(document.get("records"), list):
        raise ValueError(f"Invalid asset review package: {path}")
    files = {}
    bindings = []
    for record in document["records"]:
        if not all(
            record.get(key)
            for key in ("case", "part", "task", "revision", "rubric", "reviewer", "reviewedOn")
        ):
            raise ValueError(f"Incomplete asset review identity: {path}")
        extra = record.get("additionalUses", [])
        chapter_mesh_review = "chapterSha256" in record or (
            "meshSha256" in record and record.get("source") != "sweep"
        )
        if chapter_mesh_review and (
            record.get("source") != "case"
            or not record.get("chapter")
            or extra
            or record.get("occurrence", 1) != 1
            or not all(
                isinstance(value, str) and HEX64.fullmatch(value)
                for value in (
                    record.get("meshSha256"),
                    record.get("chapterSha256"),
                    document.get("rubricHash"),
                )
            )
        ):
            raise ValueError(f"Invalid chapter mesh review binding: {path}")
        base = {key: value for key, value in record.items() if key != "additionalUses"}
        bindings.append(base)
        for use in extra:
            if not use.get("case") or use.keys() - {"case", "chapter"}:
                raise ValueError(f"Invalid additional asset review use: {path}")
            bindings.append(base | use)
        scores = record.get("scores", {})
        if scores.keys() - AXES:
            raise ValueError(f"Unknown asset review axis: {path}")
        for axis, grade in scores.items():
            if grade is not None and (
                type(grade) is not int
                or not 0 <= grade <= MAX_AXIS_SCORE
                or not record.get("scoreEvidence", {}).get(axis)
            ):
                raise ValueError(f"Unsubstantiated asset review score: {path} / {axis}")
        for image in review_images(record):
            try:
                media = repo_file(path.parents[2], image)
            except ValueError as exc:
                raise ValueError(f"Missing or unbound asset review image: {image}") from exc
            if not media.is_relative_to(path.parent.resolve()):
                raise ValueError(f"Missing or unbound asset review image: {image}")
            if media not in files:
                raw = media.read_bytes()
                if allow_lfs_pointers and raw.startswith(POINTER_PREFIX):
                    files[media] = parse_pointer(raw)[0]
                else:
                    files[media] = sha256(raw).hexdigest()
    expected = document.get("evidenceSha256", {})
    actual = {
        f.relative_to(path.parent.resolve()).as_posix(): digest for f, digest in files.items()
    }
    if expected != actual:
        raise ValueError(f"Asset review evidence identity mismatch: {path}")
    return document | {"records": bindings}
