"""Resolve accepted teaching records and render their maintained views."""
from collections import Counter, defaultdict
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re
import os
from typing import NamedTuple

from .artifacts import HEX64, repo_file, source_path, unique_keys
from .derivatives import AssessmentIdentities

REGISTER = "docs/gallery/maintained-models.md"
REGISTER_TABLE_HEADER = "| Register entry | Selected export |"
SCORECARD = "records/campaigns/teaching-asset-review/current-coverage.md"
PROMOTION_JOURNAL = "reviews/teaching-assessments/.promotion.json"
SELECTIONS = "docs/gallery/maintained-selections.json"
ASSESSMENTS = "reviews/teaching-assessments/current-assessments.json"
ATTRIBUTION = ("evaluator", "date", "rubric")
STABLE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
EXPORT_OWNERS = ("models/", "assemblies/", "lessons/", "heart/", "body/")
MARKDOWN_PUNCTUATION = str.maketrans({char: f"&#{ord(char)};" for char in "|[]*_`~\\<>"})


class Selection(NamedTuple):
    path: str
    task_id: str
    assessment_sha256: str
    collection: str
    collection_id: str
    family_id: str
    family: str
    label: str
    shared_owner: str | None


class AcceptedAssessment(NamedTuple):
    owner: Path
    attribution: dict
    row: dict
    task_id: str
    sha256: str


def require(condition, message):
    if not condition:
        raise ValueError(message)


def document(path):
    return teaching_document(path.read_text(), path)


def teaching_document(raw, name):
    result = json.loads(raw, object_pairs_hook=unique_keys)
    require(type(result["schemaVersion"]) is int and result["schemaVersion"] == 1,
            f"Unsupported teaching schema: {name}")
    return result


def assessment_digest(row):
    data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


@contextmanager
def locked_store(repo, *, exclusive=False):
    owner = repo / Path(ASSESSMENTS).parent
    require(owner == owner.resolve(), f"Linked teaching store: {owner}")
    descriptor = os.open(owner, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Lock the existing directory so read-only checkouts need no lock file.
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        os.close(descriptor)


def check_promotion_journal(repo):
    journal = repo_file(repo, PROMOTION_JOURNAL, exists=False)
    require(not journal.exists(), "Interrupted teaching promotion. Run tools/maintained_teaching.py recover.")


def valid_id(identifier):
    require(isinstance(identifier, str) and STABLE_ID.fullmatch(identifier), f"Invalid teaching ID: {identifier}")
    return identifier


def title(value):
    require(isinstance(value, str) and value.strip() == value and bool(value)
            and value.splitlines() == [value], f"Invalid register title: {value!r}")
    return value


def markdown_label(value):
    # Keep literal character references while leaving ordinary ampersands readable.
    value = re.sub(r"&(?=(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);)", "&amp;", value)
    return value.translate(MARKDOWN_PUNCTUATION)


def exact_export(relative):
    source_path(relative)
    require(relative.startswith(EXPORT_OWNERS) and Path(relative).suffix in (".blend", ".glb"),
            f"Teaching export has no asset owner: {relative}")
    return relative


def selections(repo, register=None):
    repo = repo.resolve()
    if register is None:
        with locked_store(repo):
            check_promotion_journal(repo)
            register = document(repo_file(repo, SELECTIONS))
    families = register["families"]
    for identifier, family in families.items():
        valid_id(identifier)
        title(family["label"])
        if "owner" in family:
            owner = source_path(family["owner"])
            path = repo / owner
            require(path == path.resolve() and path.is_file() and path.name == "README.md",
                    f"Family owner is unavailable: {owner}")
    collection_ids = set()
    collection_labels = set()
    used_families = set()
    chosen = {}
    for collection in register["collections"]:
        identifier, name = valid_id(collection["id"]), title(collection["label"])
        require(identifier not in collection_ids and name not in collection_labels and collection["families"],
                f"Duplicate or empty collection: {identifier}")
        collection_ids.add(identifier)
        collection_labels.add(name)
        members = set()
        member_labels = set()
        for member in collection["families"]:
            family_id = valid_id(member["id"])
            family = families[family_id]
            require(family_id not in members and member["exports"], f"Duplicate or empty family: {family_id} in {name}")
            members.add(family_id)
            owner = family.get("owner")
            require(family_id not in used_families or owner, f"Cross-listed family has no shared owner: {family_id}")
            used_families.add(family_id)
            label = title(member["label"]) if "label" in member else family["label"]
            require(bool(owner) == ("label" in member), f"Shared family label and owner must agree: {family_id}")
            row_label = (label, family["label"]) if owner else (label,)
            require(row_label not in member_labels, f"Ambiguous family label: {label} in {name}")
            member_labels.add(row_label)
            for entry in member["exports"]:
                path = exact_export(entry["path"])
                require(path not in chosen, f"Duplicate maintained selection: {path}")
                digest = entry["assessmentSha256"]
                require(HEX64.fullmatch(digest or ""), f"Invalid selected assessment pin: {path}")
                chosen[path] = Selection(path, valid_id(entry["taskId"]), digest, name, identifier,
                                         family_id, family["label"], label, owner)
    require(chosen and used_families == families.keys(), "Maintained register is empty or contains unused families")
    return chosen


def validate_teaching_axes(assessment, name):
    require(assessment["task"].strip() and assessment["sources"], f"Missing teaching task or evidence: {name}")
    axes = assessment["axes"]
    require(len(axes) == 4, f"Expected four teaching assessment axes: {name}")
    for axis in axes:
        score = axis["score"]
        require(score is None or (type(score) is int and 0 <= score <= 4),
                f"Invalid teaching assessment score: {name}")
        require(isinstance(axis["observation"], str) and axis["observation"].strip(),
                f"Missing teaching assessment observation: {name}")


def validate_assessment(repo, identities, row):
    path = row["export"]["path"]
    validate_teaching_axes(row, path)
    require(row["views"], f"Missing reviewed views: {path}")
    views = {view["path"] for view in row["views"]}
    require(len(views) == len(row["views"]), f"Duplicate reviewed view: {path}")
    for claim in (row["export"], *row["views"]):
        require(type(claim["bytes"]) is int and claim["bytes"] > 0, f"Invalid reviewed byte size: {claim['path']}")
        identities.check(claim)
    for source in row["sources"]:
        if "path" in source:
            try:
                repo_file(repo, source["path"].split("#", 1)[0])
            except ValueError as error:
                raise ValueError(f"Missing or linked assessment source: {source['path']}") from error
        else:
            require(source.get("url", "").startswith("https://"), f"Missing assessment source: {path}")
    if "teachingView" in row:
        require(row["teachingView"] in views, f"Teaching view is outside the reviewed views: {path}")
    for key in ("refinement", "target"):
        if key in row:
            result = row[key]
            require({result["before"], result["after"]} <= views, f"Comparison witness is outside the reviewed views: {path}")
    if "target" in row:
        target = row["target"]
        exemptions = target["exemptions"]
        low = {str(index) for index, axis in enumerate(row["axes"]) if axis["score"] is None or axis["score"] < 3}
        require(exemptions.keys() == low and all(
            detail[field].strip() for detail in exemptions.values() for field in ("reason", "permittedUse", "reopen")
        ), f"Invalid accepted teaching exemptions: {path}")
        require(target["taskCheck"].strip() and target["status"] in ("passed", "blocked"),
                f"Missing learner outcome: {path}")


class CurrentTeaching:
    def __init__(self, repo, *, register=None, catalog=None):
        self.repo = repo.resolve()
        if register is None and catalog is None:
            with locked_store(self.repo):
                check_promotion_journal(self.repo)
                register = document(repo_file(self.repo, SELECTIONS))
                catalog = document(repo_file(self.repo, ASSESSMENTS))
        self.selections = selections(self.repo, register)
        self.memberships = {(collection["id"], family["id"])
                            for collection in register["collections"] for family in collection["families"]}
        self.attributions = catalog["attributions"]
        self.entries = {}
        self.base = {}
        self.resolved = {}
        self.identities = AssessmentIdentities(self.repo)
        self.tasks = {}
        for entry in catalog["assessments"]:
            path, task_id = exact_export(entry["path"]), valid_id(entry["taskId"])
            require((path, task_id) not in self.entries, f"Duplicate assessment for {path} and task {task_id}")
            if "familyId" in entry or "collectionId" in entry:
                require((entry.get("collectionId"), entry.get("familyId")) in self.memberships,
                        f"Unknown accepted teaching family for {path} and task {task_id}")
            self.entries[path, task_id] = entry

    def resolve(self, path, task_id):
        if (path, task_id) in self.resolved:
            return self.resolved[path, task_id]
        entry = self.entries.get((path, task_id))
        require(entry is not None, f"Accepted assessment missing for {path} and task {task_id}")
        base_pin = entry["base"]
        base = repo_file(self.repo, base_pin["path"])
        require(base.is_relative_to(self.repo / "reviews"),
                f"Invalid assessment owner: {base_pin['path']}")
        if base not in self.base:
            batch = document(base)
            originals = {}
            for row in batch["assessments"]:
                originals.setdefault(assessment_digest(row), []).append(row)
            self.base[base] = batch, originals
        batch, originals = self.base[base]
        matches = originals.get(base_pin["sha256"], [])
        require(len(matches) == 1 and matches[0]["export"]["path"] == path, f"Base assessment pin differs: {path}")
        original = matches[0]

        changes = entry.get("changes", {})
        additions = entry.get("additions", {})
        axes = entry.get("axisChanges", {})
        require(changes.keys() <= (original.keys() | {"refinement", "target", "teachingView"}) - {"axes", "export", "task"}
                and additions.keys() <= {"sources", "views"} and changes.keys().isdisjoint(additions),
                f"Invalid effective assessment fields: {path}")
        require(axes.keys() <= {"0", "1", "2", "3"}, f"Invalid changed teaching axis: {path}")
        if changes or additions or axes:
            require("review" in entry and "attribution" in entry, f"Missing effective assessment provenance: {path}")
        owner = source_path(entry.get("review", base_pin["path"]))
        review_path = self.repo / owner
        require(review_path.is_relative_to(self.repo / "reviews") and review_path == review_path.resolve()
                and review_path.is_file(), f"Missing or linked accepted review: {owner}")
        attribution = self.attributions[entry["attribution"]] if "attribution" in entry else {key: batch[key] for key in ATTRIBUTION}
        require(all(attribution[key].strip() for key in ("evaluator", "date")) and attribution["rubric"],
                f"Missing review attribution: {path}")
        row = {**original, **changes}
        for field, more in additions.items():
            row[field] = [*original[field], *more]
        if axes:
            row["axes"] = [axes.get(str(index), axis) for index, axis in enumerate(original["axes"])]
        digest = assessment_digest({"owner": owner, "attribution": attribution, "assessment": row, "taskId": task_id})
        require(digest == entry["sha256"], f"Accepted assessment pin differs: {path} and task {task_id}")
        require(self.tasks.setdefault(task_id, row["task"]) == row["task"], f"Conflicting task text for {task_id}")
        validate_assessment(self.repo, self.identities, row)
        record = AcceptedAssessment(review_path, attribution, row, task_id, digest)
        self.resolved[path, task_id] = record
        return record

    def selected(self, *, paths=None):
        for path, selection in self.selections.items():
            if paths is not None and path not in paths:
                continue
            assessment = self.resolve(path, selection.task_id)
            require(assessment.sha256 == selection.assessment_sha256, f"Stale maintained assessment pin: {path}")
            require(assessment.row.get("target", {}).get("status") != "blocked",
                    f"A blocked learner outcome cannot be maintained: {path}")
            entry = self.entries[path, selection.task_id]
            if "familyId" in entry:
                require((entry["collectionId"], entry["familyId"]) == (selection.collection_id, selection.family_id),
                        f"Accepted family differs from selected family: {path}")
            yield selection, assessment

    def validate_current(self):
        """Check every accepted task, including tasks omitted from the Gallery view."""
        for path, task_id in self.entries:
            self.resolve(path, task_id)
        # Gallery resolution also validates each selected pin and alternative membership.
        for _ in self.gallery():
            pass
        return len(self.entries)

    def gallery(self):
        selected = {selection.path: assessment for selection, assessment in self.selected()}
        alternatives = set()
        for path, task_id in self.entries:
            if path in selected:
                if task_id == selected[path].task_id:
                    yield selected[path]
                continue
            require(path not in alternatives, f"Several current tasks without a selected assessment: {path}")
            alternatives.add(path)
            yield self.resolve(path, task_id)

    def maintained_exports(self):
        exports = {}
        for selection, assessment in self.selected():
            if selection.path.endswith(".glb"):
                file = assessment.row["export"]
                exports.setdefault((file["sha256"], file["bytes"]), selection.path)
        return exports


def validate_current(repo):
    """Validate a consistent on-disk snapshot and its two tracked views."""
    repo = repo.resolve()
    with locked_store(repo):
        check_promotion_journal(repo)
        current = CurrentTeaching(repo, register=document(repo_file(repo, SELECTIONS)),
                                  catalog=document(repo_file(repo, ASSESSMENTS)))
        count = current.validate_current()
        require(repo_file(repo, REGISTER).read_text() == render_register(current.selections),
                "Maintained register drift.")
        require(repo_file(repo, SCORECARD).read_text() == render_scorecard(current), "Coverage report drift.")
        return count


def render_register(current):
    lines = [
        '<a id="maintained-3d-model-families"></a>', "",
        "# Teaching register", "",
        "This register covers selected 3D assets and is generated from the [exact export and task selections](maintained-selections.json). Each row represents one register entry in its collection and may list several selected exports. A shared entry can appear in more than one collection.", "",
        "The [scorecard](../../records/campaigns/teaching-asset-review/current-coverage.md) reports register IDs and export–task pairs separately. See the [counting rules](asset-library.md#review-coverage) for the scope of these counts and the evidence required for an asset inventory.", "",
        "Each multi-model Blender entry opens an editable assembly for its stated task. Use the [Library](asset-library.md) for exact asset revisions, component meshes, alternatives, credits and evidence.", "",
        "Each selection serves the learner task recorded in the scorecard. Source studies, editable masters and alternate views remain available through revision history. The [exemption recheck](../../records/campaigns/teaching-exemption-recheck.md) identifies local default changes, their before/after evidence and exceptions. Existing published routes retain their original deliveries.", "",
    ]
    groups = {}
    for selection in current.values():
        row = groups.setdefault(selection.collection, {})
        label = markdown_label(selection.family)
        if selection.shared_owner:
            shared_label = markdown_label(selection.label)
            label = f"{shared_label} · [{label}](../../{selection.shared_owner})"
        exports = row.setdefault((selection.family_id, label), [])
        exports.append(f"[{Path(selection.path).name}](../../{selection.path})")
    for collection, rows in groups.items():
        lines.extend([f"## {markdown_label(collection)}", "", REGISTER_TABLE_HEADER, "| --- | --- |"])
        lines.extend(f"| {label} | {'<br>'.join(exports)} |" for (_, label), exports in rows.items())
        lines.append("")
    return "\n".join(lines)


def link(label, path):
    if path.startswith("https://"):
        return f"[{label}]({path})"
    return f"[{label}](../../../{path})"


def cell(value):
    return str(value).replace("|", r"\|").replace("\n", " ")


def table(columns, rows):
    return [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *("| " + " | ".join(map(cell, row)) + " |" for row in rows),
        "",
    ]


STATES = ("Full", "Partial", "Unrated")

def render_scorecard(current):
    rows = []
    counts = defaultdict(Counter)
    entry_ids = defaultdict(set)
    entry_exports = Counter((item.collection, item.family_id) for item in current.selections.values())
    for selection, assessment in current.selected():
        row = assessment.row
        scores = [axis["score"] for axis in row["axes"]]
        rated = sum(score is not None for score in scores)
        coverage = "Full" if rated == 4 else "Partial" if rated else "Unrated"
        target = "At target" if all(score is not None and score >= 3 for score in scores) else (
            "Exemption" if row.get("target", {}).get("exemptions") else "Open")
        collection = selection.collection
        counts[collection].update({target: 1, coverage: 1, "Export–task pairs": 1})
        entry_ids[collection].add(selection.family_id)
        label = selection.label
        if entry_exports[collection, selection.family_id] > 1:
            label += f" · {Path(selection.path).stem}"
        if selection.shared_owner:
            label = f"{selection.family} · {label}"
        rows.append((markdown_label(collection), link(markdown_label(label), selection.path),
                     *("—" if score is None else score for score in scores),
                     target, link("Evidence", assessment.owner.relative_to(current.repo).as_posix())))

    entry_ids["**Total**"] = set().union(*entry_ids.values())
    counts["**Total**"] = sum(counts.values(), Counter())
    lines = [
        "# Maintained teaching asset scorecard", "",
        "The total counts distinct register IDs under the existing `families` key across collections. Coverage and target counts apply to selected export–task pairs. See the [counting rules](../../../docs/gallery/asset-library.md#review-coverage) for the scope of both counts.", "",
        "Use the [rubric](../../../docs/guides/asset-quality.md) for the anchors and the "
        "[exemption recheck](../teaching-exemption-recheck.md) for the current before/after decisions and owned follow-ups.", "",
        "Run `python3.12 records/campaigns/teaching-asset-review/coverage.py --audit --baseline a6f4b3c` for every identity, "
        "historical alternate, evidence gap and register change.", "",
    ]
    count_columns = ("At target", "Exemption", "Open", *STATES, "Export–task pairs")
    lines += table(("Collection", "Register IDs", *count_columns), (
        (markdown_label(collection) if collection != "**Total**" else collection,
         len(entry_ids[collection]), *(count[column] for column in count_columns))
        for collection, count in counts.items()
    ))
    lines += table(("Collection", "Selected export", "Fidelity", "Form", "Readability", "Economy", "Target", "Review"), rows)
    return "\n".join(lines)
