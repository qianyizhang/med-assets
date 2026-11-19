"""Build the offline body-systems survey from reviewed copy and render receipts."""
from html import escape
import hashlib
import os
import json
from pathlib import Path
import struct
from urllib.parse import quote

SOURCE = Path(__file__).resolve().parent
REPO = SOURCE.parents[1]
HERE = REPO / ".artifacts/body-systems-survey-2026-11-19"
MEDIA = HERE / "media"
REMOTE = "https://github.com/qianyizhang/med-assets/blob"
REFERENCE = "https://openstax.org/books/anatomy-and-physiology-2e/pages/1-2-structural-organization-of-the-human-body"
CONCEPTS = {
    "skin": ("Layered skin barrier", "Proposed asset with a hair follicle and sweat gland. Separate layer and appendage meshes would support toggling and close inspection."),
    "lymph": ("Lymphatic return junction", "Proposed regional node-to-vein teaching model. The draft explores shape and hierarchy. Anatomical placement and venous entry would need reference-based modelling."),
}
STATUS_TEXT = {"Ready": "Ready for a scoped demo", "Partial": "Partial assembly", "Missing": "Missing core model"}


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


def concept(key):
    if key not in CONCEPTS:
        return ""
    filename = "concept-" + key + ".png"
    if not (MEDIA / filename).is_file():
        return ""
    title, copy = CONCEPTS[key]
    return f"""<figure class="concept">
  <a href="media/{filename}" aria-label="{title}. Open full concept image">{image(filename, title + ', paired oblique and straight-on concept views')}</a>
  <figcaption><p class="eyebrow">ImageGen concept · illustrative</p><h3>{title}</h3><p>{copy}</p><p>Design reference only. A future 3D model requires its own anatomy review.</p></figcaption>
</figure>"""


def href(path):
    if not path.is_file():
        raise ValueError(f"Missing local review file {path}")
    return quote(os.path.relpath(path, HERE))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def study_section(system, jobs, rev):
    study = system["study"]
    owner = REPO / study["owner"]
    review = REPO / study["review"]
    paths = {}
    links = [("Replay and attribution", owner / "README.md"), ("Review and checks", review / "README.md")]
    for receipt in sorted(review.rglob("renders.json")):
        record = json.loads(receipt.read_text())
        model = owner / record["glb"]
        if not model.is_file():
            matches = list(owner.rglob(record["glb"]))
            if len(matches) != 1:
                raise ValueError(f"Cannot resolve {record['glb']} for {receipt}")
            model = matches[0]
        if digest(model) != record["sha256"]:
            raise ValueError(f"Candidate GLB differs from {receipt}")
        if model not in (p for _, p in links):
            links.append((model.name, model))
            blend = model.with_suffix(".blend")
            if blend.is_file():
                links.append((blend.name, blend))
        folder = receipt.parent.relative_to(review)
        for view in record["views"]:
            key = (folder / view["id"]).as_posix()
            label = key.replace("/", " · ").replace("-", " ").capitalize()
            frames = []
            for item in view["images"]:
                image_path = receipt.parent / item["file"]
                if digest(image_path) != item["sha256"]:
                    raise ValueError(f"Screenshot differs from {receipt}: {image_path}")
                url = href(image_path)
                angle = "Isometric" if image_path.stem.endswith("-iso") else "Straight"
                w,h = png_dimensions(image_path)
                frames.append(f'<a class="view" href="{url}"><img src="{url}" alt="{escape(label)} · {angle.lower()}" width="{w}" height="{h}" loading="lazy" decoding="async"><span>{angle}</span></a>')
            if len(frames) != 2 or key in paths:
                raise ValueError(f"Invalid view pair: {key}")
            paths[key] = f'<figure class="plate"><div class="views">{"".join(frames)}</div><figcaption><h3>{escape(label)}</h3></figcaption></figure>'
    featured = "".join(paths.pop(key) for key in study["featured"])
    extras = "".join(paths.values())
    parts = "".join(plate(jobs[id], title) for id, title in system["parts"])
    sources = "".join(source_link(label, file, rev) for label, file in system["sources"])
    key = system["id"]
    if study.get("lesson"):
        links.insert(0, ("Run One Breath locally", REPO / study["lesson"]))
    live = ""
    if study.get("lesson"):
        shots = []
        for filename,label in (("mechanics-rest","Rest"),("mechanics-inspiration","Paused during inspiration")):
            path = review / "browser" / (filename + ".png")
            url = href(path)
            w,h = png_dimensions(path)
            shots.append(f'<a class="view" href="{url}"><img src="{url}" width="{w}" height="{h}" alt="One Breath · {label}" loading="lazy"><span>{label}</span></a>')
        live = '<details><summary>Breathing scene in local Chrome</summary><div class="views">' + "".join(shots) + '</div></details>'
    links_html = "".join(f'<a href="{href(path)}">{escape(label)}</a>' for label,path in links)
    return f"""<section id="{key}" class="system" aria-labelledby="{key}-heading">
    <header><div class="system-title"><h2 id="{key}-heading">{escape(system['name'])}</h2>
    <span class="status ready">Scoped teaching demo</span></div>
    <p class="function">{escape(system['function'])}</p><p class="verdict">{escape(system['verdict'])}</p></header>
    <div class="combined-grid">{featured}</div>
    <div class="source-links downloads">{links_html}</div>
    <details><summary>Junctions, poses and isolated views ({len(paths)} pairs)</summary><div class="part-grid">{extras}</div></details>
    {live}<div class="gap"><h3>Verification and limits</h3><p>{escape(' '.join(system['gaps']))}</p></div>
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
    stats = '<div class="stat ready"><strong>7</strong>New setups</div><div class="stat ready"><strong>4</strong>Refined demos</div><div class="stat ready"><strong>11</strong>Systems reviewed</div>'
    directory = "".join(f'<li><a href="#{s["id"]}">{escape(s["name"])}</a></li>'
                        for s in systems)
    sections = "".join(study_section(system, jobs, baseline) for system in systems)
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
    hero_path = REPO / "reviews/skin/teaching-block-r01/skin-block-iso.png"
    width, height = png_dimensions(hero_path)
    hero = f'<img src="{href(hero_path)}" width="{width}" height="{height}" fetchpriority="high" alt="Layered skin cutaway showing hair follicle, coiled sweat gland and surface opening">'
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
  <p class="lede">Explore eleven teaching setups. Follow a route, isolate a junction or compare a pose. Each study includes its editable source, portable model and screenshots from the exported geometry.</p>
  <div class="stats" aria-label="Survey outcomes">{stats}</div></div>
  <figure class="hero-art">{hero}<figcaption>Skin section · clean import of the new teaching GLB</figcaption></figure>
</section>
<nav id="index" class="directory" aria-labelledby="systems-title"><h2 id="systems-title">Jump to a system</h2><ul>{directory}</ul></nav>
{sections}
<section class="comparison" id="comparison">
  <h2>Compare with the existing galleries</h2>
  <p>Gallery consolidation is pending your review. <a href="baseline.html">Open the original gap survey and concept studies</a>. The two existing surfaces answer different questions. The Model Survey helps you find the asset. Anatomy Verification helps you inspect a study. This report asks whether the pieces can demonstrate a system together.</p>
  <div class="old-grid">{survey}{gallery}</div>
</section>
<section class="method" id="method">
  <h2>What counts as ready</h2>
  <p>The survey covers the eleven major adult systems, including both reproductive tracts and the special senses within the nervous system. The scope is gross anatomy teaching for one core function per system.</p>
  <ul>
    <li><strong>Ready.</strong> Essential 3D parts for the stated demo have a documented common frame or supplied regional assembly, and the relationship is visible in the rendered setup.</li>
    <li><strong>Screenshot standard.</strong> Clean Blender GLB imports, a matched isometric and straight orthographic view at the same scale within each pair, and a matte teaching palette. Straight views use the default source axis or a documented side/reverse axis. Different plates are fitted independently. Original textures and geometry remain in the GLBs.</li>
    <li><strong>Assembly evidence.</strong> Shared-frame inputs keep their native transforms. Regional views and concept images carry their own labels. Source links and per-plate receipts identify the selected GLB bytes.</li>
    <li><strong>Review scope.</strong> An introductory educational coverage review. Motion checks are specific to the designated studies and poses. Each owner records clinical and runtime limits independently.</li>
  </ul>
  <p>Source families include TotalSegmentator, BodyParts3D, Z-Anatomy, HuBMAP/HRA and repository-authored studies. Each source record carries its attribution and reuse terms. Baseline plates use survey display materials. New evidence pairs retain the delivered teaching colors and use matched orthographic cameras.</p>
  <p>Taxonomy reference <a href="{REFERENCE}">OpenStax Anatomy and Physiology 2e, §1.2</a>.</p>
</section>
</main>
<footer><div class="wrap">med-assets · local revision <code>{rev[:12]}</code> · model and screenshot links open this checkout</div></footer>
</body></html>
"""
    (HERE / "index.html").write_text(html)


if __name__ == "__main__":
    build()
