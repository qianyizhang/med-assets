#!/usr/bin/env python3
"""Regenerate the exact-file coverage report from the register and review owners."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "transport/tools"))
from lfs_transport import parse_pointer, unique_keys
sys.path.insert(0, str(ROOT / "tools"))
from teaching_assessments import REGISTER, campaign_rows, register_rows, register_selections

BASELINE = "a6f4b3c"
GALLERY = "sites/anatomy-gallery/app/src/content/gallery/"
PILOT = "reviews/teaching-assessments/2026-11-21-library-pilot/assessments.json"
SURFACES = "reviews/body-systems/2026-11-20-surface-quality"
AXES = ("Fidelity", "Form and surface", "Teaching readability", "Mesh economy")
STATES = ("Full", "Partial", "Unrated")
ASSEMBLIES = {
    "body/anatomy-workshop-r1/Anatomy_Workshop.blend": (
        "The Workshop assembles multiple systems. Choose an assembly-level learner task and view.",
        "body/anatomy-workshop-r1/README.md",
    ),
    "body/breathing/Breathing_Assembly.blend": (
        "The replay checks the assembly and clips. A named learner action in the assembly needs a rubric assessment.",
        "records/work-items/items/AG-GAL-024-retire-builds-and-replay-breathing.md",
    ),
}
GAPS = {
    **ASSEMBLIES,
    "models/bronchial_tree/exports/distal-sampling-r14/bronchial_distal_sampling.glb": (
        "The first-fork trial binds geometry and views to r14. Assign r14 scores separately from r13.",
        "reviews/bronchial_tree/2026-11-21-distal-simplification-trial/README.md",
    ),
    "heart/exterior-presentation-r02/exports/static-opaque-exterior-repacked.glb": (
        "The packaging comparison confirms equivalent views and scene data. Assess the exact r02 for a named learner task.",
        "heart/exterior-presentation-r02/README.md",
    ),
}


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_keys)


def identity(repo, path):
    file = (repo / path).resolve()
    if not file.is_relative_to(repo) or not file.is_file():
        raise ValueError(f"Missing or outside repository: {path}")
    with file.open("rb") as stream:
        header = stream.read(128)
        if header.startswith(b"version https://git-lfs.github.com/spec/"):
            return parse_pointer(header + stream.read())
        stream.seek(0)
        return hashlib.file_digest(stream, "sha256").hexdigest(), file.stat().st_size


def expected_match(repo, claim):
    try:
        digest, size = identity(repo, claim["path"])
    except ValueError as error:
        return str(error)
    if digest != claim.get("sha256") or (claim.get("bytes") is not None and size != claim["bytes"]):
        return f"Identity mismatch for {claim['path']}"
    return ""


def records(repo):
    owners = sorted((repo / "reviews").glob("*/*/teaching-assessment.json"))
    def inputs():
        for path in (repo / PILOT, *owners):
            document = read_json(path)
            if document["schemaVersion"] != 1:
                raise ValueError(f"Unsupported assessment schema in {path}")
            for item in document["assessments"]:
                yield path, document, item, False
        for path, document, item in campaign_rows(repo):
            yield path, document, item, True

    for path, document, item, campaign in inputs():
        yield {
            **item,
            "source": path.relative_to(repo).as_posix(),
            "source_label": f"{path.name} · {item.get('route', Path(item['export']['path']).stem)}",
            "campaign": campaign,
            "evaluator": document.get("evaluator"), "date": document.get("date"), "rubric": document.get("rubric"),
        }


def bound_views(repo, receipt, view_id, path):
    matches = [view for view in read_json(repo / receipt)["views"] if view["id"] == view_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one {view_id} view in {receipt}")
    view = matches[0]
    if view["glb"]["file"] != Path(path).name:
        raise ValueError(f"Render receipt export name differs from {path}")
    images = [
        {"path": str(Path(receipt).parent / image["file"]), "sha256": image["sha256"]}
        for image in view["images"]
    ]
    return {"path": path, "sha256": view["glb"]["sha256"]}, images


def overview(repo, key, path, view, column):
    name, anchor, task = {
        "nail": ("Seated nail", "seated-nail-unit", "Trace the nail from the root under the fold, across the supporting bed and out to the unsupported free edge."),
        "airspaces": ("Terminal airspaces", "terminal-airspaces", "Follow air through the bronchiole into a shared duct and the alveolar recesses."),
        "adrenal": ("s1233 adrenals", "adrenals-in-their-scan-frame", "Locate the left and right adrenal relative to the same-side kidney in the retained scan frame."),
    }[key]
    source = f"{SURFACES}/README.md"
    row = next(line for line in (repo / source).read_text().splitlines() if line.startswith(f"| {name} |"))
    scores = [int(cell.split("→")[column].strip()) for cell in row.split("|")[2:6]]
    return legacy(repo, source, anchor, f"{SURFACES}/views/{key}/renders.json", view, path, task, scores, "2026-11-20")


def legacy(repo, source, anchor, receipt, view, path, task, scores, date):
    export, images = bound_views(repo, receipt, view, path)
    return {
        "export": export,
        "views": images,
        "sources": [receipt, source],
        "source": f"{source}#{anchor}",
        "source_label": "Independent review" if "r05/" in source else "Retained review",
        "task": task,
        "evaluator": "Agent review (see source for attribution)",
        "date": date,
        "axes": [{"score": score, "observation": f"See {source}#{anchor}."} for score in scores],
        "rubric": {"path": "docs/guides/asset-quality.md"},
    }


def choose_section(repo, path, heading):
    return (repo / path).read_text().split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def adrenal_review(repo, revision, path, view):
    owner = "r04" if revision == "r03" else "r05"
    directory = f"reviews/endocrine-locator/adrenal-study-{owner}"
    heading = "Reassessment" if owner == "r04" else "Independent assessment"
    source = f"{directory}/README.md"
    section = choose_section(repo, source, heading)
    scored_rows = [line.split("|")[1:-1] for line in section.splitlines() if re.match(
        r"^\| (Fidelity|Form and surface|Teaching readability|Mesh economy)\b", line,
    )]
    if owner == "r04":
        scores = [int(row[1].replace("*", "").split("→")[0].strip()) for row in scored_rows]
    else:
        index = 1 if revision == "r04" else 2
        scores = [int(row[index].strip()) for row in scored_rows]
    date = "2026-11-20"
    return legacy(
        repo, source, heading.lower().replace(" ", "-"), f"{directory}/renders.json", view,
        path, "Locate both adrenal glands relative to the same-side kidneys, then isolate them and inspect their gross exterior.",
        scores, date,
    )


def historical(repo):
    originals = {
        "nail": "models/skin/teaching-block-r01/skin-block.glb",
        "airspaces": "lessons/one-breath/airway-r01/airway-route.glb",
        "adrenal": "assemblies/endocrine-locator/r02/s1233-adrenals.glb",
    }
    for key, path in originals.items():
        yield overview(repo, key, path, "original", 0)
    for entry in read_json(repo / (GALLERY + "reviewed-entries.json")):
        key = {"seated-nail-r02": "nail", "terminal-airspaces-r02": "airspaces"}[entry["id"]]
        retained = overview(repo, key, entry["exportPath"], "updated", 1)
        yield retained
        yield {
            **retained,
            "source": GALLERY + "reviewed-entries.json",
            "source_label": f"Gallery · {entry['id']}",
            "axes": [{"score": score, "observation": entry["evidence"]["url"]} for score in entry["axes"]],
            "date": entry["reviewDate"],
        }
    files = {
        "r03": "assemblies/endocrine-locator/adrenal-study-r03/s1233-adrenals-teaching.glb",
        "r04": "assemblies/endocrine-locator/adrenal-study-r04/s1233-adrenals-illustrative.glb",
        "r05": "assemblies/endocrine-locator/adrenal-study-r05/s1233-adrenals-regional.glb",
    }
    retained = {
        "r03": overview(repo, "adrenal", files["r03"], "updated", 1),
        "r04": adrenal_review(repo, "r04", files["r04"], "original"),
        "r05": adrenal_review(repo, "r05", files["r05"], "updated"),
    }
    reassessment = adrenal_review(repo, "r03", files["r03"], "original")
    yield reassessment
    yield from retained.values()
    catalog = (repo / (GALLERY + "adrenal-study.js")).read_text()
    entries = re.findall(
        r"^\s*(r\d+): \{ suffix: '([^']+)', axes: (\[[^\]]+\]), review: '([^']+)' \},$",
        catalog, re.MULTILINE,
    )
    if {entry[0] for entry in entries} != files.keys() or len(entries) != len(files):
        raise ValueError("Unmapped or duplicate adrenal Gallery revision")
    for revision, suffix, axes, review in entries:
        item = retained[revision]
        if revision == "r03" and review in (reassessment["source"], reassessment["source"].split("#")[0]):
            item = reassessment
        if (Path(files[revision]).stem != f"s1233-adrenals-{suffix}"
                or review not in (item["source"], item["source"].split("#")[0])):
            raise ValueError(f"Unmapped adrenal Gallery evidence for {revision}")
        yield {
            **item,
            "source": GALLERY + "adrenal-study.js",
            "source_label": f"Gallery · {revision}",
            "axes": [{"score": score, "observation": review} for score in json.loads(axes)],
        }


def rate(repo, item):
    axes = item["axes"]
    if len(axes) != 4 or any(
        axis["score"] is not None and (type(axis["score"]) is not int or not 0 <= axis["score"] <= 4)
        for axis in axes
    ):
        return "Unrated", "Invalid axis scores."
    if (not all(item.get(key, "").strip() for key in ("task", "evaluator", "date"))
            or not all(item.get(key) for key in ("rubric", "sources", "views"))):
        return "Unrated", "Missing task, attribution, rubric, reference or reviewed-view evidence."
    if not all(axis.get("observation", "").strip() for axis in axes):
        return "Unrated", "Missing score observations."
    for claim in (item["export"], *item["views"]):
        reason = expected_match(repo, claim)
        if reason:
            return "Unrated", reason + "."
    missing = [name for name, axis in zip(AXES, axes) if axis["score"] is None]
    if not missing:
        return "Full", "Four rated axes."
    if len(missing) == 4:
        return "Unrated", "All four axes lack scores."
    return "Partial", " ".join(
        f"{name} — {axis['observation']}" for name, axis in zip(AXES, axes) if axis["score"] is None
    )


def select(repo, items):
    rated = [(item, *rate(repo, item)) for item in items]
    campaign = [r for r in rated if r[0].get("campaign") and not expected_match(repo, r[0]["export"])]
    if campaign:
        newest = max(item["date"] for item, _, _ in campaign)
        rated = [r for r in campaign if r[0]["date"] == newest]
        if len(rated) != 1:
            return "Unrated", "Several campaign assessments share the newest date. Select a campaign task explicitly."
    usable = [r for r in rated if r[1] != "Unrated"]
    if len({tuple(a["score"] for a in item["axes"]) for item, _, _ in usable}) > 1:
        return "Unrated", "Several score profiles match this file. Resolve the task or review disagreement."
    if len({" ".join(item["task"].casefold().split()) for item, _, _ in usable}) > 1:
        return "Unrated", "Several tasks match this file. Select a campaign task explicitly."
    if usable:
        _, state, reason = usable[0]
        if any(r[1] == "Unrated" for r in rated):
            reason += " See assessment evidence below for a rejected binding."
        return state, reason
    if rated:
        return "Unrated", " ".join(dict.fromkeys(reason for _, _, reason in rated))
    return "Unrated", "No attributable rubric assessment for this starting file and a named task."


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


def assessment_row(repo, item):
    export = item["export"]
    state, reason = rate(repo, item)
    scores = " / ".join("—" if axis["score"] is None else str(axis["score"]) for axis in item["axes"])
    return (
        link(Path(export["path"]).name, export["path"]) if (repo / export["path"]).is_file() else f"`{export['path']}`",
        f"`{export.get('sha256', 'missing')}`",
        link(item["source_label"], item["source"]),
        item.get("evaluator") or "Missing", item.get("date") or "Missing", item.get("task") or "Missing",
        scores, f"{state}. {reason}",
    )


def report(repo, audit=False):
    raw = (repo / REGISTER).read_text()
    selections = register_selections(raw)
    maintained = {path: (item.collection, item.label) for path, item in selections.items()}
    pinned = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{BASELINE}:{REGISTER}"], text=True,
    )
    baseline = register_rows(pinned)
    added = maintained.keys() - baseline.keys()
    removed = baseline.keys() - maintained.keys()
    moved = [path for path in maintained.keys() & baseline.keys() if maintained[path] != baseline[path]]
    assessments = defaultdict(list)
    for item in (*records(repo), *historical(repo)):
        assessments[item["export"]["path"]].append(item)

    rows = []
    scorecard = []
    family_exports = Counter(maintained.values())
    family_keys = {item.shared_owner or (item.collection, item.family) for item in selections.values()}
    families = Counter(collection for collection, _ in {(item.collection, item.family) for item in selections.values()})
    target_counts = defaultdict(Counter)
    counts = defaultdict(Counter)
    for path, (collection, family) in maintained.items():
        items = assessments[path]
        state, reason = select(repo, items)
        if not items and path in GAPS:
            gap, evidence = GAPS[path]
            reason = f"{gap} {link('Existing evidence', evidence)}."
        digest, size = identity(repo, path)
        counts[collection][state] += 1
        sources = ", ".join(link(item["source_label"], item["source"]) for item in items) or "—"
        rows.append((collection, family, link(path, path), f"`{digest}` · {size:,}", state, sources, reason))
        current = [item for item in items if item.get("campaign") and item["export"]["sha256"] == digest]
        if current:
            latest = max(item["date"] for item in current)
            choices = [item for item in current if item["date"] == latest]
            if len(choices) == 1:
                item = choices[0]
                scores = [axis["score"] if axis["score"] is not None else "—" for axis in item["axes"]]
                target = item.get("target")
                if target and target["family"] != family:
                    raise ValueError(f"Target family differs from the register: {path}")
                status = "At target" if all(isinstance(n, int) and n >= 3 for n in scores) else (
                    "Exemption" if target and target["exemptions"] else "Open")
                target_counts[collection][status] += 1
                label = family if family_exports[(collection, family)] == 1 else f"{family} · {Path(path).stem}"
                if selections[path].shared_owner:
                    label = selections[path].family + " · " + label
                scorecard.append((collection, link(label, path), *scores, status, link("Evidence", item["source"])))


    summary = [
        (collection, *(count[state] for state in STATES), count.total())
        for collection, count in counts.items()
    ]
    families["**Total**"] = len(family_keys)
    total = sum(counts.values(), Counter())
    summary.append(("**Total**", *(total[state] for state in STATES), total.total()))
    if not audit and len(scorecard) == len(maintained) and not total["Unrated"]:
        lines = [
            "# Maintained teaching asset scorecard", "",
            "The total counts each shared family once across collections. Coverage and target counts apply to the selected files. Each file has its own learner task and four scores.",
            "Use the [rubric](../../../docs/guides/asset-quality.md) for the anchors and the "
            "[exemption recheck](../teaching-exemption-recheck.md) for the current before/after decisions and owned follow-ups.", "",
            "Run `python3.12 records/campaigns/teaching-asset-review/coverage.py --audit` for every identity, "
            "historical alternate, evidence gap and register change.", "",
        ]
        if added or removed or moved:
            lines.extend([f"Changes from the pinned register include {len(added)} additions, "
                          f"{len(removed)} replacements or retirements, and {len(moved)} regroupings.", ""])
        target_columns = ("At target", "Exemption", "Open")
        lines += table(("Collection", "Families", *target_columns, *STATES, "Selected files"), (
            (label, families[label], *((sum(target_counts.values(), Counter()) if label == "**Total**" else target_counts[label])[key]
                      for key in target_columns), *values) for label, *values in summary
        ))
        lines += table(("Collection", "Starting file", "Fidelity", "Form", "Readability", "Economy", "Target", "Review"), scorecard)
        return "\n".join(lines)

    lines = [
        "# Exact-file teaching review coverage", "",
        f"Generated by [coverage.py](coverage.py) from the {link('maintained register', REGISTER)}.",
        f"The campaign baseline at `{BASELINE}` has {len(baseline)} starting files in "
        f"{len({collection for collection, _ in baseline.values()})} collections.", "",
        "Full coverage requires an attributable four-axis assessment for the same task and exact file.",
        "Partial coverage has a verified task and some axes with scores. An unrated file may have technical,",
        "visual or teaching evidence that still needs a rubric decision.",
        "Hashes identify the local file bytes or, for an unresolved LFS pointer, its declared object.",
        "Reviewed-view files use the same identity rule. Geometry, image interpretation, anatomy and hosted availability",
        "require separate verification.",
        "When an exact-file campaign task exists, its newest dated assessment supplies the coverage decision.",
        "Multiple campaign tasks on the same date or unresolved earlier score conflicts are flagged.",
        "", "## Register changes", "",
    ]
    if not (added or removed or moved):
        lines += ["No collection, family or path changes from the campaign baseline."]
    for label, paths in (("Added", added), ("Removed", removed), ("Renamed or regrouped", moved)):
        lines.extend(f"- {label} · `{path}`" for path in sorted(paths))
    lines += ["", "## Coverage counts", ""]
    lines += table(("Collection", "Families", *STATES, "Selected files"),
                   ((label, families[label], *rest) for label, *rest in summary))
    lines += ["## Starting files", ""]
    lines += table(("Collection", "Family", "Starting file", "SHA-256 · bytes", "Coverage", "Assessments", "Result or evidence gap"), rows)
    columns = ("File", "Assessment SHA-256", "Source", "Attribution", "Date", "Task", "Fidelity / Form / Readability / Economy", "Binding and coverage")
    lines += ["## Starting-file assessment evidence", ""]
    lines += table(columns, (assessment_row(repo, item) for path in maintained for item in assessments[path]))
    lines += [
        "## Alternate, historical and hosted revisions", "",
        "The bronchial r13 assessment covers the retained hosted first-fork export.",
        "The hosted static heart r01 has a local recorded identity of "
        "`595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f` · 8,951,936 bytes. "
        "The r01–r02 packaging comparison covers a verified repack. The two files need separate teaching assessments.",
        f"See {link('static heart r01 export', 'heart/exterior-presentation-r01/exports/static-opaque-exterior.glb')} and "
        f"{link('r01 to r02 adoption', 'records/work-items/items/AG-GAL-020-adopt-static-heart-repack.md')}.", "",
        "At the campaign baseline, the adrenal r03 overview and Gallery give Form 3. The later r04 close-up review gives the same r03 bytes Form 2 "
        "at closer teaching scale. Both findings retain their own task and evidence. The current r05 has its own assessment.",
        "", "The original adrenal, airspace and nail reviews record the identity of the then-reviewed input. An input",
        "missing from the current checkout remains historical evidence with its binding unavailable for recomputation.",
        "", "Older primary-organ quality-audit plates provide comparison images. No attributable four-axis rating "
        "record with an exact starting-file identity and named task was found beside those plates.", "",
    ]
    lines += table(columns, (assessment_row(repo, item) for path, items in assessments.items() if path not in maintained for item in items))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT, help="Use this repository checkout for the report")
    parser.add_argument("--check", type=Path, help="Check an existing report for drift")
    parser.add_argument("--audit", action="store_true", help="Include all file identities, historical reviews and coverage decisions")
    args = parser.parse_args()
    try:
        output = report(args.repo.resolve(), audit=args.audit)
        if args.check:
            if args.check.read_text() != output:
                parser.exit(1, "Coverage report drift. Regenerate and review the register or assessment changes.\n")
        else:
            sys.stdout.write(output)
    except (ValueError, OSError, KeyError, IndexError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Coverage report failed: {error}\n")


if __name__ == "__main__":
    main()
