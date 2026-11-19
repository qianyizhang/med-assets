"""Build the offline body-systems survey from reviewed copy and render receipts."""
from html import escape
import hashlib
import math
import json
import os
import struct
from urllib.parse import quote

from gallery_plan import (
    ASSEMBLIES, GALLERY as HERE, GALLERY_VIEWS, REPO, SOURCE, TITLES,
    render_plan, study_records,
)

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


def presentation():
    plates = {}
    for job in render_plan():
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


def gallery_plate(entry, title, *, assembly=False):
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
    return (f'<figure class="plate" data-plate="{"assembly" if assembly else "detail"}"><div class="views">{"".join(frames)}</div>'
            f'<figcaption><{heading}>{escape(title)}</{heading}>{frame_info}<ul class="legend" aria-label="Parts and display colors">'
            f'{colors}</ul></figcaption></figure>')


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


def study_section(system, jobs, rev, plates):
    study = system["study"]
    key = system["id"]
    owner = REPO / study["owner"]
    review = REPO / study["review"]
    links = [("Replay and attribution", owner / "README.md"), ("Review and checks", review / "README.md")]
    detail = {}
    for receipt, record, model, prefix in study_records(system):
        links.append((model.name, model))
        blend = model.with_suffix(".blend")
        if blend.is_file():
            links.append((blend.name, blend))
        scene = key + ("-" + prefix.rstrip("/") if prefix else "")
        for view in record["views"]:
            name = prefix + view["id"]
            label = name.replace("/", " · ").replace("-", " ").capitalize()
            detail[name] = gallery_plate(plates[scene, view["id"]], label)
        links.append((f"Original {prefix.rstrip('/') or 'study'} render receipt", receipt))
    featured = "".join(detail.pop(name) for name in study["featured"])
    details = featured + "".join(detail.values())
    state, title, note, *entries = ASSEMBLIES[key]
    combined = []
    for entry in entries:
        scene, name = {
            "urinary-overview": ("urinary", "tract"),
            "nervous-central": ("nervous", "central"),
            "endocrine-overview": ("endocrine", "locator"),
            "lymphatic-overview": ("lymphatic", "overview"),
            "reproductive-female": ("reproductive-female", "context"),
            "reproductive-male": ("reproductive-male", "context"),
        }.get(entry, (entry, "assembly"))
        combined.append(gallery_plate(plates[scene, name], TITLES.get(entry, title), assembly=True))
        links.append((f"{TITLES.get(entry, title)} display receipt", plates[scene, name][0] / "renders.json"))
    parts = "".join(plate(jobs[id], title) for id, title in system["parts"])
    sources = "".join(source_link(label, file, rev) for label, file in system["sources"])
    if study.get("lesson"):
        links.insert(0, ("Run One Breath locally", REPO / study["lesson"]))
    links_html = "".join(f'<a href="{href(path)}">{escape(label)}</a>' for label, path in links)
    status_class = "partial" if state in {"Partial assembly", "Illustrative placement"} else "ready"
    return f"""<section id="{key}" class="system" aria-labelledby="{key}-heading">
    <header><div class="system-title"><h2 id="{key}-heading">{escape(system['name'])}</h2>
    <span class="status {status_class}">{escape(state)}</span></div>
    <p class="function">{escape(system['function'])}</p></header>
    <h3 class="view-heading">System assembly</h3><p class="verdict">{escape(note)}</p>
    <div class="combined-grid">{"".join(combined)}</div>
    <details class="asset-detail"><summary>Asset detail ({len(detail) + len(study['featured'])} pairs)</summary>
    <p class="verdict">{escape(system['verdict'])}</p><div class="part-grid">{details}</div></details>
    {browser_evidence(study, review)}
    <div class="gap"><h3>Audit and limits</h3><p>{escape(' '.join(system['gaps']))}</p></div>
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


def build():
    rev = (SOURCE / "revision.txt").read_text().strip()
    baseline = "2cb53c05577b4cbc2355c4bff293666127d21382"
    systems = load("systems.json")
    jobs = {job["id"]: job for job in load("jobs.json")}
    if len(systems) != 11 or len({system["id"] for system in systems}) != 11:
        raise ValueError("Expected 11 unique systems")
    plates = presentation()
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
    sections = "".join(study_section(system, jobs, baseline, plates) for system in systems)
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
  <p class="lede">See how the parts of eleven body systems fit together. Open Asset detail to follow a route, inspect a junction or compare a pose.</p>
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
  <p>The survey covers the eleven major adult systems, including both reproductive tracts and the special senses within the nervous system. The scope is gross anatomy teaching for one core function per system.</p>
  <ul>
    <li><strong>System assembly.</strong> The overview shows together the structures supported by the stated frame. Native and shared frames preserve source placement and relative scale. Partial assemblies and illustrative placements have separate audit labels.</li>
    <li><strong>Asset detail.</strong> Open for named parts, sections, poses, schematic routes and magnified structures. Read the paired views at the same camera scale. Separate plates are fitted independently.</li>
    <li><strong>Anatomical frame.</strong> Origin, orientation, laterality and units. A pose is an articulated configuration. A view is a camera direction. Axis labels refer to the documented frame or the staged display axes.</li>
    <li><strong>Color and body context.</strong> Named display colors separate nearby anatomical groups. Any silhouette or translucent organ is context. The report keeps exact input identities and links the owner’s anatomy and runtime review.</li>
  </ul>
  <p>Source families include TotalSegmentator, BodyParts3D, Z-Anatomy, HuBMAP/HRA and repository-authored studies. Each source record carries its attribution and reuse terms. Gallery plates use display-only materials. The owning review records retain their original evidence and licenses.</p>
  <p>Taxonomy reference <a href="{REFERENCE}">OpenStax Anatomy and Physiology 2e, §1.2</a>.</p>
</section>
</main>
<footer><div class="wrap">med-assets · teaching asset revision <code>{rev[:12]}</code> · model and screenshot links open this checkout</div></footer>
</body></html>
"""
    temporary = HERE / "index.html.next"
    temporary.write_text(html)
    temporary.replace(HERE / "index.html")


if __name__ == "__main__":
    build()
