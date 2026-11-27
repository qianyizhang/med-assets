"""Add the authored Ultrasound tour/chapter inventory from its playback source of truth."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from .governance import Catalog, Consumer, GovernanceError, build_catalog as build_base_catalog

OWNERS = ("vascular", "organs", "pregnancy", "echo")
CASES_ROOT = Path("experiments/ultrasound-sweep/cases")
EVIDENCE_SCRIPT = Path("experiments/ultrasound-sweep/tours/case-evidence.mjs")

@dataclass(frozen=True)
class CompleteCatalog(Catalog):
    def to_dict(self):
        result = super().to_dict()
        result["counts"]["ultrasoundTours"] = sum(
            row.kind == "modeled-case" and row.domain == "ultrasound-anatomy" for row in self.consumers
        )
        result["counts"]["ultrasoundTourChapters"] = sum(
            row.kind == "tour-chapter" and row.domain == "ultrasound-anatomy" for row in self.consumers
        )
        return result

def authored_tour_chapters(repo: Path):
    script = repo / EVIDENCE_SCRIPT
    if not script.is_file():
        return (), {}
    visits = []
    owners = {}
    for owner in OWNERS:
        case_file = repo / CASES_ROOT / owner / "cases.json"
        if not case_file.is_file():
            continue
        try:
            records = json.loads(case_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GovernanceError(f"Invalid Ultrasound tour source {case_file}: {exc}") from exc
        if not isinstance(records, list):
            raise GovernanceError(f"Expected case array: {case_file}")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                raise GovernanceError(f"Invalid authored case in {case_file}")
            visits.append({"owner": owner, "record": record})
            owners[record["id"]] = (owner, case_file.relative_to(repo).as_posix(), record)
    try:
        result = subprocess.run(
            ["node", str(script)], cwd=repo, input=json.dumps(visits), text=True,
            capture_output=True, check=True, timeout=90,
        )
        chapters = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"Could not derive authored Ultrasound tour chapters: {exc}") from exc
    consumers = []
    hashes = {EVIDENCE_SCRIPT.as_posix(): __import__("hashlib").sha256(script.read_bytes()).hexdigest()}
    for case_id, (owner, case_path, record) in owners.items():
        owner_script = repo / CASES_ROOT / owner / "playable.js"
        if owner_script.is_file():
            hashes[owner_script.relative_to(repo).as_posix()] = __import__("hashlib").sha256(owner_script.read_bytes()).hexdigest()
        chapter_rows = chapters.get(case_id)
        if not isinstance(chapter_rows, list):
            raise GovernanceError(f"Missing chapter evidence for authored tour {case_id}")
        for index, chapter in enumerate(chapter_rows):
            required = ("id", "title", "frames", "evidenceFrame", "observation")
            if any(key not in chapter for key in required):
                raise GovernanceError(f"Incomplete authored chapter: {case_id}/{index}")
            identity = f"ultrasound:tour-chapter:{case_id}:{chapter['id']}"
            consumers.append(Consumer(
                identity, "ultrasound-anatomy", "tour-chapter",
                f"{record.get('title', case_id)} · {chapter['title']}",
                chapter["observation"], "authored-tour-chapter",
                case_path,
                {"caseId":case_id,"family":record.get("family"),"chapterId":chapter["id"],
                 "chapterIndex":index,"viewImage":chapter.get("viewImage"),"frames":chapter["frames"],
                 "evidenceFrame":chapter["evidenceFrame"],"measurement":chapter.get("measurement"),
                 "color":chapter.get("color"),"chapterSource":"playable.js"})
            )
    return tuple(consumers), hashes

def build_catalog(repo: Path) -> CompleteCatalog:
    repo = repo.resolve()
    base = build_base_catalog(repo)
    chapters, hashes = authored_tour_chapters(repo)
    combined = list(base.consumers) + list(chapters)
    identities = [row.consumer_id for row in combined]
    if len(identities) != len(set(identities)):
        raise GovernanceError("Duplicate consumer identity after Ultrasound tour expansion")
    source_hashes = dict(base.source_hashes)
    source_hashes.update(hashes)
    return CompleteCatalog(base.repository, base.packages, tuple(combined), source_hashes)
