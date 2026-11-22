"""Compose exact-file teaching plates from local replays and retained review views."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


OWNER = Path(__file__).resolve().parent
BATCHES = Path("reviews/teaching-assessments")
DENTAL = Path("reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/media")
URETHRA = Path("reviews/urethra_male/2026-10-26-native-context-r01")
FONT = "experiments/dental-video-treatments/fonts/DejaVuSans.ttf"
PAPER = "#f6f4ef"
INK = "#23282d"
BACKGROUND = "#303437"
WHITE = "#fff7e7"
GOLD = "#ffcf76"


def identity(path):
    data = path.read_bytes()
    return {"sha256": sha256(data).hexdigest(), "bytes": len(data)}


def load(path, expected=None):
    if expected and identity(path) != {key: expected[key] for key in ("sha256", "bytes")}:
        raise ValueError(f"Wrong image bytes: {path}")
    with Image.open(path) as image:
        return image.convert("RGBA")


def text(draw, at, content, size, color=INK):
    draw.text(at, content, font=ImageFont.truetype(FONT, size), fill=color)


def dash(draw, left, right, y, color):
    for x in range(left, right, 18):
        draw.line((x, y, min(x + 10, right), y), fill=color, width=2)


def outline(image, mask, color):
    border = mask.getchannel("A").point(lambda value: 255 if value > 96 else 0)
    border = border.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
    edge = Image.new("RGBA", image.size, color)
    edge.putalpha(border)
    return Image.alpha_composite(image, edge)


class Plate:
    def __init__(self, width, height, title, subtitle):
        self.image = Image.new("RGB", (width, height), PAPER)
        self.draw = ImageDraw.Draw(self.image)
        text(self.draw, (20, 12), title, 32)
        text(self.draw, (20, 57), subtitle, 22)

    def panel(self, image, rect, title, crop=None):
        x, y, width, height = rect
        text(self.draw, (x, y), title, 23)
        y += 32
        source = image if crop is None else image.crop(crop)
        source = source.resize((width, height), Image.Resampling.LANCZOS)
        self.draw.rectangle((x, y, x + width - 1, y + height - 1), fill=BACKGROUND)
        self.image.paste(source, (x, y), source)
        return x, y

    def pin(self, panel, text_pos, tip, label, color=WHITE):
        x, y = panel
        px, py = x + text_pos[0], y + text_pos[1]
        tx, ty = x + tip[0], y + tip[1]
        font = ImageFont.truetype(FONT, 22)
        width = self.draw.textlength(label, font=font)
        # Connect at the nearest edge of the label so the leader never crosses letters.
        stem = px if tx < px else min(tx, px + width)
        self.draw.line((stem, py + 13, tx, ty), fill=color, width=2)
        self.draw.ellipse((tx - 4, ty - 4, tx + 4, ty + 4), fill=color, outline=INK, width=1)
        self.draw.text((px, py), label, fill=color, font=font, stroke_fill=INK, stroke_width=2)

    def foot(self, y, *lines):
        for i, line in enumerate(lines):
            if self.draw.textlength(line, font=ImageFont.truetype(FONT, 21)) > self.image.width - 40:
                raise ValueError(f"Caption exceeds plate width: {line}")
            text(self.draw, (20, y + i * 30), line, 21)

    def save(self, output, name):
        self.image.save(output / (name + ".jpg"), quality=91, optimize=True, subsampling=0)


def lymph(raw, out):
    plate = Plate(1220, 810, "Inside one HRA lymph node", "The capsule and tissues occupy the same source frame. Vessel meshes are hidden in every panel.")
    crop = (0, 166, 720, 501)
    for row, angle in enumerate(("primary", "reverse")):
        capsule = raw(f"lymph-{angle}-capsule.png")
        inside = outline(raw(f"lymph-{angle}-interior.png"), capsule, "#e6e6df")
        y = 102 + row * 318
        view = "Oblique" if row == 0 else "Low oblique"
        plate.panel(capsule, (20, y, 580, 270), f"{view} · capsule", crop)
        pane = plate.panel(inside, (620, y, 580, 270), f"{view} · named tissue meshes", crop)
        if row == 0:
            plate.pin(pane, (408, 45), (302, 130), "Medulla")
        else:
            plate.pin(pane, (70, 10), (170, 100), "Follicles")
            plate.pin(pane, (377, 220), (360, 145), "Paracortex")
    plate.foot(748, "Thin outline is the capsule’s projected edge. Colors distinguish HRA’s named parts.",
               "The vascular network has conflicting source labels. These views show gross regions.")
    plate.save(out, "lymph-node-capsule-and-regions")


def breath(raw, out):
    plate = Plate(1220, 878, "Follow the diaphragm dome down", "The same lateral camera compares expiration and peak inspiration in the authored assembly.")
    crop = (0, 134, 720, 558)
    for column, (frame, phase) in enumerate(((1, "Expiration"), (49, "Peak inspiration"))):
        x = 20 + 600 * column
        context = plate.panel(raw(f"breath-{frame}-context.png"),
                              (x, 103, 580, 342), f"{phase} · frame {frame}", crop)
        dome = raw(f"breath-{frame}-dome.png")
        if column == 0:
            plate.pin(context, (405, 64), (430, 170), "Lung base")
            plate.pin(context, (18, 291), (145, 226), "Liver")
        else:
            plate.pin(context, (395, 61), (432, 202), "Lung base")
            plate.pin(context, (20, 288), (150, 258), "Liver")
        pane = plate.panel(dome, (x, 492, 580, 274), "Diaphragm only", (0, 202, 720, 542))
        reference = raw("breath-1-dome.png").getchannel("A").getbbox()[1]
        y = pane[1] + round((reference - 202) * 274 / 340)
        dash(plate.draw, pane[0] + 45, pane[0] + 535, y - 1, GOLD)
        tip = (288, 83) if column == 0 else (288, 122)
        plate.pin(pane, (374, 191), tip, "Dome crest")
    plate.foot(810, "The dashed line marks the top of the dome at expiration in both lower panels.",
               "Follow the lung base and liver above. The two phases illustrate authored motion.")
    plate.save(out, "breathing-dome-descent")


def heart(raw, info, out):
    plate = Plate(1220, 721, "Watch the left ventricular wall change shape", "The two frames use one fixed camera. The aorta supplies a stationary reference.")
    peak = info["peakFrame"]
    fps = info["fps"]
    for column, frame in enumerate((0, peak)):
        image = raw(f"heart-{frame}-context.png")
        title = "Start · 0.0 s"
        if frame:
            image = outline(image, raw("heart-0-lv.png"), GOLD)
            title = f"Largest sampled wall change · {frame / fps:.3f} s"
        pane = plate.panel(image, (55 + 600 * column, 104, 510, 510), title)
        plate.pin(pane, (342, 79), (274, 155), "Aorta")
        plate.pin(pane, (20, 416), (213, 375), "Ventricular wall")
    distance = info["maxWorldVertexDisplacementMm"]["LV | complete wall"]
    plate.foot(658, "Compare the lower contour with the gold outline of its starting position. Other parts are hidden.",
               f"Largest sampled vertex displacement: {distance:.2f} mm on the wall. The aorta stays fixed.")
    plate.save(out, "cardiac-wall-motion")


def bladder(raw, out):
    plate = Plate(1220, 665, "Find the two ureteral entries at the bladder base",
                  "These rear oblique views share one camera. The base and neck are easier to see with context hidden.")
    crop = (0, 60, 720, 643)
    left = plate.panel(raw("full-back-up-palette.png"), (20, 105, 580, 470), "Full pelvic context", crop)
    right = plate.panel(raw("base-back-up-palette.png"), (620, 105, 580, 470), "Bladder base and neck", crop)
    plate.pin(left, (318, 352), (528, 337), "Ureter in context")
    plate.pin(right, (260, 86), (281, 163), "Bladder base")
    plate.pin(right, (20, 202), (127, 290), "Ureteral entry")
    plate.pin(right, (399, 200), (429, 303), "Ureteral entry")
    plate.pin(right, (328, 426), (276, 431), "Bladder neck")
    plate.foot(618, "The focused view hides the dome, ureters and other pelvic structures. Landmark labels follow the atlas.")
    plate.save(out, "bladder-base-landmarks")


def eye(raw, out):
    plate = Plate(1220, 745, "Cornea, iris opening and lens",
                  "The same three structures are visible in both views. Four ciliary and zonular meshes are hidden.")
    crop = (0, 55, 1000, 943)
    front = plate.panel(raw("anterior-order-three-structures.png"),
                        (20, 103, 580, 515), "Front oblique · through the iris opening", crop)
    profile = plate.panel(raw("corneal-profile-three-structures.png"),
                          (620, 103, 580, 515), "Profile · front to back", crop)
    plate.pin(front, (25, 91), (245, 174), "Cornea")
    plate.pin(front, (390, 369), (355, 350), "Iris")
    plate.pin(front, (22, 336), (280, 260), "Lens seen through pupil")
    plate.pin(profile, (30, 95), (179, 240), "Cornea")
    plate.pin(profile, (386, 137), (317, 181), "Iris")
    plate.pin(profile, (385, 329), (348, 260), "Lens")
    plate.foot(666, "The pupil is the opening in the iris. The pale blue surface seen through it belongs to the lens.",
               "The transparent display shows broad order. The corneal rim and attachments are outside this task.")
    plate.save(out, "eye-anterior-order")


def tooth(out):
    record = {r["file"]: r for r in json.loads((DENTAL.parent / "media-sanitization.json").read_text())}
    def dental(name):
        row = record[name]
        return load(DENTAL / name, {"sha256": row["public_sha256"], "bytes": row["public_bytes"]})
    plate = Plate(1220, 865, "Why this extracted space closes early",
                  "Compare the tooth surface, computed space and three source scan slices near one end.")
    crop = (0, 305, 900, 575)
    plate.panel(dental("display-hard_side.png"), (20, 104, 580, 174), "Tooth exterior", crop)
    plate.panel(dental("display-void_side.png"), (620, 104, 580, 174), "Computed space proxy · isolated", crop)
    scan = dental("terminal-overlays.png")
    text(plate.draw, (20, 320), "Enlarged terminal slices · same crop in all three panels", 26)
    boxes = [
        ((212, 519, 358, 665), "Slice 966 · 140 voxels"),
        ((712, 519, 858, 665), "Slice 969 · 128 voxels"),
        ((1212, 519, 1358, 665), "Slice 972 · 0 voxels"),
    ]
    for i, (box, label) in enumerate(boxes):
        pane = plate.panel(scan, (20 + i * 400, 368, 380, 380), label, box)
        if i == 2:
            plate.pin(pane, (25, 292), (228, 202), "Opening to exterior")
        elif i == 0:
            plate.pin(pane, (23, 287), (220, 201), "Selected interior")
    plate.foot(789, "The per-slice method selects enclosed pixels, shown in orange. The open channel drops out of its selection.",
               "That produces an artificial end in the proxy. The source slice numbers give scan order.")
    plate.save(out, "uff-proxy-terminal-evidence")


def urethra(raw, out):
    source = load(URETHRA / "context-oblique.webp")
    receipt = json.loads((URETHRA / "replay-receipt.json").read_text())
    binding = receipt["packaged_media"]["context-oblique.webp"]["source_png"]
    expected = next(v["decoded_rgba_sha256"] for v in receipt["images"] if v["image"] == binding)
    if sha256(source.tobytes()).hexdigest() != expected:
        raise ValueError("Wrong decoded pixels for the retained oblique urethral view")
    plate = Plate(1220, 617, "Trace the gross urethral course",
                  "Each panel looks along the same source direction at the same scale. Transparency reveals the course.")
    for i, (title, image) in enumerate((
        ("Opaque tissue context", raw("urethra-opaque.png")),
        ("Translucent tissue context", source),
        ("Urethral surface alone", raw("urethra-path.png")),
    )):
        panel = plate.panel(image, (20 + i * 400, 106, 380, 380), title)
        if i == 1:
            plate.pin(panel, (18, 53), (258, 81), "Bladder")
            plate.pin(panel, (15, 123), (274, 153), "Prostate")
            plate.pin(panel, (163, 294), (129, 254), "Spongiosum")
        elif i == 2:
            plate.pin(panel, (185, 240), (118, 247), "Urethral surface")
    plate.foot(534, "Follow the ochre surface from below the bladder, through the prostate region and along the spongiosum.",
               "The modeled ends remain open and unverified. The surface has no demonstrated lumen or patency.")
    plate.save(out, "urethra-course-in-context")


def parathyroids(raw, out):
    plate = Plate(1220, 697, "Locate the four atlas parathyroid targets",
                  "Posterior view. The target-only component and the thyroid companion use the same camera and scale.")
    for i, (name, title) in enumerate((
        ("targets", "Target-only export"),
        ("context", "Separate same-source thyroid companion"),
    )):
        pane = plate.panel(raw(f"parathyroids-{name}.png"), (20 + i * 600, 105, 580, 460), title,
                           (0, 65, 720, 635))
        if i == 0:
            plate.pin(pane, (161, 40), (126, 149), "Superior pair")
            plate.pin(pane, (188, 380), (175, 353), "Inferior pair")
    plate.foot(613, "The four targets retain their source positions. The target-only file has no thyroid surface.",
               "The gray thyroid illustrates one atlas example. Its central projection has no assigned identity here.")
    plate.save(out, "parathyroids-targets-and-companion")


def digestive(raw, out, organ):
    gall = organ == "gallbladder"
    title = ("Gallbladder exterior and wall section" if gall else "Stomach exterior and schematic rugae")
    plate = Plate(1220, 676, title,
                  "A fixed camera compares two separate views. The source exterior can obscure the teaching section.")
    row = "12" if gall else "17"
    crop = (0, 56, 640, 594)
    plate.panel(raw(f"{row}-source.png"), (20, 104, 580, 488), "Source exterior", crop)
    pane = plate.panel(raw(f"{row}-section.png"), (620, 104, 580, 488), "Authored teaching section", crop)
    if gall:
        plate.pin(pane, (180, 47), (122, 151), "Schematic cystic duct")
        plate.pin(pane, (23, 397), (165, 351), "Cut rim")
        plate.foot(632, "The duct is a separate schematic part. The view does not establish a connected lumen.")
    else:
        plate.pin(pane, (349, 71), (332, 206), "Rugae cues")
        plate.pin(pane, (24, 411), (171, 343), "Section edge")
        plate.foot(632, "The independent authored section repeats the rugae pattern. It omits a gastric inlet and outlet.")
    plate.save(out, f"{organ}-exterior-and-section")


def reader(directory, views):
    bindings = {view["file"]: view for view in views}
    return lambda filename: load(directory / filename, bindings[filename])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("render", "eye", "digestive", "bladder", "output"):
        parser.add_argument(f"--{arg}", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    trial = json.loads((args.render / "render.json").read_text())["review"]
    raw = reader(args.render, [v for item in trial.values() for v in item["views"]])
    lymph(raw, args.output)
    breath(raw, args.output)
    heart(raw, trial["heart"], args.output)
    parathyroids(raw, args.output)
    urethra(raw, args.output)
    tooth(args.output)
    eye(reader(args.eye, json.loads((args.eye / "render-manifest.json").read_text())["views"]), args.output)
    bladder(reader(args.bladder, json.loads((args.bladder / "bladder-view.json").read_text())["views"]), args.output)
    digestion = json.loads((args.digestive / "render.json").read_text())["rows"]
    digestive_raw = reader(args.digestive, [v for row in digestion for v in row["views"]])
    for organ in ("gallbladder", "stomach"):
        digestive(digestive_raw, args.output, organ)
    receipt = {p.name: identity(p) for p in sorted(args.output.glob("*.jpg"))}
    (args.output / "plates.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
