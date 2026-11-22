"""Make review plates from identity-checked clean-import renders."""

import argparse
import json
from pathlib import Path
import runpy

from PIL import Image

HERE = Path(__file__).resolve().parent
SHARED = runpy.run_path(str(HERE.parent / "refinement-risk/plates.py"))
Plate = SHARED["Plate"]


def frames(folder, receipt="receipt.json"):
    record = json.loads((folder / receipt).read_text())
    views = {v["file"]: v for v in record["views"]}

    def load(stem):
        file = stem + ".png"
        return SHARED["load"](folder / file, views[file])

    return load, views


def save(plate, output, family):
    plate.image.save(output / (family + ".webp"), quality=92, method=6)


def parathyroid(folder, output):
    raw, views = frames(folder)
    plate = Plate(1200, 880, "Find the four parathyroid targets",
                  "Matched posterior and side views of the target component and the same-source thyroid companion.")
    cell = 370
    crop = (0, 83, 640, 548)
    for col, (angle, title) in enumerate((("posterior", "Posterior"),
                                         ("patient-right", "From the patient's right"),
                                         ("patient-left", "From the patient's left"))):
        x = 20 + col * 393
        for row, state in enumerate(("control", "candidate")):
            y = 140 + row * 313
            stem = f"{state}-{angle}"
            pane = plate.panel(raw(stem), (x, y, cell, 269), title if row == 0 else "", crop)
            if angle == "posterior":
                for name, (px, py) in views[stem + ".png"]["targetProjection"].items():
                    tip = (round(px * cell), round(((1 - py) * 640 - crop[1]) * 269 / (crop[3] - crop[1])))
                    left = ".l." in name
                    upper = name.startswith("Superior")
                    label = ("L" if left else "R") + (" upper" if upper else " lower")
                    plate.pin(pane, (14 if left else 262, 17 if upper else 228), tip, label)
    SHARED["text"](plate.draw, (20, 100), "Original · isolated gland component", 21)
    SHARED["text"](plate.draw, (20, 439), "Updated · same-source thyroid and the original four glands", 21)
    plate.foot(775, "In the posterior view the left and right sides retain their atlas positions in both rows.",
               "One atlas example. The thyroid’s central projection has an unassigned identity.")
    save(plate, output, "parathyroid")


def breathing(folder, output):
    raw, _ = frames(folder)
    plate = Plate(1200, 835, "Compare expiration and peak inspiration",
                  "Reimported phase views from the selected five lobes, diaphragm and liver.")
    crop = (0, 122, 640, 495)
    target = 374
    height = 218
    for i, (frame, title) in enumerate(((1, "Expiration · frame 1"), (49, "Peak inspiration · frame 49"))):
        x = 22 + i * 391
        pane = plate.panel(raw(f"candidate-{frame}-phase"), (x, 108, target, height), title, crop)
        if i == 0:
            plate.pin(pane, (235, 55), (272, 104), "Lung base")
            plate.pin(pane, (16, 176), (103, 146), "Liver")
        dome = raw(f"candidate-{frame}-isolated")
        pane = plate.panel(dome, (x, 370, target, height), "Diaphragm only", crop)
        alpha = dome.getchannel("A")
        crest = alpha.getbbox()[1]
        guide = raw("candidate-1-isolated").getchannel("A").getbbox()[1]
        h = lambda v: round((v - crop[1]) * height / (crop[3] - crop[1]))
        SHARED["dash"](plate.draw, pane[0] + 25, pane[0] + target - 25, pane[1] + h(guide), SHARED["GOLD"])
        crest_x = next(x for x in range(640) if alpha.getpixel((x, crest)) > 0)
        plate.pin(pane, (215, 160), (round(crest_x * target / 640), h(crest)), "Dome crest")
    for i, (frame, title) in enumerate(((1, "Original · frame 1"), (49, "Original · frame 49"))):
        plate.panel(raw(f"control-{frame}-phase"), (804, 108 + i * 262, target, height), title, crop)
    plate.foot(676, "The same camera shows the dome flatten and descend between frames 1 and 49.",
               "The superior dome bound falls 20.90 mm, the left lower-lobe base 17.60 mm and the liver 7.98 mm.",
               "The view illustrates authored motion. Projected overlap cannot establish attachment or physiology.")
    save(plate, output, "breath")


def cardiac(folder, output):
    raw, _ = frames(folder)
    plate = Plate(1100, 789, "Track ventricular contour change",
                  "Match the aorta while the left ventricular wall moves through the authored cycle.")
    crop = (100, 0, 540, 640)
    for i, (side, phase, label) in enumerate((
            ("control", 0, "Original · reference"),
            ("control", 8, "Original · peak sample"),
            ("candidate", 0, "Updated · reference"),
            ("candidate", 8, "Updated · peak sample"))):
        x = 20 + i * 270
        panel = raw(f"{side}-{phase}-phase")
        if side == "candidate" and phase:
            panel = SHARED["outline"](panel, raw("candidate-0-phase"), "#ddd6b4")
        plate.panel(panel, (x, 108, 250, 364), label, crop)
    plate.foot(539, "Brown aorta · fixed reference. Gold ventricular wall · 5.05 mm maximum sampled displacement.",
               "The largest 24 fps sample falls at 0.333 s. The pale outline shows the reference silhouette.",
               "The full atlas supplies whole-heart orientation. The clip shows authored contour motion.")
    save(plate, output, "heart")


def digestive(folder, output, family):
    raw, _ = frames(folder)
    stomach = family == "stomach"
    title = "Compare the stomach exterior and rugae cues" if stomach else "Compare the gallbladder exterior and wall section"
    subtitle = "Matched cameras and scale. The lower-right panel enlarges the section."
    plate = Plate(1200, 1004, title, subtitle)
    side = "control"
    crop = (0, 0, 640, 640)
    entries = [
        ("control-front-all", "Diagnostic · all parts"),
        (f"{side}-front-exterior", "Current · source exterior"),
        (f"{side}-front-section", "Current · authored section"),
        (f"{side}-oblique-section", "Current · oblique section"),
        (f"{side}-oblique-exterior", "Current · oblique exterior"),
        (f"{side}-front-section", "Current · section detail"),
    ]
    for i, (stem, label) in enumerate(entries):
        plate.panel(raw(stem), (20 + (i % 3) * 393, 106 + (i // 3) * 410, 375, 375), label, (100, 100, 540, 540) if i == 5 else crop)
    notes = ("The section contains eleven authored folds and its own backing. Source and section are separate options.",
             "Source surface undulations remain visible. The model does not establish gastric inlet or outlet anatomy.") if stomach else (
             "The rim marks the authored cut face. The ochre tube is the separately modeled cystic-duct cue.",
             "Source depressions remain visible on the surface. The duct cue does not establish lumen continuity.")
    plate.foot(933, *notes)
    save(plate, output, family)


def stomach_trial(folder, output):
    raw, _ = frames(folder)
    plate = Plate(1140, 630, "Smaller stomach section trial", "Matched oblique views of the authored section with its eleven rugae cues.")
    image_crop = (5, 65, 635, 590)
    for i, (side, title) in enumerate((("control", "Original · 60,456 triangles total"), ("candidate", "Trial · 58,748 triangles total"))):
        plate.panel(raw(f"{side}-oblique-section"), (20 + i * 554, 111, 535, 446), title, image_crop)
    plate.foot(596, "The trial saved 37,216 bytes. The original has the established exterior and section experience.")
    save(plate, output, "stomach-trial")


def bladder(folder, output):
    raw, _ = frames(folder)
    plate = Plate(1200, 820, "Find the base, neck and paired ureteral entries",
                  "The eight retained atlas parts keep their original positions and their own selections.")
    xsteps = (20, 414, 808)
    images = [
        ("control-rear-context", "Original · pelvic context"),
        ("candidate-rear-context", "Updated · bladder and ureters"),
        ("candidate-rear-ureters", "Updated · dome hidden"),
        ("control-reverse-base", "Original · base focus"),
        ("candidate-reverse-ureters", "Updated · opposite oblique"),
        ("candidate-reverse-base", "Updated · base focus"),
    ]
    crop = (0, 57, 640, 573)
    for i, (stem, title) in enumerate(images):
        col, row = i % 3, i // 3
        pane = plate.panel(raw(stem), (xsteps[col], 109 + row * 340, 370, 298), title, crop)
        if i == 2:
            plate.pin(pane, (8, 158), (85, 190), "Entry")
            plate.pin(pane, (278, 143), (273, 197), "Entry")
            plate.pin(pane, (244, 254), (163, 263), "Neck")
        if i == 5:
            plate.pin(pane, (52, 226), (168, 183), "Base")
    plate.foot(785, "The atlas’s thin patch edge and ridge remain. The ureters extend beyond this base-focused crop.")
    save(plate, output, "bladder")


def eye(folder, output):
    raw, _ = frames(folder, "reimport-render-receipt.json")
    plate = Plate(1190, 950, "Find the cornea, iris opening and lens",
                  "The teaching edition carries the three retained source meshes and their original materials.")
    for col, (side, title) in enumerate((("baseline", "Original · diagnostic export"), ("candidate", "Updated · three-structure export"))):
        x = 20 + col * 586
        for row, (view, label, crop) in enumerate((("context", title, (115, 0, 885, 1000)),
                                                     ("detail", "Matched superior close-up", (0, 200, 1000, 940)))):
            pane = plate.panel(raw(f"{side}-{view}"), (x, 107 + row * 391, 568, 350), label,
                               (0, 120, 1000, 880) if view == "context" else crop)
            if side == "candidate" and row == 0:
                plate.pin(pane, (40, 64), (236, 119), "Cornea")
                plate.pin(pane, (394, 100), (313, 169), "Iris")
                plate.pin(pane, (57, 247), (269, 182), "Lens through pupil")
    plate.foot(906, "The thin faceted boundary is inherited from the source. The pupil is the opening in the iris.")
    save(plate, output, "eye")


def lymph(folder, output):
    raw, views = frames(folder)
    test = "candidate-front-medulla.png" in views
    plate = Plate(1180, 760, "Trace the capsule and locate the three tissue regions",
                  "Compare the intact projected shape, named tissue regions and neutral medulla close-up.")
    crop = (0, 105, 640, 542)
    for row, angle in enumerate(("front", "oblique")):
        side = "candidate" if test and row == 1 else "control"
        for col, (mode, title) in enumerate((("capsule", "Capsule"), ("interior", "Named tissue regions"), ("medulla", "Neutral medulla"))):
            x, y = 20 + col * 388, 106 + row * 288
            image = raw(f"{side}-{angle}-{mode}")
            if mode == "interior":
                image = SHARED["outline"](image, raw(f"{side}-{angle}-capsule"), "#e6e6df")
            plate.panel(image, (x, y, 368, 251), title, crop)
    plate.foot(690, "Ochre follicles, purple paracortex, blue medulla. The outline is the projected capsule edge.",
               "The capsule aperture and medullary clefts remain in the source. Their exact identities are unassigned.")
    save(plate, output, "lymph")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True)
    for name, function in (("parathyroid", parathyroid), ("breath", breathing), ("heart", cardiac),
                           ("bladder", bladder), ("eye", eye), ("lymph", lymph)):
        suffix = {"parathyroid": "-verified", "lymph": "-fine"}.get(name, "-qa")
        function(args.input / (name + suffix), args.output)
    for name in ("gallbladder", "stomach"):
        digestive(args.input / (name + "-qa"), args.output, name)
    stomach_trial(args.input / "stomach-qa", args.output)


if __name__ == "__main__":
    main()
