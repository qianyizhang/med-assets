"""Build the offline body-systems survey from reviewed copy and render receipts."""
from html import escape
import hashlib
import math
import json
import os
import re
import struct
import sys
from urllib.parse import quote

from gallery_plan import (
    ASSEMBLIES, GALLERY as HERE, GALLERY_VIEWS, REPO, SOURCE, TITLES, WORKSHOP_ASSEMBLIES,
    core_scenes, study_records, workshop_scenes,
)

from viewer_catalog import Catalog, DEFAULT_PORT
from refinements import comparable, definitions, evidence, local_path

MEDIA = HERE / "media"
REMOTE = "https://github.com/qianyizhang/med-assets/blob"
REFERENCE = "https://openstax.org/books/anatomy-and-physiology-2e/pages/1-2-structural-organization-of-the-human-body"

def load(name):
    return json.loads((SOURCE / name).read_text())


def png_dimensions(path):
    with path.open("rb") as source:
        header = source.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Expected PNG: {path}")
    return struct.unpack(">II", header[16:24])


def image(filename, alt, *, hero=False):
    width, height = png_dimensions(MEDIA / filename)
    priority = 'fetchpriority="high"' if hero else 'loading="lazy"'
    return f'<img src="media/{filename}" alt="{escape(alt)}" width="{width}" height="{height}" {priority} decoding="async">'


def local_image(filename, alt, label):
    return (f'<a class="view" href="media/{filename}" aria-label="{escape(alt)}. Open full image">'
            f'{image(filename, alt)}<span>{label}</span></a>')


def plate(job, title, note="", combined=False):
    job_id = job["id"]
    straight = {
        (0, 1, 0): "Reverse-axis orthographic",
        (1, 0, 0): "Side-axis orthographic",
    }.get(tuple(job["front"]), "Straight orthographic")
    iso = local_image(job_id + "-iso.png", f"{title}, isometric orthographic view", "Isometric")
    ortho = local_image(job_id + "-ortho.png", f"{title}, {straight.lower()} view", straight)
    heading = f"<h3>{escape(title)}</h3>" if combined else f"<strong>{escape(title)}</strong>"
    caption = f"<p>{escape(note)}</p>" if note else ""
    return f'<figure class="plate"><div class="views">{iso}{ortho}</div><figcaption>{heading}{caption}</figcaption></figure>'


def source_link(label, path, rev):
    if not (REPO / path).is_file():
        raise ValueError(f"Missing source link: {path}")
    return f'<a href="{REMOTE}/{rev}/{quote(path)}">{escape(label)}</a>'


def href(path):
    if not path.is_file():
        raise ValueError(f"Missing local review file {path}")
    return quote(os.path.relpath(path, HERE))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def presentation(jobs):
    plates = {}
    for job in jobs:
        folder = GALLERY_VIEWS / job["id"]
        path = folder / "renders.json"
        record = json.loads(path.read_text())
        expected = [(source["path"], source["sha256"]) for source in job["inputs"]]
        got = [(source["path"], source["sha256"]) for source in record["inputs"]]
        if got != expected or record["id"] != job["id"]:
            raise ValueError(f"Gallery inputs differ from the plan: {path}")
        for source, sha in expected:
            if digest(REPO / source) != sha:
                raise ValueError(f"Changed gallery source: {source}")
        if [view["id"] for view in record["views"]] != [view["id"] for view in job["views"]]:
            raise ValueError(f"Gallery view list differs from the plan: {path}")
        for expected_view, view in zip(job["views"], record["views"], strict=True):
            if "include" in expected_view and set(view["visible"]) != set(expected_view["include"]):
                raise ValueError(f"Visible geometry differs from the plan: {path}/{view['id']}")
            if "bounds" in expected_view and not all(
                math.isclose(left, right, abs_tol=1e-6)
                for expected_corner, actual_corner in zip(expected_view["bounds"], view["bounds"], strict=True)
                for left, right in zip(expected_corner, actual_corner, strict=True)
            ):
                raise ValueError(f"Geometry or pose bounds differ from the review: {path}/{view['id']}")
            if view["frame"] != expected_view.get("frame", 1):
                raise ValueError(f"Pose frame differs from the plan: {path}/{view['id']}")
            straight = view["images"][1]["direction"]
            if not all(math.isclose(x, y, abs_tol=1e-6)
                       for x, y in zip(straight, expected_view["front"], strict=True)):
                raise ValueError(f"View orientation differs from the plan: {path}/{view['id']}")
            colors = [group["color"] for group in view["legend"]]
            if not colors or len(set(colors)) != len(colors):
                raise ValueError(f"Duplicate or missing legend colors: {path}/{view['id']}")
            for frame in view["images"]:
                if digest(folder / frame["file"]) != frame["sha256"]:
                    raise ValueError(f"Gallery image does not match its receipt: {frame['file']}")
            plates[job["id"], view["id"]] = (folder, view)
    return plates


def workshop_presentation():
    """Activate optional overviews only when both models and their plates verify."""
    if not WORKSHOP_ASSEMBLIES.exists():
        return [], {}, "", None
    try:
        jobs = list(workshop_scenes())
        for job in jobs:
            model = REPO / job["inputs"][0]["path"]
            if not model.with_suffix(".blend").is_file():
                raise FileNotFoundError(f"Missing editable scene for {model.name}")
        plates = presentation(jobs)
        audit = json.loads((WORKSHOP_ASSEMBLIES / "mask-audit.json").read_text())
        colon_gap_copy(audit)
    except (OSError, ValueError, LookupError, TypeError) as exc:
        message = (
            "Same-case s1233 views are unavailable. The gallery shows the Workshop and BodyParts3D "
            "fallbacks. Restore or rebuild the assembly bundle and its renders using the gallery README."
        )
        print(f"{message} ({exc})", file=sys.stderr)
        return [], {}, message, None
    return jobs, plates, "", audit


def colon_gap_copy(audit):
    colon = audit["parts"]["colon"]
    if not isinstance(colon, dict):
        raise ValueError("Missing colon audit record")
    counts = colon.get("componentVoxelCounts6")
    gap = colon.get("largestComponentsMinimumVoxelCentreMm")
    if counts is None and gap is None:
        return "The baseline mask review records a 24.6 mm gap between the two main colon components."
    if (not isinstance(counts, list) or len(counts) < 2
            or any(type(count) is not int or count <= 0 for count in counts)
            or counts != sorted(counts, reverse=True)
            or len(counts) != colon["components6"] or sum(counts) != colon["voxels"]
            or type(gap) not in (int, float) or not math.isfinite(gap) or gap < 0):
        raise ValueError("Invalid colon component measurements")
    sizes = ", ".join(f"{count:,}" for count in counts)
    return f"The source colon has components of {sizes} voxels. The largest pair is {gap:.3f} mm apart."


def gallery_plate(entry, title, *, assembly=False, viewer_url=None):
    folder, view = entry
    frames = []
    for item in view["images"]:
        path = folder / item["file"]
        url = href(path)
        if path.stem.endswith("-iso"):
            angle = "Isometric"
        else:
            direction = tuple(round(v, 4) for v in item["direction"])
            axes = {
                (0, -1, 0): ("Anterior", "−Y orthographic"),
                (0, 1, 0): ("Posterior", "+Y orthographic"),
                (1, 0, 0): ("Left lateral", "+X orthographic"),
                (-1, 0, 0): ("Right lateral", "−X orthographic"),
            }
            angle = axes.get(direction, ("Straight orthographic",) * 2)[0 if assembly else 1]
        w, h = png_dimensions(path)
        alt = escape(f"{title} · {angle}")
        frames.append(f'<a class="view" href="{url}"><img src="{url}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async"><span>{angle}</span></a>')
    if len(frames) != 2:
        raise ValueError(f"Expected two images for {folder}/{view['id']}")
    colors = "".join(f'<li><span aria-hidden="true" style="--swatch:{group["color"]}"></span>'
                     f'{escape(group["label"])}</li>' for group in view["legend"])
    width = view["orthographicScale"] * 100
    frame_info = f'<p class="picture-width">Matched camera width · {width:.1f} cm in model units</p>' if assembly else ""
    heading = "h4" if assembly else "strong"
    action = viewer_link(viewer_url, "Open in 3D") if viewer_url else ""
    return (f'<figure class="plate" data-plate="{"assembly" if assembly else "detail"}"><div class="views">{"".join(frames)}</div>'
            f'<figcaption><{heading}>{escape(title)}</{heading}>{frame_info}<ul class="legend" aria-label="Parts and display colors">'
            f'{colors}</ul>{action}</figcaption></figure>')


def browser_evidence(study, review):
    if not study.get("lesson"):
        return ""
    shots = []
    for filename, label in (("mechanics-rest", "Rest"), ("mechanics-inspiration", "Paused during inspiration")):
        path = review / "browser" / (filename + ".png")
        url = href(path)
        w, h = png_dimensions(path)
        shots.append(f'<a class="view" href="{url}"><img src="{url}" width="{w}" height="{h}" alt="One Breath · {label}" loading="lazy"><span>{label}</span></a>')
    return '<details><summary>Breathing scene in local Chrome</summary><div class="views">' + "".join(shots) + "</div></details>"


WORKSHOP_VIEWS = {
    "cardiovascular": (
        "Same-case heart and great vessels", "Vessels isolated",
        "The heart, aorta, pulmonary venous mask and both venae cavae retain their s1233 positions. "
        "The schematic supplies pulmonary arterial outflow, chamber and valve interiors, and the distal circuits.",
        "The source vessel masks approach or overlap the heart label. The labels identify the outer heart "
        "boundary and leave the internal chamber connections unresolved.",
    ),
    "digestive": (
        "Same-case esophagus through colon", "Digestive tract isolated",
        "The esophagus, stomach, duodenum, small bowel, colon and accessory organs share the s1233 scan frame. "
        "The schematic supplies the mouth, terminal outlet and accessory duct entry.",
        "Consecutive label boundaries approach or overlap within 1.5 mm. "
        "A verified ileocecal landmark and continuous lumen remain open.",
    ),
}


def viewer_link(url, label):
    return f'<a class="viewer-action" href="{escape(url)}">{escape(label)}</a>'


def refinement_figure(entry, heading, title, locators=()):
    folder, view, _ = entry
    images = []
    for frame, angle in zip(view["images"], ("Isometric", "Orthographic"), strict=True):
        path = folder / frame["file"]
        url = href(path)
        w, h = png_dimensions(path)
        alt = escape(f"{title}, {heading.lower()}, {angle.lower()}")
        link = (f'<a class="view" href="{url}"><img src="{url}" alt="{alt}" '
                f'width="{w}" height="{h}" loading="lazy" decoding="async"><span>{angle}</span></a>')
        if angle == "Orthographic" and locators:
            markers = "".join(
                f'<a class="body-marker" href="#refinement-{escape(marker["target"])}" '
                f'style="--marker-x:{marker["x"]}%;--marker-y:{marker["y"]}%">{escape(marker["title"])}</a>'
                for marker in locators
            )
            link = f'<div class="body-locators">{link}{markers}</div>'
        images.append(link)
    legend = ""
    if heading == "Updated" and view.get("legend"):
        keys = "".join(f'<li><span aria-hidden="true" style="--swatch:{group["color"]}"></span>'
                       f'{escape(group["label"])}</li>' for group in view["legend"])
        legend = f'<ul class="legend" aria-label="Updated display colors">{keys}</ul>'
    return (f'<figure class="refinement-frame"><figcaption>{escape(heading)}</figcaption>'
            f'<div class="views">{"".join(images)}</div>{legend}</figure>')


def refinement_panels(plates, catalog):
    ready = []
    for item in definitions():
        note = item["note"]
        try:
            before, after = (evidence(item[label], plates) for label in ("before", "after"))
            if item["matched"]:
                sizes = [[png_dimensions(entry[0] / frame["file"]) for frame in entry[1]["images"]]
                         for entry in (before, after)]
                if sizes[0] != sizes[1] or not comparable(before, after):
                    raise ValueError("Camera position, orientation, scale or image dimensions differ")
            if item.get("colonAudit"):
                folder = local_path(after[2][0]["path"]).parent
                list(workshop_scenes(folder))
                note += " " + colon_gap_copy(json.loads((folder / "mask-audit.json").read_text()))
        except (OSError, ValueError, LookupError, TypeError) as exc:
            if any(local_path(item[label]["receipt"]).exists()
                   for label in ("before", "after") if "receipt" in item[label]):
                print(f"Skipping refinement {item['id']}: {exc}", file=sys.stderr)
            continue
        related = []
        for detail in item.get("details", ()):
            try:
                folder, view, _ = evidence({**item["after"], **detail}, plates)
                related.append((detail["title"], folder / view["images"][0]["file"]))
            except (OSError, ValueError, LookupError, TypeError) as exc:
                print(f"Skipping refinement detail {item['id']}/{detail['view']}: {exc}", file=sys.stderr)
        ready.append((item, before, after, note, related))

    panels = {}
    ready_ids = {item["id"] for item, *_ in ready}
    for item, before, after, note, related in ready:
        key, title = item["system"], item["title"]
        folder, view, inputs = after
        links = []
        if item.get("inspect3d"):
            if len(inputs) != 1:
                raise ValueError(f"Refinement {item['id']} requires a single model")
            display_groups = item.get("groups", [])
            if display_groups:
                groups = display_groups + list(catalog.plans[item["scene"]]["inputs"][0]["groups"])
            else:
                grouped_parts = [
                    {**group, "color": "#7a7971", "alpha": 1} for group in item.get("groupParts", ())
                ]
                groups = grouped_parts + [
                    dict(label=name, pattern="^" + re.escape(name) + "$", color="#7a7971", alpha=1)
                    for name in view["visible"]
                ]
            styles = {**inputs[0], "label": "Other anatomy", "color": "#7a7971",
                      "alpha": 1, "groups": groups, "sourceMaterials": not display_groups}
            url = catalog.add(f"refinement/{item['id']}", folder, view, title, key, [styles], view["visible"])
            links.append(viewer_link(url, "Open updated view in 3D"))
            model = local_path(inputs[0]["path"])
            links.append(f'<a href="{href(model)}">Download GLB</a>')
            blend = model.with_suffix(".blend")
            if blend.is_file():
                links.append(f'<a href="{href(blend)}">Editable Blender scene</a>')
        for label, entry in (("Original render receipt", before), ("Updated render receipt", after)):
            links.append(f'<a href="{href(entry[0] / "renders.json")}">{label}</a>')
        if "review" in item:
            links.append(f'<a href="{href(local_path(item["review"]))}">Build and checks</a>')
        for label, path in related:
            links.append(f'<a href="{href(path)}">{escape(label)}</a>')

        frames = refinement_figure(before, item.get("beforeLabel", "Original"), title)
        locators = [marker for marker in item.get("locators", ()) if marker["target"] in ready_ids]
        frames += refinement_figure(after, item.get("afterLabel", "Updated"), title, locators)
        basis = "Matched camera and scale." if item["matched"] else "Separately framed views."
        panel = (f'<article class="refinement" id="refinement-{escape(item["id"])}"><h4>{escape(title)}</h4>'
                 f'<p>{escape(note)} {basis}</p><div class="refinement-grid">{frames}</div>'
                 f'<div class="source-links">{"".join(links)}</div></article>')
        panels.setdefault(key, []).append(panel)
    return {key: '<div class="refinements"><h3 class="view-heading">Before and after</h3>'
                 + "".join(cards) + "</div>" for key, cards in panels.items()}


def study_section(system, jobs, rev, plates, catalog, workshop_audit, workshop_warning, refinement):
    study = system["study"]
    key = system["id"]
    owner = REPO / study["owner"]
    review = REPO / study["review"]
    links = [("Replay and attribution", owner / "README.md"), ("Review and checks", review / "README.md")]
    detail = {}
    model_actions = []
    for receipt, record, model, prefix in study_records(system):
        links.append((model.name, model))
        blend = model.with_suffix(".blend")
        if blend.is_file():
            links.append((blend.name, blend))
        scene = key + ("-" + prefix.rstrip("/") if prefix else "")
        view = record["views"][0]
        folder, display = plates[scene, view["id"]]
        model_actions.append(viewer_link(
            catalog.register(folder, display, model.stem.replace("-", " ").capitalize(), key, whole=True),
            f"Open {model.stem} in 3D",
        ))
        for view in record["views"]:
            name = prefix + view["id"]
            label = name.replace("/", " · ").replace("-", " ").capitalize()
            detail[name] = gallery_plate(plates[scene, view["id"]], label)
        links.append((f"Original {prefix.rstrip('/') or 'study'} render receipt", receipt))
    featured = "".join(detail.pop(name) for name in study["featured"])
    state, title, note, *entries = ASSEMBLIES[key]
    combined = []
    audit = " ".join(system["gaps"])
    workshop = key + "-s1233"
    if (workshop, "assembly") in plates:
        title, route, note, limits = WORKSHOP_VIEWS[key]
        entries = []
        entry = plates[workshop, "assembly"]
        combined.append(gallery_plate(entry, title, assembly=True,
                                      viewer_url=catalog.register(*entry, title, key)))
        detail["workshop-route"] = gallery_plate(plates[workshop, "route"], route)
        links.extend([
            ("Same-case GLB", WORKSHOP_ASSEMBLIES / f"{key}.glb"),
            ("Same-case Blender scene", WORKSHOP_ASSEMBLIES / f"{key}.blend"),
            ("Mask and junction audit", WORKSHOP_ASSEMBLIES / "mask-audit.json"),
            ("Same-case render receipt", GALLERY_VIEWS / workshop / "renders.json"),
        ])
        audit = limits + " " + audit
        if key == "digestive":
            audit = colon_gap_copy(workshop_audit) + " " + audit
    if workshop_warning and key in WORKSHOP_VIEWS:
        audit = workshop_warning + " " + audit
    details = featured + "".join(detail.values())
    for entry in entries:
        scene, name = {
            "urinary-overview": ("urinary", "tract"),
            "nervous-central": ("nervous", "central"),
            "endocrine-overview": ("endocrine", "locator"),
            "lymphatic-overview": ("lymphatic", "overview"),
            "reproductive-female": ("reproductive-female", "context"),
            "reproductive-male": ("reproductive-male", "context"),
        }.get(entry, (entry, "assembly"))
        entry_title = TITLES.get(entry, title)
        display = plates[scene, name]
        combined.append(gallery_plate(display, entry_title, assembly=True,
                                      viewer_url=catalog.register(*display, entry_title, key)))
        links.append((f"{TITLES.get(entry, title)} display receipt", plates[scene, name][0] / "renders.json"))
    parts = "".join(plate(jobs[id], title) for id, title in system["parts"])
    sources = "".join(source_link(label, file, rev) for label, file in system["sources"])
    if study.get("lesson"):
        links.insert(0, ("Run One Breath locally", REPO / study["lesson"]))
    links_html = "".join(f'<a href="{href(path)}">{escape(label)}</a>' for label, path in links)
    links_html += "".join(model_actions)
    status_class = "partial" if state in {"Partial assembly", "Illustrative placement"} else "ready"
    return f"""<section id="{key}" class="system" aria-labelledby="{key}-heading">
    <header><div class="system-title"><h2 id="{key}-heading">{escape(system['name'])}</h2>
    <span class="status {status_class}">{escape(state)}</span></div>
    <p class="function">{escape(system['function'])}</p></header>
    <h3 class="view-heading">System assembly</h3><p class="verdict">{escape(note)}</p>
    <div class="combined-grid">{"".join(combined)}</div>
    {refinement}
    <details class="asset-detail"><summary>Asset detail ({len(detail) + len(study['featured'])} pairs)</summary>
    <p class="verdict">{escape(system['verdict'])}</p><div class="part-grid">{details}</div></details>
    {browser_evidence(study, review)}
    <div class="gap"><h3>Audit and limits</h3><p>{escape(audit)}</p></div>
    <details><summary>Models, review and attribution</summary><div class="source-links downloads">{links_html}</div></details>
    <details><summary>Source assets and baseline screenshots</summary><div class="part-grid">{parts}</div><div class="source-links">{sources}</div></details>
    </section>"""


def comparison_card(title, href, purpose, overlap, screenshot, fallback):
    image_html = ""
    if (MEDIA / screenshot).is_file():
        image_html = (f'<a href="media/{screenshot}" aria-label="Open full {title} screenshot">'
                      f'{image(screenshot, f"{title}, {fallback.lower()}")}</a>')
    return f"""<article class="old-card">
    {image_html}
    <div class="card-body">
      <p class="image-note">{fallback}</p>
      <h3>{title}</h3>
      <p>{purpose}</p>
      <p>{overlap}</p>
      <a href="{href}">Open {title}</a>
    </div>
  </article>"""


def build(viewer_port=DEFAULT_PORT):
    rev = (SOURCE / "revision.txt").read_text().strip()
    baseline = "2cb53c05577b4cbc2355c4bff293666127d21382"
    systems = load("systems.json")
    jobs = {job["id"]: job for job in load("jobs.json")}
    if len(systems) != 11 or len({system["id"] for system in systems}) != 11:
        raise ValueError("Expected 11 unique systems")
    core = list(core_scenes())
    plates = presentation(core)
    workshop, optional_plates, warning, mask_audit = workshop_presentation()
    plates.update(optional_plates)
    catalog = Catalog(viewer_port, core + workshop)
    refinements = refinement_panels(plates, catalog)
    comparison_hint = (" Look for <strong>Before and after</strong> within each refined system."
                       if refinements else "")
    states = [ASSEMBLIES[system["id"]][0] for system in systems]
    native = sum(state.startswith(("Native", "Shared")) for state in states)
    partial = sum(state in {"Partial assembly", "Illustrative placement"} for state in states)
    locator = states.count("Body locator")
    stats = (
        f'<div class="stat ready"><strong>{native}</strong>Native or shared-frame assemblies</div>'
        f'<div class="stat partial"><strong>{partial}</strong>Partial or illustrative placements</div>'
        f'<div class="stat"><strong>{locator}</strong>Body locator with local details</div>'
    )
    directory = "".join(f'<li><a href="#{s["id"]}">{escape(s["name"])}</a></li>'
                        for s in systems)
    sections = "".join(study_section(system, jobs, baseline, plates, catalog, mask_audit, warning,
                                     refinements.get(system["id"], ""))
                       for system in systems)
    survey = comparison_card("Medical Model Survey", "https://med-assets-model-survey.landy123007.chatgpt.site/",
        "Browse individual assets, variants, review states, files and related products across the collection.",
        "It already owns the asset inventory. This body-systems report adds the minimum teaching setup, the assembly evidence, and the missing joins.",
        "existing-survey.png", "Archived offline survey · 6 November 2026" if (MEDIA / "existing-survey.png").exists() else "Documented inventory snapshot")
    gallery = comparison_card("Anatomy Verification", "https://anatomy-verification.landy123007.chatgpt.site/review/",
        "Inspect a specific candidate, compare revisions, and check its review evidence.",
        "Its focused comparisons are useful evidence behind this report. For example, the knee study shows finer visual differences than the body-system plate.",
        "existing-gallery.png" if (MEDIA / "existing-gallery.png").exists() else "gallery-knee.png",
        "Live review gallery · 19 November 2026" if (MEDIA / "existing-gallery.png").exists() else "Retained knee comparison from the gallery integration")
    stylesheet = (SOURCE / "style.css").read_text()
    hero_path = GALLERY_VIEWS / "thorax/assembly-iso.png"
    width, height = png_dimensions(hero_path)
    hero = f'<img src="{href(hero_path)}" width="{width}" height="{height}" fetchpriority="high" alt="Translucent lung lobes around the lobar bronchi, above the diaphragm">'
    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Body Systems · med-assets survey</title><style>{stylesheet}</style></head>
<body>
<a class="skip" href="#main">Skip to survey</a>
<header class="masthead"><div class="wrap"><span class="brand">med-assets</span>
<nav aria-label="Report"><a href="#index">Systems</a><a href="#comparison">Existing galleries</a><a href="#method">Method</a></nav></div></header>
<main id="main" class="wrap">
<section class="hero" aria-labelledby="page-title">
  <div><p class="eyebrow">Repository survey · 19 November 2026</p>
  <h1 id="page-title">Body systems in 3D</h1>
  <p class="lede">See how the parts of eleven body systems fit together. Use <strong>Open in 3D</strong> to rotate a local assembly and isolate structures.{comparison_hint}</p>
  <div class="stats" aria-label="Survey outcomes">{stats}</div></div>
  <figure class="hero-art">{hero}<figcaption>Respiratory system · shared thoracic frame</figcaption></figure>
</section>
<nav id="index" class="directory" aria-labelledby="systems-title"><h2 id="systems-title">Jump to a system</h2><ul>{directory}</ul></nav>
{sections}
<section class="comparison" id="comparison">
  <h2>Compare with the existing galleries</h2>
  <p>Gallery consolidation is pending your review. <a href="baseline.html">Open the original gap survey and concept studies</a>. The two existing surfaces answer different questions. The Model Survey helps you find the asset. Anatomy Verification helps you inspect a study. This report asks whether the pieces can demonstrate a system together.</p>
  <div class="old-grid">{survey}{gallery}</div>
</section>
<section class="method" id="method">
  <h2>How to read the gallery</h2>
  <p><strong>Local 3D.</strong> Start the gallery server with <code>python3.12 sites/body-systems-survey/serve.py</code>. The screenshots also open directly from disk.</p>
  <p>The survey covers the eleven major adult systems, including both reproductive tracts and the special senses within the nervous system. The scope is gross anatomy teaching for one core function per system.</p>
  <ul>
    <li><strong>System assembly.</strong> The overview shows together the structures supported by the stated frame. Native and shared frames preserve source placement and relative scale. Partial assemblies and illustrative placements have separate audit labels.</li>
    <li><strong>Asset detail.</strong> Open for named parts, sections, poses, schematic routes and magnified structures. Read the paired views at the same camera scale. Separate plates are fitted independently.</li>
    <li><strong>Before and after.</strong> Compare the original with the updated view. Matched pairs share camera and scale. Captions identify independently framed assets, authored geometry and display changes.</li>
    <li><strong>Anatomical frame.</strong> Origin, orientation, laterality and units. A pose is an articulated configuration. A view is a camera direction. Axis labels refer to the documented frame or the staged display axes.</li>
    <li><strong>Color and body context.</strong> Named display colors separate nearby anatomical groups. Any silhouette or translucent organ is context. The report keeps exact input identities and links the owner’s anatomy and runtime review.</li>
  </ul>
  <p>Source families include TotalSegmentator, BodyParts3D, Z-Anatomy, HuBMAP/HRA and repository-authored studies. Each source record carries its attribution and reuse terms. Updated assets use their GLB materials in 3D. Regional presentations apply the display palette. The owning review records retain their evidence and licenses.</p>
  <p>Taxonomy reference <a href="{REFERENCE}">OpenStax Anatomy and Physiology 2e, §1.2</a>.</p>
</section>
</main>
<footer><div class="wrap">med-assets · original teaching revision <code>{rev[:12]}</code> · model and screenshot links open this checkout</div></footer>
</body></html>
"""
    temporary = HERE / "index.html.next"
    temporary.write_text(html)
    temporary.replace(HERE / "index.html")
    return catalog.data()


if __name__ == "__main__":
    build()
