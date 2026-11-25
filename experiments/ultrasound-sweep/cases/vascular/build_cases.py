"""Render original vascular teaching schematics and the visit records."""
import argparse
from html import escape
import json
import math
from pathlib import Path


AIUM = {
    "title": "AIUM adult abdominal aorta practice parameter, 2025 revision",
    "url": "https://doi.org/10.1002/jum.70167",
}
IAC = {
    "title": "IAC vascular testing standards, extracranial cerebrovascular documentation",
    "url": "https://intersocietal.org/wp-content/uploads/2026/08/IACVascularTestingStandardsAug2026.pdf#page=24",
}
CRITERIA = {
    "title": "IAC modified SRU criteria for ICA stenosis",
    "url": "https://intersocietal.org/wp-content/uploads/2023/11/IAC-Updated-Recommendations-for-Carotid-Stenosis-Interpretation-Criteria_11.1.23.pdf",
}
COMPARISON = {
    "title": "Acquired comparison: AAA with mural thrombus, Mikael Häggström, CC0. Separate patient.",
    "url": "https://commons.wikimedia.org/w/index.php?title=File:Ultrasonography_of_abdominal_aortic_aneurysm_with_mural_thrombus.jpg&oldid=1264972910",
}
WIDTH, HEIGHT = 800, 420
INK = "#dee8ed"
GOLD = "#f2c668"


def label(x, y, content, size=16, color=INK):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(content)}</text>'


def line(x1, y1, x2, y2, color=INK, width=1.5):
    return (f'<path d="M{x1:g} {y1:g}L{x2:g} {y2:g}" stroke="{color}" '
            f'stroke-width="{width}" fill="none"/>')


def path(d, fill, stroke="none", width=1.5):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def ellipse(cx, cy, rx, ry, fill, stroke="none"):
    return (f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')


def caption(view_title, marks):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img"><title>{escape(view_title)}</title>'
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#131b22"/>'
            '<g font-family="system-ui, sans-serif">'
            + label(24, 30, "MODELED TEACHING SCHEMATIC", 12, "#a4bac7")
            + label(24, 62, view_title, 23)
            + marks + "</g></svg>\n")


def caliper(x1, y1, x2, y2):
    return line(x1, y1, x2, y2, GOLD) + "".join(
        line(x - 5, y, x + 5, y, GOLD) + line(x, y - 5, x, y + 5, GOLD)
        for x, y in ((x1, y1), (x2, y2))
    )


def aorta_end_on(diameters, thrombus=False):
    # Project physical diameters to a common graphic scale for all transverse levels.
    layout = []
    spacing = 750 / len(diameters)
    for i, (name, ap_mm, width_mm) in enumerate(diameters):
        x, y = 25 + spacing * (i + .5), 228
        rx, ry = width_mm * 2.1, ap_mm * 2.1
        layout.append(label(x - spacing / 2 + 10, 105, name, 15))
        layout.append(ellipse(x, 355, 39, 14, "#30383c", "#556168"))
        layout.append(ellipse(x, y, rx, ry, "#59646a", "#eef4f6"))
        layout.append(ellipse(x, y - (ry * .23 if thrombus else 0),
                              rx * (.73 if thrombus else .91),
                              ry * (.59 if thrombus else .90), "#0b1015"))
        if thrombus:
            layout.extend([line(x + rx * .36, y + ry * .64, x + 165, y + 66),
                           label(x + 174, y + 72, "Mural thrombus")])
        layout.extend([caliper(x, y - ry, x, y + ry),
                       label(x + rx + 12, y - 16, f"{ap_mm} mm AP", 14, GOLD)])
        if len(diameters) == 1:
            layout.extend([caliper(x - rx, y, x + rx, y),
                           label(x - rx - 182, y + 5, f"{width_mm} mm transverse", 14, GOLD),
                           label(x - 47, 380, "Vertebral body", 13, "#a4bac7")])
    if len(diameters) > 1:
        layout.append(label(25, 393, "Anterior at top · vertebral body deep to the aorta", 14, "#a4bac7"))
    return "".join(layout)


def bifurcation(right_mm, left_mm):
    mark = path("M398 108 L398 200 Q380 223 215 300 M398 200 Q430 225 586 300",
                "none", "#c1cdd3", 55)
    mark += path("M398 108 L398 200 Q380 223 215 300 M398 200 Q430 225 586 300",
                 "none", "#222e35", 46)
    mark += label(426, 177, "Aorta")
    mark += label(95, 208, "Bifurcation") + line(181, 202, 366, 199)
    for x, letter, width_mm in ((195, "Right", right_mm), (605, "Left", left_mm)):
        radius = 2.1 * width_mm
        mark += ellipse(x, 314, radius, radius, "#0b1015", "#dce8ed")
        mark += caliper(x, 314 - radius, x, 314 + radius)
        mark += label(x - 90, 371, f"{letter} common iliac · {width_mm} mm", 15, GOLD)
    return mark


def aorta_long(levels, right_mm, left_mm):
    xs = (64, 191, 326, 473, 617, 729)
    center = 240
    radii = [val * 2.1 for val in levels]
    top = [center - radius for radius in radii]
    bottom = [center + radius for radius in radii]
    def contour(points):
        return "".join(
            f"C{(x1+x2)/2:g} {y1:g} {(x1+x2)/2:g} {y2:g} {x2:g} {y2:g}"
            for (x1, y1), (x2, y2) in zip(points, points[1:])
        )

    near = list(zip(xs, top, strict=True))
    far = list(zip(reversed(xs), reversed(bottom), strict=True))
    wall = f"M{xs[0]} {top[0]:g}" + contour(near)
    wall += f"L{xs[-1]} {bottom[-1]:g}" + contour(far) + "Z"
    lumen = ("M65 203 C144 203 166 204 215 202 S320 187 400 170 "
             "S520 178 617 202 L728 207 L728 270 L617 274 "
             "C510 280 450 259 400 256 S290 265 215 274 L65 279Z")
    return (path(wall, "#58636a", "#ebf3f6", 2) + path(lumen, "#3e758a")
            + line(168, 135, 168, 195) + label(72, 125, "Renal artery level")
            + line(711, 133, 711, 197) + label(602, 124, "Iliac bifurcation")
            + label(295, 219, "Patent flow channel") + label(345, 302, "Mural thrombus")
            + caliper(xs[3], top[3], xs[3], bottom[3])
            + label(xs[3] + 14, top[3] - 12, f"{levels[3]} mm AP", 14, GOLD)
            + label(260, 362, "Fusiform infrarenal dilation")
            + label(24, 395, f"Cranial left · common iliac segments measured separately ({right_mm}/{left_mm} mm R/L)",
                    14, "#a4bac7"))


def iliac_long(right_mm, left_mm):
    marks = []
    for x, side, diameter in ((46, "Right", right_mm), (428, "Left", left_mm)):
        radius = diameter * 2.1
        y = 218
        marks.extend([
            label(x, 132, f"{side} proximal common iliac"),
            path(f"M{x} {y-radius:g}H{x+280}V{y+radius:g}H{x}Z", "#3e758a", "#deedf1", 2),
            caliper(x + 140, y - radius, x + 140, y + radius),
            label(x + 163, y + 5, f"{diameter} mm", 14, GOLD),
            label(x, 280, "Outer-wall calipers · cranial left", 14, "#a4bac7"),
        ])
    return "".join(marks)


def obstruction(what, *, lateral=False, mandibular=False):
    if mandibular:
        return (path("M258 192L481 114L560 161L344 231Z", "#77818a", "#d9e3e8", 3)
                + path("M344 230L560 160L706 356H457Z", "#0a1016")
                + label(96, 155, "Mandibular cortex") + line(239, 154, 311, 176)
                + label(440, 264, "Acoustic shadow", 15)
                + label(24, 388, "Distal ICA not resolved · waveform and velocity withheld", 15, GOLD))
    if lateral:
        return (path("M112 182Q182 97 251 145Q343 210 422 166T570 153", "none", "#d4dfe3", 5)
                + path("M112 188L568 158L668 349L228 370Z", "#303941")
                + "".join(line(147 + (y-194)*.46, y, 599 + (y-194)*.38, y-28, "#3c4851", 3)
                          for y in range(194, 358, 17))
                + label(130, 123, "Residual bowel gas")
                + label(245, 290, "Distal wall and split remain obscure", 16)
                + label(24, 388, "Left lateral repeat · diameter withheld", 15, GOLD))
    return (path("M120 160 Q175 106 232 145 T347 147 T470 139 T594 142 T683 157",
                 "none", "#d4dfe3", 5)
            + path("M120 166 L680 166 L760 363 L42 363Z", "#303941")
            + "".join(line(100, y, 700, y, "#3c4851", 3) for y in range(182, 360, 17))
            + label(125, 123, what + " obscures the target")
            + label(235, 282, "A continuous vessel wall cannot be traced", 17)
            + label(248, 312, "No calipers or velocity saved", 15, GOLD))


def carotid_bmode(side, plaque=False, color=False, limited=False):
    lumen = "#3e758a" if color else "#0b1016"
    main = path("M42 224 L265 224 Q315 224 373 187 L700 138 L705 168 "
                "L405 222 Q370 226 374 237 Q395 249 443 258 L684 294 "
                "L678 327 L410 291 Q332 283 270 263 L42 264Z",
                lumen, "#dbe7eb", 2)
    marks = [main, label(70, 211, "CCA"),
             label(254, 188, "Bulb / bifurcation"), line(331, 195, 329, 224),
             label(642, 124, "ICA"), label(639, 357, "ECA"),
             label(24, 393, f"{side} neck · proximal left · long axis", 14, "#a4bac7")]
    if plaque:
        marks.extend([
            path("M382 219Q415 174 488 180Q515 185 535 196Z", "#b3b7b5", "#e2dfcf"),
            label(386, 318, "Eccentric plaque"),
            line(450, 300, 451, 196),
        ])
        if color:
            marks.extend([
                path("M407 193Q455 181 510 172L483 183Q451 185 420 199Z", "#ffc76a"),
                path("M510 172L552 164L567 175L523 189L482 183Z", "#956ca9"),
                label(418, 97, "Jet and distal flow disturbance"), line(541, 107, 501, 177),
            ])
    if limited:
        marks.extend([path("M566 141L688 115L735 217L575 226Z", "#313b43"),
                      label(518, 245, "Distal ICA obscured", 15, GOLD)])
    return "".join(marks)


def plaque_transverse(residual_mm, reference_mm):
    # Compare same-scale short-axis spans along the direction of narrowing.
    residual_radius = residual_mm * 10
    reference_radius = reference_mm * 10
    return (label(130, 124, "Plaque level") + label(509, 124, "Unaffected distal reference")
            + ellipse(243, 244, 91, 74, "#747d80", "#e1edf1")
            + ellipse(256, 218, 57, residual_radius, "#0b1016")
            + ellipse(594, 244, 68, reference_radius, "#0b1016", "#dbe7eb")
            + caliper(256, 218 - residual_radius, 256, 218 + residual_radius)
            + caliper(594, 244 - reference_radius, 594, 244 + reference_radius)
            + line(221, 279, 93, 319) + label(48, 343, "Eccentric plaque")
            + label(312, 192, f"{residual_mm} mm residual", 14, GOLD)
            + label(669, 242, f"{reference_mm} mm", 14, GOLD)
            + label(24, 394, "Right ICA · transverse · paired views at the same scale", 14, "#a4bac7"))


def wave_panel(x, y, name, psv, edv, angle, label_angle=True, broaden=False):
    width, height = 228, 116
    baseline = y + 87
    header = f"{name} · {angle}°" if label_angle else name
    marks = [label(x, y + 14, header, 14)]
    marks += [line(x + 29, baseline, x + width, baseline, "#64808d"),
              line(x + 29, y + 26, x + 29, baseline + 3, "#64808d")]
    if psv is None:
        marks.extend([label(x + 45, y + 61, "Window unobtainable", 14, GOLD),
                      label(x, y + height, "PSV and EDV withheld", 14)])
        return "".join(marks)
    axis = 250
    scale = 57 / axis
    marks.extend([label(x, y + 35, "250", 10), label(x + 15, baseline + 4, "0", 10),
                  line(x + 25, baseline - axis * scale, x + 29, baseline - axis * scale, "#64808d")])
    pts = []
    for step in range(201):
        phase = (step % 100) / 100
        fraction = math.sin(math.pi * phase / .28) if phase < .14 else (
            math.exp(-4.5 * (phase - .14)) * (1 - phase) / .86)
        velocity = edv + (psv - edv) * fraction
        pts.append((x + 30 + step * .952, baseline - velocity * scale))
    points = " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)
    lower = [(px, baseline - (baseline - py) * (.67 if broaden else .89)) for px, py in pts]
    return_edge = " ".join(f"{px:.2f},{py:.2f}" for px, py in reversed(lower))
    marks += [path(f"M{points} L{return_edge}Z", "#658d85" if broaden else "#48645f"),
              f'<polyline points="{points}" fill="none" stroke="#b9e9df" stroke-width="2"/>',
              label(x, y + height, f"{psv} / {edv} cm/s  PSV / EDV", 14, GOLD)]
    return "".join(marks)


def spectral(samples, focused=False):
    return "".join(
        wave_panel(24 + (i % 3) * 256, 89 + (i // 3) * 144, name, psv, edv, angle,
                   label_angle=psv is not None, broaden=focused and i in (1, 2))
        for i, (name, psv, edv, angle) in enumerate(samples)
    ) + label(24, 402, "Time → · vertical scale in cm/s · angle-corrected samples", 14, "#a4bac7")


def gate_placement():
    marks = carotid_bmode("Right", plaque=True, color=True)
    for x, y, num in ((373, 212, 1), (461, 182, 2), (556, 176, 3)):
        marks += line(x - 14, y + 12, x + 14, y - 12, GOLD, 2)
        marks += line(x - 7, y - 5, x + 7, y + 5, GOLD, 2)
        marks += label(x - 8, y + 45, str(num), 18, GOLD)
    return marks


class CaseBuilder:
    def __init__(self, output):
        self.output = output
        self.cases = []

    def case(self, case_id, family, title, indication, kind, summary, impression, limits, sources):
        record = {
            "id": case_id, "family": family, "title": title, "indication": indication,
            "kind": kind, "summary": summary, "views": [], "impression": impression,
            "limitations": limits, "sources": sources,
        }
        self.cases.append(record)
        return record

    def view(self, case, slug, title, marks, description, measurement=None, *, reference_ids=()):
        image = f"{case['id']}-{slug}.svg"
        (self.output / image).write_text(caption(title, marks), encoding="utf-8")
        view = {"title": title, "image": image, "caption": description}
        if measurement:
            view["measurement"] = measurement
        if reference_ids:
            view["referenceIds"] = list(reference_ids)
        case["views"].append(view)
        return view


def aaa_cases(builder):
    normal_levels = [("Proximal / suprarenal", 24, 23), ("Mid / juxtarenal", 19, 19),
                     ("Distal / infrarenal", 17, 17)]
    screened = "One-time AAA screening in an asymptomatic 68-year-old man with a smoking history"
    model_limit = "Original teaching schematic using authored wall boundaries and caliber. No acquired pixels or sonographer validation."
    normal = builder.case(
        "aaa-negative", "aaa", "AAA screening · negative", screened, "normal",
        "Follow one aorta from just below the diaphragm through the iliac split. Save the largest outer-to-outer AP span.",
        f"Negative screen. Suprarenal aorta visualized without dilation. Largest measured AP diameter {max(row[1] for row in normal_levels)} mm. The infrarenal segment and bifurcation are seen throughout.",
        model_limit + " The AP sizes are rounded starting points from the existing normal atlas sweep, which measured the CT segmentation boundary. These schematics use new illustrative wall contours and iliac geometry.",
        [AIUM],
    )
    builder.view(normal, "stations", "Proximal, mid and distal transverse levels",
                 aorta_end_on(normal_levels),
                 "Follow the aorta anterior to the vertebral body. The marked AP spans run from external anterior wall to external posterior wall.",
                 "24 mm proximal · 19 mm mid · 17 mm distal",
                 reference_ids=("aortic-screening-12", "aortic-screening-30", "aortic-screening-48"))
    builder.view(normal, "split", "Aortic bifurcation and proximal common iliacs",
                 bifurcation(11, 10),
                 "Follow the single distal lumen into both common iliac arteries. The two circles represent perpendicular proximal iliac sections, drawn at their branch locations as a composite.",
                 "Right 11 mm · left 10 mm, outer to outer")

    limited = builder.case(
        "aaa-indeterminate", "aaa", "AAA screening · indeterminate", screened, "limited",
        "The initial anterior sweep loses the distal infrarenal aorta behind bowel gas. Review the alternate window and document what remains unseen.",
        "Indeterminate screen. Suprarenal aorta seen without dilation. The visualized mid aorta is 19 mm AP, but the distal infrarenal aorta and bifurcation remain unevaluable.",
        model_limit + " Distal outer-wall measurements and the full aortic maximum are withheld. The limited windows illustrate the decision to request completion of screening under the local pathway.",
        [AIUM],
    )
    builder.view(limited, "visible", "Visible proximal and mid aorta",
                 aorta_end_on(normal_levels[:2]), "The proximal and mid aortic walls are visible. These spans cover only those levels.",
                 "24 mm proximal · 19 mm mid",
                 reference_ids=("aortic-screening-12", "aortic-screening-30"))
    builder.view(limited, "anterior", "Anterior window · distal aorta obscured",
                 obstruction("Bowel gas"), "Bowel gas interrupts the distal window. The defining landmarks for a wall-to-wall measurement cannot be resolved.")
    builder.view(limited, "retry", "Repeat from a left lateral window",
                 obstruction("Residual bowel gas", lateral=True),
                 "The repeat uses a lateral approach after repositioning. The infrarenal end and split remain obscured, so no maximum for the complete aorta is saved.")

    positive_levels = [("Proximal / suprarenal", 24, 25), ("Proximal infrarenal", 21, 22),
                       ("Distal / infrarenal neck", 22, 23)]
    max_ap, max_width, right_mm, left_mm = 43, 46, 13, 12
    positive = builder.case(
        "aaa-positive", "aaa", "AAA screening · positive with diagnostic views", screened, "abnormal",
        "The screening sweep finds distal enlargement. In the same modeled case, the diagnostic acquisition documents the sac shape, flow channel, renal relationship and both iliacs.",
        f"Positive screen. Fusiform infrarenal AAA measuring up to {max_ap} mm AP × {max_width} mm transverse, with eccentric mural thrombus and a patent residual lumen. The sac ends above the bifurcation. Suprarenal aorta and proximal common iliacs are visualized without dilation.",
        model_limit + " The linked acquired mural-thrombus image is a separate patient and supplies no case measurements. No prior study is modeled, so interval growth is unknown.",
        [AIUM, COMPARISON],
    )
    builder.view(positive, "stations", "Aortic survey through the infrarenal neck", aorta_end_on(positive_levels),
                 "Relate the adjacent nondilated levels to the dilated infrarenal segment saved separately.",
                 "24 mm suprarenal · 21 mm proximal infrarenal · 22 mm distal neck")
    maximum_section = builder.view(positive, "sac", "Largest sac section · transverse", aorta_end_on([("Infrarenal sac", max_ap, max_width)], thrombus=True),
                 "The perpendicular section locates the widest transverse sac. Both calipers reach the outer wall and include the thrombus, which is also visible in Häggström’s linked acquired comparison.",
                 f"{max_ap} mm AP × {max_width} mm transverse, outer to outer")
    maximum_section["illustration"] = {
        "file": "aaa-transverse-cutaway.webp",
        "sha256": "ea6dc59a629232ffcde37226f1cb28754f71526a0272710a1b36241ecf6c80cb",
        "title": "Inside the aneurysm sac",
        "alt": "Cross-section of the modeled aneurysm with a thin outer wall, an open anterior lumen and a posterior crescent of mural thrombus.",
        "caption": "AI-generated anatomical illustration, anterior at the top. The crescent of thrombus sits behind the open lumen. Replay the transverse scan and turn on Tissue overlay to see why both calipers reach the outer wall. In the separate acquired image below, the thrombus lies above the lumen on screen.",
    }
    builder.view(positive, "long", "Long axis · extent and lumen",
                 aorta_long([24, 21, max_ap - 8, max_ap, 22, 18], right_mm, left_mm),
                 "Align the long axis with the residual channel and relate the fusiform shape to the renal level and bifurcation. The color fill denotes the patent channel inside mural thrombus.",
                 f"{max_ap} mm AP, outer to outer in long axis")
    builder.view(positive, "split", "Bifurcation and iliac cross-sections", bifurcation(right_mm, left_mm),
                 "The sac ends proximal to the split. The two perpendicular sections show the widest imaged portions of the proximal common iliac arteries.",
                 f"Right {right_mm} mm · left {left_mm} mm, outer to outer")
    builder.view(positive, "iliacs", "Longitudinal proximal common iliacs", iliac_long(right_mm, left_mm),
                 "Confirm continuity of each proximal common iliac in long axis. Only the proximal iliac segments are characterized.",
                 f"Right {right_mm} mm · left {left_mm} mm, outer to outer")

CAROTID_COMPARISON = {
    "title": "Li et al., Figure 1A–B: acquired right proximal ICA plaque and Doppler. Separate patient.",
    "url": "https://cdn.amegroups.cn/journals/amepc/files/journals/2/articles/61527/public/61527-PB6-2943-R2.pdf#page=3",
}


def normal_carotid_sections(side):
    return (
        ellipse(151, 237, 61, 59, "#0b1016", "#dbe7eb")
        + ellipse(396, 238, 66, 52, "#0b1016", "#dbe7eb")
        + ellipse(479, 207, 29, 27, "#0b1016", "#dbe7eb")
        + ellipse(645, 234, 51, 47, "#0b1016", "#dbe7eb")
        + label(91, 127, "Mid / distal CCA")
        + label(349, 127, "Bifurcation")
        + label(590, 127, "Proximal ICA")
        + label(360, 244, "ICA") + label(463, 212, "ECA", 12)
        + label(24, 389, f"{side} neck · transverse · anterior at top", 14, "#a4bac7")
    )


def carotid_samples(builder, record, side, samples, limited=False):
    stem = side.lower()
    builder.view(
        record, f"{stem}-gray", f"{side} carotid long-axis grayscale",
        carotid_bmode(side, limited=limited),
        "Identify the CCA, bulb, bifurcation and proximal ICA. The distal ICA passes beyond the available window."
        if limited else "Identify the CCA, bulb and bifurcation, then trace the ICA toward the distal window.",
    )
    builder.view(
        record, f"{stem}-short", f"{side} carotid transverse sweep",
        normal_carotid_sections(side),
        "Trace the common trunk into both branches and inspect the proximal ICA lumen in cross-section.",
        reference_ids=("carotid-bifurcation",) if side == "Left" else (),
    )
    builder.view(
        record, f"{stem}-color", f"{side} carotid color survey",
        carotid_bmode(side, color=True, limited=limited),
        "The color fill illustrates patent CCA, ECA and visible proximal ICA flow. Repositioning is needed to attempt the distal ICA."
        if limited else "Follow color fill through the CCA, bifurcation and visible ICA. The schematic color denotes a flowing channel.",
    )
    sample_caption = "Review separate angle-corrected pulsed-wave (PW) Doppler samples from the CCA, ICA, ECA and vertebral artery."
    if limited:
        sample_caption += " The distal ICA window was lost and has no recorded velocity."
    else:
        sample_caption += " The vertebral sample is antegrade, with positive velocities on this display."
    builder.view(record, f"{stem}-spectra", f"{side} carotid spectral record", spectral(samples),
                 sample_caption, "Each available panel saves angle, PSV and EDV.",
                 reference_ids=("carotid-cca-spectral", "carotid-ica") if side == "Right" else ())


def carotid_cases(builder):
    stations = ("Proximal CCA", "Distal CCA", "Proximal ICA", "Distal ICA", "ECA", "Vertebral")
    right = [(name, psv, edv, angle) for name, (psv, edv, angle) in zip(
        stations, [(87, 17, 55), (72, 16, 58), (84, 26, 55), (79, 28, 58), (94, 9, 56), (44, 13, 54)], strict=True)]
    left = [(name, psv, edv, angle) for name, (psv, edv, angle) in zip(
        stations, [(91, 19, 54), (76, 17, 56), (92, 29, 58), (86, 27, 57), (103, 10, 56), (49, 14, 53)], strict=True)]
    model_limit = "Original teaching schematics with authored flow and spectra. The velocity traces are scaled to the displayed values. No acquired pixels, scanner measurements or sonographer validation."
    normal = builder.case(
        "carotid-normal", "carotid", "Bilateral carotid duplex · normal",
        "Evaluate a cervical bruit for extracranial carotid stenosis", "normal",
        "Document both sides, from carotid grayscale and color through angle-corrected carotid and vertebral waveforms.",
        f"No plaque or Doppler evidence of ICA stenosis on either side. ICA/CCA PSV ratios are {right[2][1] / right[1][1]:.2f} right and {left[2][1] / left[1][1]:.2f} left. Both vertebral arteries show antegrade flow.",
        model_limit + " The modeled windows stop at the accessible cervical segments.",
        [IAC, CRITERIA],
    )
    carotid_samples(builder, normal, "Right", right)
    carotid_samples(builder, normal, "Left", left)

    limited = builder.case(
        "carotid-limited", "carotid", "Bilateral carotid duplex · limited",
        "Evaluate a left cervical bruit for extracranial carotid stenosis", "limited",
        "The distal left ICA passes deep behind the mandible. Save the visualized segments, then document the alternate attempt.",
        "Limited left ICA assessment. No focal plaque or velocity elevation in the imaged proximal left ICA. The distal left ICA is ungraded because its wall and a reproducible spectral envelope remain unobtainable. No plaque or Doppler evidence of stenosis in the right ICA.",
        model_limit + " A complete left ICA/CCA PSV ratio is withheld because the true highest ICA PSV could have been outside the visualized window.",
        [IAC, CRITERIA],
    )
    carotid_samples(builder, limited, "Right", right)
    left_limited = [sample if sample[0] != "Distal ICA" else (sample[0], None, None, None) for sample in left]
    carotid_samples(builder, limited, "Left", left_limited, limited=True)
    builder.view(limited, "retry", "Distal left ICA · alternate window",
                 obstruction("Mandibular shadow", mandibular=True),
                 "Reduce neck rotation and move to a posterolateral window. The vessel still cannot be reliably followed or sampled at an appropriate correction angle.")

    jet_psv, jet_edv = 207, 67
    residual_mm, reference_mm = 2.7, 6.1
    plaque_estimate = (1 - residual_mm / reference_mm) * 100
    right_plaque = [sample if sample[0] != "Proximal ICA" else ("Proximal ICA jet", jet_psv, jet_edv, 58)
                    for sample in right]
    ratio = jet_psv / right_plaque[1][1]
    plaque = builder.case(
        "carotid-plaque", "carotid", "Bilateral carotid duplex · right ICA stenosis",
        "Assess the extracranial carotids after transient right monocular visual loss", "abnormal",
        "Localize eccentric proximal right ICA plaque. Compare the spectra before, at and downstream of the narrowing, then integrate both sides.",
        f"Right proximal ICA stenosis in the 50–69% category by modified IAC criteria. The paired short-axis sections show about {plaque_estimate:.0f}% diameter reduction. The jet reaches {jet_psv} cm/s PSV, {jet_edv} cm/s EDV and an ICA/CCA PSV ratio of {ratio:.2f}. No plaque or Doppler evidence of left ICA stenosis. Vertebral flow is antegrade bilaterally.",
        model_limit + " The cited Li et al. panels show an independently acquired higher-grade lesion in another patient. They supply no case velocities or stenosis grade.",
        [IAC, CRITERIA, CAROTID_COMPARISON],
    )
    builder.view(plaque, "right-gray", "Right carotid grayscale · longitudinal",
                 carotid_bmode("Right", plaque=True),
                 "Follow the narrowing from the bifurcation into the proximal right ICA. As in Li et al. Figure 1A, look for eccentric plaque along the wall and a residual flow channel.")
    builder.view(plaque, "right-short", "Right proximal ICA · transverse plaque",
                 plaque_transverse(residual_mm, reference_mm),
                 "The asymmetric plaque occupies one side of the vessel. Estimate diameter reduction from the residual lumen relative to the unaffected distal ICA shown at the same scale.",
                 f"{residual_mm} mm residual / {reference_mm} mm distal reference · about {plaque_estimate:.0f}% reduction")
    builder.view(plaque, "right-color", "Right proximal ICA · color and spectral gates",
                 gate_placement(), "The narrowed color channel localizes the jet. As in Li et al. Figure 1B, place the gate in the narrowed flow stream for spectral confirmation. The numbered gates are before (1), at (2) and just beyond (3) the narrowing.")
    focused = [("1 · Before", 94, 27, 56), ("2 · Jet", jet_psv, jet_edv, 58), ("3 · Just beyond", 122, 39, 58)]
    builder.view(plaque, "right-triplet", "Right ICA · prejet, jet and postjet spectra",
                 spectral(focused, focused=True),
                 "The sample at the narrowing gives the highest PSV. The immediately downstream spectrum has lower PSV with persistent broadening.",
                 "Before 94/27 · jet 207/67 · just beyond 122/39 cm/s PSV/EDV")
    builder.view(plaque, "right-spectra", "Right carotid spectral record", spectral(right_plaque),
                 "Compare the jet with the right distal CCA reference and the more distant distal ICA. The antegrade vertebral artery has a separate window.",
                 f"Right ICA/CCA PSV ratio {jet_psv}/{right[1][1]} = {ratio:.2f}",
                 reference_ids=("carotid-cca-spectral",))
    carotid_samples(builder, plaque, "Left", left)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=Path(__file__).parent)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    builder = CaseBuilder(args.output)
    aaa_cases(builder)
    carotid_cases(builder)
    (args.output / "cases.json").write_text(
        json.dumps(builder.cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
