"""Build a local adrenal round trip using the real survey and system report."""
import hashlib
from html import escape
import json
import os
from pathlib import Path
import shutil
from string import Template
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SURVEY = HERE.parent / "model-survey"
SYSTEMS = HERE.parent / "body-systems-survey"
sys.path.insert(0, str(SURVEY / "tools"))
from framework import prepare

sys.path.insert(0, str(SYSTEMS))
from gallery_plan import GALLERY
from report import build as build_systems

OUT = GALLERY / "adrenal-pilot"
RECORD = REPO / "reviews/adrenals/2026-10-23-bp3d-bounded-migration/bounded-record.json"
FAMILY = "adrenals"


def read(path):
    return json.loads(path.read_text())


def checked(path, digest):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
            raise ValueError(f"Pilot identity differs for {path.name}")
    return path


def relative(path):
    return Path(os.path.relpath(path, OUT)).as_posix()


def exact_candidate(row, record, candidates):
    artifact = record["artifact"]
    candidate = next((c for c in candidates if c["id"] == record["variantId"]), None)
    if not candidate or Path(candidate["source"]["file"]).name != artifact["sha256"] + ".glb.gz":
        raise ValueError("Verification candidate does not identify the recorded export")
    if not any((m["path"], m["sha256"], m["bytes"]) ==
               (artifact["file"], artifact["sha256"], artifact["bytes"]) for m in row["media"]):
        raise ValueError("Model Survey has no exact match for the review export")
    if checked(REPO / artifact["file"], artifact["sha256"]).stat().st_size != artifact["bytes"]:
        raise ValueError("Verification record has the wrong byte count")
    return candidate


def verification_page(record, candidate):
    pictures = {e["label"]["en"]: relative(checked(REPO / e["file"], e["sha256"]))
                for e in record["evidence"] if e["reviewPhase"] == "candidate"}
    artifact = record["artifact"]
    return Template((HERE / "verification.html").read_text()).substitute(
        candidate=escape(candidate["id"]), pair=pictures["oblique"], contact=pictures["contact"],
        size=f'{artifact["bytes"]:,}', sha=artifact["sha256"], model=relative(REPO / artifact["file"]),
        record=relative(RECORD), gates="".join(
            f'<dt>{escape(axis.title())}</dt><dd><b>{escape(g["status"])}</b> · {escape(g["scope"])}</dd>'
            for axis, g in record["gates"].items()
        ),
    )


def main():
    # Reuse the pinned framework, restored survey snapshot and its installed lockfile tree.
    original_hash = read(SURVEY / "snapshot-reference.json")["sourceSnapshotSha256"]
    original = checked(SURVEY / f".local/preview/dist/snapshot.{original_hash}.json", original_hash)
    snapshot = read(SURVEY / "app/src/data.json")
    snapshot["previewGallery"] = read(original)["previewGallery"]
    row = next(r for r in snapshot["queries"]["model_survey"]["rows"] if r["id"] == FAMILY)
    record = read(RECORD)
    candidates = read(REPO / "tests/gallery/fixtures/entries.json")["candidates"]
    candidate = exact_candidate(row, record, candidates)
    study = next(e for e in read(SYSTEMS / "refinements/surface-quality.json") if e["id"] == "surface-adrenal")
    build_systems()
    target = f'refinement-{study["id"]}'
    available = f'id="{target}"' in (GALLERY / "index.html").read_text()
    config = dict(family=FAMILY, candidate=candidate["id"], sha256=record["artifact"]["sha256"],
                  modelPath=record["artifact"]["file"], hasSystemView=available,
                  study=(f"../index.html#{target}" if available else relative(REPO / study["comparisonPage"])))
    verification = verification_page(record, candidate)
    with TemporaryDirectory(prefix="gallery-pilot-", dir=GALLERY) as temp:
        work = prepare(SURVEY, SURVEY / ".local/publication", Path(temp) / "project")
        modules = SURVEY / ".local/app/node_modules"
        if not modules.is_dir():
            raise ValueError("Install the Model Survey's locked dependencies in its prepared project")
        (work / "node_modules").symlink_to(modules, target_is_directory=True)
        (work / "src/data.json").write_text(json.dumps(snapshot, ensure_ascii=False))
        subprocess.run(["npm", "run", "build"], cwd=work, check=True,
                       env={**os.environ, "VITE_ADRENAL_PILOT": json.dumps(config)})
        OUT.mkdir(exist_ok=True)
        (OUT / "verification.html").write_text(verification)
        shutil.copyfile(work / "dist/index.html", OUT / "model-survey.html")
    build_systems()
    print(OUT / "model-survey.html")


if __name__ == "__main__":
    main()
