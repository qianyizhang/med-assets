"""Plan and recover a local promotion of an exact owner assessment."""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .artifacts import HEX64, repo_file, unique_keys
from .teaching import (
    ASSESSMENTS, ATTRIBUTION, PROMOTION_JOURNAL, REGISTER, SCORECARD, SELECTIONS,
    CurrentTeaching, assessment_digest, check_promotion_journal, exact_export, locked_store,
    render_register, render_scorecard, require, teaching_document, title, valid_id,
)

STATE_FILES = (ASSESSMENTS, SELECTIONS, REGISTER, SCORECARD)


@dataclass(frozen=True)
class Promotion:
    review: str
    reviewed_sha256: str | None
    export: str
    task_id: str
    collection_id: str
    family_id: str
    disposition: str
    replaces: str | None = None
    new_family_label: str | None = None


def read_state(repo):
    return {name: repo_file(repo, name).read_bytes().decode() for name in STATE_FILES}


def from_state(repo, state):
    return CurrentTeaching(
        repo,
        register=teaching_document(state[SELECTIONS], SELECTIONS),
        catalog=teaching_document(state[ASSESSMENTS], ASSESSMENTS),
    )


def reviewed_entry(repo, promotion, known_task):
    owner = repo_file(repo, promotion.review)
    require(owner.is_relative_to(repo / "reviews") and owner != repo / ASSESSMENTS,
            "Promotion requires an owner assessment under reviews/.")
    batch = teaching_document(owner.read_text(), promotion.review)
    if promotion.reviewed_sha256 is not None:
        require(HEX64.fullmatch(promotion.reviewed_sha256), "Invalid reviewed assessment SHA-256.")
        matches = [row for row in batch["assessments"] if assessment_digest(row) == promotion.reviewed_sha256]
        require(len(matches) == 1, "Reviewed assessment pin is stale, missing or ambiguous.")
    else:
        matches = [row for row in batch["assessments"] if row["export"]["path"] == promotion.export
                   and row.get("taskId", promotion.task_id) == promotion.task_id
                   and (known_task is None or row["task"] == known_task)]
        require(matches, "Owner review has no matching export and task.")
        if len(matches) > 1:
            choices = "\n".join(f"  {assessment_digest(row)}  {row['task']}" for row in matches)
            raise ValueError("Owner review has several matching assessments. Select --reviewed-sha256:\n" + choices)
    row = matches[0]
    require(row["export"]["path"] == promotion.export, "Reviewed assessment belongs to a different export.")
    require(row.get("taskId", promotion.task_id) == promotion.task_id,
            "Reviewed assessment belongs to a different task ID.")
    attribution = {key: batch[key] for key in ATTRIBUTION}
    digest = assessment_digest({
        "owner": promotion.review, "attribution": attribution, "assessment": row, "taskId": promotion.task_id,
    })
    return {
        "path": promotion.export, "taskId": promotion.task_id, "familyId": promotion.family_id,
        "collectionId": promotion.collection_id,
        "base": {"path": promotion.review, "sha256": assessment_digest(row)}, "sha256": digest,
    }


def change_selection(member, current, promotion, pin):
    existing = current.selections.get(promotion.export)
    if existing is not None:
        require((existing.collection_id, existing.family_id) == (promotion.collection_id, promotion.family_id),
                "Export is already selected in a different family.")
    if promotion.disposition == "alternative":
        require(promotion.replaces is None, "A retained alternative cannot replace a maintained export.")
        require(existing is None or existing.task_id != promotion.task_id,
                "This task is maintained. Promote a replacement to change its disposition.")
        return

    replacement = {"path": promotion.export, "taskId": promotion.task_id, "assessmentSha256": pin}
    exports = member["exports"]
    prior_path = promotion.replaces or promotion.export
    prior = next((index for index, item in enumerate(exports) if item["path"] == prior_path), None)
    if prior is None:
        if promotion.replaces:
            require(any(item == replacement for item in exports)
                    and any(path == prior_path for path, _ in current.entries),
                    "Replacement is not selected in this family.")
        else:
            exports.append(replacement)
    else:
        require(existing is None or promotion.export == prior_path,
                "Replacement would duplicate an existing selection.")
        exports[prior] = replacement


def promotion_member(register, promotion):
    collection = next((item for item in register["collections"] if item["id"] == promotion.collection_id), None)
    require(collection is not None, f"Unknown teaching collection: {promotion.collection_id}")
    families = register["families"]
    family = families.get(promotion.family_id)
    member = next((item for item in collection["families"] if item["id"] == promotion.family_id), None)
    if promotion.new_family_label is None:
        require(member is not None, "Unknown collection and family placement.")
    elif family is not None:
        require(member is not None and family["label"] == promotion.new_family_label,
                "New family must have a distinct stable ID and label.")
    else:
        require(promotion.disposition == "maintained" and promotion.replaces is None,
                "Admit a new family with its first maintained export.")
        families[promotion.family_id] = {"label": title(promotion.new_family_label)}
        member = {"id": promotion.family_id, "exports": []}
        collection["families"].append(member)
    return member


def describe(assessment):
    if assessment is None:
        return None
    row = assessment.row
    return {
        "sha256": assessment.sha256,
        "export": row["export"],
        "taskId": assessment.task_id,
        "task": row["task"],
        "route": row.get("route"),
        "axes": row["axes"],
        "evidence": {"sources": row["sources"], "views": row["views"], "teachingView": row.get("teachingView")},
        "target": row.get("target"),
        "decision": row.get("decision"),
        "attribution": assessment.attribution,
    }


def describe_selection(current, path):
    selection = current.selections.get(path)
    if selection is None:
        return None
    return {
        "path": path, "taskId": selection.task_id, "assessmentSha256": selection.assessment_sha256,
        "familyId": selection.family_id, "collectionId": selection.collection_id,
    }


def serialized(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def plan_promotion(repo, before, promotion):
    exact_export(promotion.export)
    if promotion.replaces is not None:
        exact_export(promotion.replaces)
        require(promotion.replaces != promotion.export, "Choose a different export to replace.")
    for identifier in (promotion.family_id, promotion.collection_id, promotion.task_id):
        valid_id(identifier)
    require(promotion.disposition in ("alternative", "maintained"), "Unknown promotion disposition.")

    current = from_state(repo, before)
    current.validate_current()
    register = teaching_document(before[SELECTIONS], SELECTIONS)
    catalog = teaching_document(before[ASSESSMENTS], ASSESSMENTS)
    member = promotion_member(register, promotion)

    entry = reviewed_entry(repo, promotion, current.tasks.get(promotion.task_id))
    key = (promotion.export, promotion.task_id)
    previous = current.entries.get(key)
    if previous and "familyId" in previous:
        require((previous["collectionId"], previous["familyId"]) == (promotion.collection_id, promotion.family_id),
                "Assessment already belongs to a different family.")
    if previous is None:
        catalog["assessments"].append(entry)
    elif previous != entry:
        catalog["assessments"][catalog["assessments"].index(previous)] = entry

    change_selection(member, current, promotion, entry["sha256"])
    after = dict(before)
    for name, data in ((ASSESSMENTS, catalog), (SELECTIONS, register)):
        if data != teaching_document(before[name], name):
            after[name] = serialized(data)
    proposed = from_state(repo, after)
    proposed.validate_current()
    new_assessment = proposed.resolve(*key)
    after[REGISTER] = render_register(proposed.selections)
    after[SCORECARD] = render_scorecard(proposed)
    paths = dict.fromkeys((promotion.export, promotion.replaces or promotion.export))
    replaced = current.selections.get(promotion.replaces)
    report = {
        "export": promotion.export,
        "review": promotion.review,
        "reviewedSha256": entry["base"]["sha256"],
        "taskId": promotion.task_id,
        "collectionId": promotion.collection_id,
        "familyId": promotion.family_id,
        "familyLabel": register["families"][promotion.family_id]["label"],
        "disposition": promotion.disposition,
        "assessmentBefore": describe(current.resolved.get(key)),
        "assessmentAfter": describe(new_assessment),
        "replacedAssessment": describe(current.resolve(replaced.path, replaced.task_id)) if replaced else None,
        "galleryMembership": any(assessment.sha256 == new_assessment.sha256 for assessment in proposed.gallery()),
        "selectionBefore": [value for path in paths if (value := describe_selection(current, path)) is not None],
        "selectionAfter": [value for path in paths if (value := describe_selection(proposed, path)) is not None],
        "changedFiles": [name for name in STATE_FILES if before[name] != after[name]],
        "planSha256": assessment_digest({"before": before, "after": after, "promotion": asdict(promotion)}),
    }
    return after, report


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_atomic(path, content):
    with NamedTemporaryFile(dir=path.parent, prefix=".promotion-stage-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
            os.fchmod(stream.fileno(), mode)
            stream.write(content.encode())
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
            sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)


def apply_journal(repo, journal, before, after):
    current = read_state(repo)
    for name in STATE_FILES:
        require(current[name] in (before[name], after[name]), f"Teaching promotion conflicts with an edit to {name}.")
    for name in STATE_FILES:
        if current[name] != after[name]:
            path = repo_file(repo, name)
            require(path.read_bytes().decode() == before[name], f"Teaching promotion input changed: {name}")
            write_atomic(path, after[name])
    journal.unlink()
    sync_directory(journal.parent)


def promote(repo, promotion, *, apply=False, expect_state=None):
    repo = repo.resolve()
    with locked_store(repo, exclusive=apply):
        check_promotion_journal(repo)
        before = read_state(repo)
        after, report = plan_promotion(repo, before, promotion)
        if apply and report["changedFiles"]:
            require(expect_state == report["planSha256"],
                    "Promotion plan is stale or missing. Run dry run and use its planSha256 with --expect-state.")
            require(read_state(repo) == before, "Promotion inputs changed during validation.")
            journal = repo_file(repo, PROMOTION_JOURNAL, exists=False)
            write_atomic(journal, serialized({"before": before, "after": after}))
            apply_journal(repo, journal, before, after)
        report["status"] = ("applied" if apply else "dry-run") if report["changedFiles"] else "unchanged"
        return report


def recover(repo):
    repo = repo.resolve()
    with locked_store(repo, exclusive=True):
        journal = repo_file(repo, PROMOTION_JOURNAL, exists=False)
        if not journal.exists():
            return False
        record = json.loads(journal.read_text(), object_pairs_hook=unique_keys)
        before, after = record["before"], record["after"]
        require(before.keys() == after.keys() == set(STATE_FILES), "Invalid teaching promotion journal.")
        proposed = from_state(repo, after)
        proposed.validate_current()
        require(render_register(proposed.selections) == after[REGISTER]
                and render_scorecard(proposed) == after[SCORECARD], "Promotion journal has incompatible views.")
        apply_journal(repo, journal, before, after)
        return True
