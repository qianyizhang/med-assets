"""Render authored obstetric teaching diagrams and case records."""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from html import escape
from math import cos, pi, sin, sqrt
from pathlib import Path


def line(x1, y1, x2, y2, color="#d8dde0", width=2):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def label(x, y, text, color="#f5f5f5"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="15">{escape(str(text))}</text>'


def ellipse(x, y, rx, ry, fill="#202328", stroke="#c9ced3", width=3):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def path(d, fill="#33383d", stroke="#c9ced3", width=3):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def span(x1, y1, x2, y2, text, tx, ty):
    color = "#ffdf81"
    graphic = line(x1, y1, x2, y2, color, 1)
    for x, y in [(x1, y1), (x2, y2)]:
        graphic += line(x - 5, y, x + 5, y, color)
        graphic += line(x, y - 5, x, y + 5, color)
    return graphic + label(tx, ty, text, color)


def pointer(text, tx, ty, x, y):
    return line(tx, ty + 4, x, y, "#99d5e2", 1) + label(tx, ty, text, "#aee3ef")


def shade(d):
    return path(d, "#10151d", "#353e4b", 1)


def diagram(title, *panels):
    width = 354 if len(panels) == 1 else 700
    rows = (len(panels) + 1) // 2
    height = 50 + rows * 202
    img = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
        f'<title>{escape(title)} — modeled schematic</title>',
        '<rect width="100%" height="100%" fill="#0c1016"/>',
        '<g font-family="system-ui,sans-serif">',
    ]
    if len(panels) == 1:
        img.append(label(16, 28, "MODELED SCHEMATIC", "#aee3ef"))
    else:
        img.extend([label(16, 28, title), label(522, 28, "MODELED SCHEMATIC", "#aee3ef")])
    for index, (name, content) in enumerate(panels):
        last_unpaired = index == len(panels) - 1 and len(panels) % 2
        x = (width - 334) // 2 if last_unpaired else 10 + (index % 2) * 346
        y = 44 + (index // 2) * 202
        img.extend([
            f'<svg x="{x}" y="{y}" width="334" height="190" viewBox="0 0 334 190">',
            '<rect width="334" height="190" fill="#191f28" rx="6"/>',
            label(8, 19, name),
            '<svg x="4" y="24" width="326" height="162" viewBox="0 0 326 162">',
            content, '</svg></svg>',
        ])
    return "".join(img) + "</g></svg>\n"


def crl_age(mm):
    days = round(8.052 * sqrt(mm) + 23.73)
    return f"{days // 7} wk {days % 7} d"


def fetal_weight(hc, ac, fl):
    # Hadlock HC/AC/FL, with inputs converted from mm to cm.
    hc, ac, fl = [mm / 10 for mm in (hc, ac, fl)]
    return round(10 ** (1.326 + 0.0107 * hc + 0.0438 * ac + 0.158 * fl - 0.00326 * ac * fl))


def early_uterus(kind):
    uterus = path("M22 27Q86 8 162 48L304 120Q286 144 252 140L146 100Q56 119 22 27Z", "#495057")
    uterus += path("M34 39Q111 32 171 72L275 123", "none", "#a6adb5", 4)
    if kind != "normal":
        return uterus + pointer("Empty cavity", 72, 132, 111, 52) + pointer("Cervix", 249, 92, 260, 123)
    uterus += ellipse(99, 59, 40, 26, "#111921", "#ddd", 4)
    uterus += ellipse(82, 56, 8, 7, "#1b2025", "#e6e6e6", 3)
    uterus += path("M99 71Q116 67 121 50Q111 41 104 55Q98 62 99 71Z", "#9ca2a8")
    return uterus + pointer("Intrauterine sac", 15, 100, 65, 70) + pointer("Embryo", 172, 116, 116, 54)


def adnexa(kind):
    panel = ellipse(87, 79, 51, 33, "#4a5158")
    panel += ellipse(69, 72, 13, 10, "#1c222a", "#9097a3", 2)
    panel += ellipse(92, 88, 10, 8, "#1c222a", "#9097a3", 2)
    panel += pointer("Ovary", 29, 129, 69, 105)
    if kind == "abnormal":
        panel += ellipse(225, 67, 34, 26, "#12181f", "#dbdfe4", 5)
        panel += ellipse(226, 67, 10, 8, "#15151c", "#eee", 3)
        return (panel + pointer("Tubal sac with yolk sac", 117, 129, 226, 74)
                + span(191, 67, 259, 67, "18 mm", 196, 28))
    if kind == "limited":
        return panel + shade("M148 10H320L301 152H184Z") + label(174, 77, "Bowel shadow")
    return panel + label(156, 84, "No discrete mass")


def embryo(mm):
    x0, x1 = 106, 106 + mm * 8
    return (
        ellipse((x0 + x1) / 2, 88, (x1 - x0) / 2 + 38, 55, "#10151d", "#e2e4e5", 4)
        + path(f"M{x0} 86Q{x0+2} 57 {x0+24} 67Q{x1-22} 70 {x1} 86Q{x1-25} 107 {x0} 86Z", "#a5acb3")
        + ellipse(93, 102, 10, 9, "#121921", "#e2e4e5", 3)
        + span(x0, 86, x1, 86, f"CRL {mm} mm", 109, 130)
        + pointer("Yolk sac", 15, 136, 84, 105)
    )


def m_mode(cycles, seconds):
    x0, x1 = 34, 298
    coords = []
    for n in range(401):
        t = n / 400
        y = 83 - 19 * cos(2 * pi * cycles * t) + 4 * sin(4 * pi * cycles * t)
        coords.append(f"{x0 + (x1 - x0) * t:.2f},{y:.2f}")
    cycles_grid = "".join(
        line(x0 + (x1 - x0) * n / cycles, 49, x0 + (x1 - x0) * n / cycles, 111, "#546472", 1)
        for n in range(cycles + 1)
    )
    return (
        cycles_grid + line(x0, 121, x1, 121, "#98a8b6", 1)
        + line(x0, 34, x0, 121, "#98a8b6", 1)
        + line(x0, 47, x1, 47, "#66717e", 3)
        + f'<polyline points="{" ".join(coords)}" fill="none" stroke="#eceff0" stroke-width="3"/>'
        + span(x0, 111, x1, 111, f"{cycles} cycles / {seconds:.2f} s", 103, 151)
        + label(x0 - 4, 139, "0 s") + label(x1 - 42, 139, f"{seconds:.2f} s")
        + label(8, 30, "Depth") + label(253, 160, "Time →")
    )


def profile(crl, limited=False, annotate=True):
    crown, rump = 51, 51 + 3.2 * crl
    panel = (
        path(f"M{crown} 77Q45 33 86 21Q131 6 150 47L166 61L153 68L154 76L142 87Q202 78 {rump} 77Q{rump+16} 117 181 133Q143 136 119 106Q64 111 {crown} 77Z", "#626b73")
        + path(f"M116 103Q153 133 {rump-7} 106", "none", "#d8dbde", 5)
        + line(148, 49, 158, 57, "#fff", 4)
    )
    if limited:
        return (f'<g transform="rotate(9 120 90)">{panel}</g>'
                + shade("M81 86L195 104L203 151L72 151Z")
                + pointer("Adjacent amnion", 17, 144, 116, 94))
    return panel + span(crown, 77, rump, 77, f"CRL {crl} mm", 214, 145) if annotate else panel


def nuchal(nt):
    scale = 8
    y1, y2 = 87, 87 + nt * scale
    panel = path("M20 74Q28 29 82 22Q133 22 158 45L176 59L165 67L169 75L149 83Q216 68 305 82L309 114L20 115Z", "#434c54")
    panel += line(156, 49, 167, 55, "#fff", 4)
    panel += path(f"M65 {y1}H267L273 94Q235 {y2} 202 {y2}Q134 {y2} 65 {y1}Z", "#0c121a", "#f0f2f4", 2)
    return (
        panel + span(202, y1, 202, y2, f"NT {nt:.1f} mm", 215, 157)
        + pointer("Nasal bone", 211, 37, 162, 52)
        + pointer("Amnion", 38, 155, 84, 136)
        + line(15, 136, 305, 136, "#aab3bb", 1)
    )


def head(hc, bpd=None, plane="Thalami"):
    # The ellipse is calibrated with its perimeter and optional transverse diameter.
    short = bpd / 2 if bpd else hc / (2 * pi) * 0.84
    long = short * 1.27
    for _ in range(24):
        perimeter = pi * (3 * (long + short) - sqrt((3 * long + short) * (long + 3 * short)))
        long += (hc - perimeter) / 4
    scale = min(103 / long, 58 / short)
    long, short = long * scale, short * scale
    panel = ellipse(150, 80, long, short, "#5d666f", "#eee", 4)
    panel += ellipse(150, 80, long + 3, short + 3, "none", "#ffdf81", 1)
    panel += line(150 - long + 5, 80, 150 + long - 5, 80, "#eee", 2)
    panel += ellipse(216, 80, 10, 8, "#10161e", "#e1e5ec", 2)
    panel += ellipse(132, 66, 15, 9, "#333c47", "#aeb5c0", 1)
    panel += ellipse(132, 93, 15, 9, "#333c47", "#aeb5c0", 1)
    panel += label(20, 155, f"HC {hc} mm")
    panel += pointer(plane, 246, 72, 139, 70)
    if bpd:
        panel += span(150, 80 - short, 150, 80 + short, f"BPD {bpd} mm", 181, 153)
    return panel


def abdomen(ac, defect=0, annotate=True):
    # Preserve a common magnification for biometry at each modeled stage.
    scale = 1.88 if ac >= 200 else 3.24
    a, b = round(scale * ac / 5.105, 1), round(scale * ac * 0.60 / 5.105, 1)
    panel = ellipse(141, 83, a, b, "#56616b", "#f0f2f5", 3)
    if annotate:
        panel += ellipse(141, 83, a, b, "none", "#ffdf81", 1)
    panel += ellipse(110, 66, 21, 13, "#121922") + pointer("Stomach", 28, 22, 98, 61)
    panel += path("M134 89Q163 59 195 76", "none", "#131820", 7)
    panel += pointer("Portal sinus", 217, 115, 169, 76)
    if defect:
        panel = path("M250 64Q218 15 129 22Q38 29 42 85Q47 140 138 141Q224 140 248 96", "#56616b", "#f0f2f5", 3)
        panel += path("M245 63Q294 34 305 70Q319 113 245 96", "#343b45", "#f0f2f5", 3)
        panel += ellipse(275, 76, 9, 9) + ellipse(288, 89, 10, 7)
        panel += span(248, 64, 248, 96, f"{defect} mm", 251, 130)
        return panel + pointer("Bowel in sac", 207, 26, 276, 70) + pointer("Cord apex", 179, 150, 302, 95)
    return panel + label(24, 148, f"AC {ac} mm") if annotate else panel


def femur(fl):
    x0, x1 = 50, 50 + fl * 3.1
    return (
        ellipse((x0 + x1) / 2, 80, (x1 - x0) / 2 + 22, 36, "#464f59", "#8e9ca9", 2)
        + line(x0, 80, x1, 80, "#f0f0f0", 10)
        + span(x0, 80, x1, 80, f"FL {fl} mm", 106, 134)
    )


def cavity(kind):
    outer = ellipse(159, 79, 124, 60, "#151c25", "#a9b3bb", 3)
    outer += path("M37 89Q92 121 209 122Q272 109 281 71L275 108Q152 181 44 117Z", "#69737b")
    if kind == "late":
        outer += path("M82 136Q101 142 115 151L144 151Q161 140 174 135", "none", "#a9b3bb", 2)
        outer += pointer("Lower uterine segment", 141, 160, 149, 147)
    skull_y = 111 if kind == "late" else 65
    outer += ellipse(129, skull_y, 31, 27, "#4f5963", "#e6ecee", 4)
    outer += path(f"M164 {skull_y}Q199 {skull_y-39} 243 69Q247 102 193 108Z", "#59646e")
    return outer + pointer("Placenta", 221, 150, 230, 123) + pointer("Head", 26, 153, 109, skull_y)


def fluid(pocket, annotate=True):
    y0, y1 = 26, 26 + pocket * 2.25
    return (
        path(f"M5 20Q120 35 321 20L324 {y1}Q160 {y1-8} 4 {y1}Z", "#10151d", "#a5b0bc", 2)
        + (span(144, y0, 144, y1, f"DVP {pocket / 10:.1f} cm", 171, 134) if annotate else "")
        + pointer("Amniotic fluid", 18, 117, 110, (y0 + y1) / 2)
    )


def doppler(peak, edv, annotate=True):
    # Each repeated envelope has a short systolic rise and slower diastolic decay.
    y0, scale = 126, 1.7
    points = []
    for beat in range(4):
        for time, fraction in [(0, 0), (.12, 1), (.23, .75), (.45, .43), (.77, .18), (1, 0)]:
            velocity = edv + fraction * (peak - edv)
            points.append(f"{34 + 67 * (beat + time):.2f},{y0 - scale * velocity:.2f}")
    return (
        label(7, 20, "cm/s") + line(32, 23, 32, 126, "#b4c3cb", 1)
        + line(32, y0, 306, y0, "#b4c3cb", 1)
        + f'<polygon points="34,126 {" ".join(points)} 302,126" fill="#51697c" stroke="#d2e0e9"/>'
        + label(9, 131, 0) + label(244, 150, "Time →")
        + (pointer(f"PSV {peak}", 78, 34, 42, y0 - scale * peak) if annotate else "")
        + (pointer(f"EDV {edv}", 153, 145, 168, y0 - scale * edv) if annotate else "")
    )


def landmarks(structures):
    panel = ellipse(156, 82, 121, 62, "#4e5761", "#b5bec6")
    for x, y, rx, ry, name, tx, ty in structures:
        panel += ellipse(x, y, rx, ry, "#19212a", "#d9dfe4", 2)
        panel += pointer(name, tx, ty, x, y)
    return panel


def heart(view, shadow=False):
    panel = ellipse(161, 83, 105, 66, "#47535c")
    if view == "Four chamber":
        panel += path("M158 29Q114 44 93 77Q80 101 103 119Q129 137 157 120Q186 135 212 117Q234 103 224 77Q214 49 158 29Z", "#242b35")
        panel += path("M157 34Q152 59 157 92L157 119M90 93L153 87M161 88L227 93", "none", "#e2e7eb", 4)
        panel += line(110, 95, 125, 87, "#acb9c5", 2)
        panel += line(184, 88, 198, 92, "#acb9c5", 2)
        panel += ellipse(160, 146, 14, 7, "#e2e7eb")
        panel += label(110, 76, "RV") + label(177, 76, "LV") + label(116, 112, "RA") + label(177, 112, "LA")
        panel += pointer("Apex", 205, 24, 161, 33) + label(183, 151, "Spine")
    elif view == "LVOT":
        panel += path("M69 105Q91 51 121 64L153 85L192 52L239 47L240 69L198 76L156 112Q105 136 69 105Z", "#141c25")
        panel += path("M74 62Q112 37 144 67L158 79", "none", "#dde4e8", 3)
        panel += pointer("Aortic root", 195, 35, 193, 64)
        panel += pointer("LV cavity", 35, 149, 112, 102)
        panel += pointer("Septum", 55, 29, 139, 66)
    elif view == "RVOT":
        panel += path("M66 101Q69 62 102 57Q125 58 143 75L190 58Q217 47 248 46L251 60Q225 69 210 77L258 101L248 114L201 89Q159 111 132 124Q88 135 66 101Z", "#151b24")
        panel += ellipse(161, 87, 13, 16, "#313d4a", "#d9e0e5", 2)
        panel += pointer("Main PA", 73, 28, 117, 66)
        panel += pointer("Aorta in cross-section", 11, 150, 159, 89)
        panel += pointer("PA branches", 216, 145, 213, 81)
    elif view == "3VT":
        panel += ellipse(162, 139, 13, 8, "#e1e5eb", "#fff", 2)
        panel += path("M70 43Q99 49 129 67L215 103L219 88Q160 67 139 50Q108 33 77 29Z", "#17212c", "#dce5e8", 3)
        panel += path("M145 34Q174 49 190 67L215 92L215 104L205 103L174 81Q153 59 137 50Z", "#17212c", "#dce5e8", 3)
        panel += ellipse(251, 55, 10, 10, "#191e25", "#d7e0e6")
        panel += ellipse(238, 100, 10, 10, "#11151e", "#fff", 3)
        panel += pointer("Ductal arch", 46, 16, 107, 47) + pointer("Aortic arch", 193, 20, 159, 48)
        panel += pointer("Trachea", 233, 138, 239, 110) + label(112, 157, "Spine")
    else:
        for x, y, r, name in [(83, 74, 23, "PA"), (150, 80, 18, "Ao"), (199, 85, 13, "SVC")]:
            panel += ellipse(x, y, r, r, "#19212a", "#e4ebef")
            panel += label(x - 13, 120, name)
        panel += ellipse(162, 139, 13, 8, "#d5dde5")
    if shadow:
        return panel + shade("M143 5L189 5L300 152H159Z") + label(180, 117, "Rib / spine shadow")
    return panel


def spine(transverse=False):
    if transverse:
        return landmarks([
            (148, 103, 11, 9, "Body", 113, 150),
            (125, 75, 9, 8, "Left arch", 43, 46),
            (171, 75, 9, 8, "Right arch", 193, 46),
        ])
    panel = path("M33 92Q144 33 290 96L290 115Q147 55 33 114Z", "#48545d", "#8f99a5")
    for x in range(45, 286, 20):
        y = 63 + 0.0021 * (x - 160) ** 2
        panel += ellipse(x, y, 7, 6, "#e1e4eb", "#a8b4c0", 1)
    return panel + pointer("Continuous skin line", 113, 25, 165, 56)


def limb(x, y, name):
    panel = path(f"M{x} {y-9}l37 3l24 -8l10 15l-32 11l-39 4Z", "#515b64", "#8797a4", 2)
    panel += line(x + 5, y + 4, x + 35, y + 6, "#f1f3f5", 5)
    panel += line(x + 38, y + 2, x + 63, y - 6, "#d7dee5", 3)
    panel += line(x + 39, y + 7, x + 65, y, "#e6ebef", 3)
    panel += ellipse(x + 70, y - 1, 8, 7, "#aab6bf")
    return panel + label(x, y + 39, name)


def limbs():
    return (limb(53, 36, "Left arm") + limb(183, 36, "Right arm")
            + limb(53, 108, "Left leg") + limb(183, 108, "Right leg"))


def hand():
    panel = path("M27 90L99 70Q135 22 158 37L150 61Q175 58 207 40Q225 36 224 45L195 71L231 55Q246 53 244 66L214 87L237 76Q247 73 248 83L218 104L229 103Q244 102 242 111L202 124Q144 134 105 106L27 110Z", "#535f69")
    for x, y in [(160, 70), (184, 80), (193, 94), (198, 107)]:
        panel += line(111, 90, x, y, "#d8e0e6", 3)
        panel += line(x + 7, y, x + 28, y - 12, "#d8e0e6", 3)
    return panel + pointer("Metacarpals", 138, 152, 149, 94)


def foot():
    panel = path("M22 98L123 86L147 51Q182 34 226 65Q260 71 265 94Q261 116 211 118L151 141Q123 131 101 115L24 120Z", "#535f69")
    panel += line(33, 108, 109, 104, "#e0e5e8", 4)
    panel += line(35, 112, 111, 109, "#e0e5e8", 3)
    for y in range(76, 109, 8):
        panel += line(163, 99, 219, y, "#e0e5e8", 3)
        panel += ellipse(235, y, 4, 3, "#d7e3ec", "#d7e3ec", 1)
    return panel + pointer("Toes", 248, 32, 237, 78) + pointer("Heel", 94, 154, 151, 132)


def cord(kind):
    if kind == "abnormal":
        return abdomen(0, 15) + path("M302 92Q316 88 323 104", "none", "#b6d4e8", 4)
    return (
        ellipse(118, 80, 73, 53, "#56616d")
        + path("M192 80Q213 58 251 74T308 84", "none", "#d5dce0", 12)
        + pointer("Intact wall", 19, 153, 188, 84)
        + pointer("Cord insertion", 190, 130, 200, 75)
    )


def pelvic(kind):
    panel = path("M20 79Q79 28 149 62L239 105Q272 100 305 134", "none", "#abb4bf", 17)
    panel += line(229, 103, 303, 137, "#f0f0f0", 2)
    panel += pointer("Internal os", 199, 153, 240, 106)
    if kind == "first":
        panel += path("M75 43Q139 34 183 79Q135 72 89 66Z", "#8f9ba7")
    else:
        panel += path("M43 40Q105 11 150 62Q122 41 56 59Z", "#8f9ba7")
    return panel + pointer("Placental edge", 12, 121, 148, 63)


def pleural():
    return (
        ellipse(152, 75, 110, 50, "#454f5a")
        + ellipse(111, 71, 24, 28, "#707a84")
        + ellipse(193, 71, 24, 28, "#707a84")
        + path("M70 107Q151 66 236 110", "none", "#e6ecee", 5)
        + pointer("Diaphragm", 115, 150, 144, 89)
        + label(126, 44, "Lungs")
    )


def cord_gate():
    panel = path("M12 76Q53 22 103 41T199 91Q253 120 303 69", "none", "#b6bdc7", 22)
    panel += path("M12 76Q53 22 103 41T199 91Q253 120 303 69", "none", "#346b8b", 7)
    panel += line(100, 5, 174, 121, "#d9e1e9", 1)
    panel += span(129, 61, 141, 54, "UA gate", 181, 44)
    return panel + pointer("Free cord loop", 33, 141, 73, 42)


PROTOCOL = {
    "early": ("SRU first-trimester lexicon", "https://doi.org/10.1148/radiol.240122"),
    "first": ("ISUOG 11–14-week scan", "https://doi.org/10.1002/uog.26106"),
    "mid": ("ISUOG routine mid-trimester fetal scan", "https://doi.org/10.1002/uog.24888"),
    "late": ("ISUOG third-trimester scan", "https://doi.org/10.1002/uog.27538"),
}
REFERENCE = {
    "early": ("Acquired comparison · Murugan et al., Fig. 7A/D/E",
              "https://www.e-ultrasonography.org/journal/view.php?doi=10.14366/usg.19043#f7-usg-19043"),
    "first": ("Acquired comparison · Moroder, nuchal profile at 13 wk 3 d",
              "https://commons.wikimedia.org/wiki/File:Nuchal_translucency_Dr._Wolfgang_Moroder.jpg"),
    "mid": ("Acquired comparison · mid-trimester standard planes, Fig. 1",
            "https://link.springer.com/article/10.1007/s00404-022-06569-2/figures/1"),
    "late": ("Acquired comparison · ISUOG third-trimester deepest vertical pocket, Fig. 15",
             "https://doi.org/10.1002/uog.27538"),
}
DATING = ("Robinson and Fleming · CRL dating equation", "https://pubmed.ncbi.nlm.nih.gov/1182090/")
FETAL_HEART = ("ISUOG fetal cardiac screening", "https://doi.org/10.1002/uog.26224")
HADLOCK = ("Hadlock et al. · HC/AC/FL weight model", "https://doi.org/10.1016/0002-9378(85)90298-4")
DOPPLER = ("ISUOG obstetric Doppler technique", "https://doi.org/10.1002/uog.23698")
FGR = ("ISUOG small-for-gestational-age fetus and growth restriction", "https://doi.org/10.1002/uog.22134")
INDICATION = {
    "early": "Pain or spotting in early pregnancy · location and cardiac activity",
    "first": "Routine 11–14-week scan · dates, plurality and early anatomy",
    "mid": "Routine mid-trimester scan · fetal anatomy and biometry",
    "late": "Fundal height lag · interval growth, fluid and umbilical artery Doppler",
}


# Acquired images from separate subjects, selected for the matching plane or technique.
HEART_REFERENCES = (
    "pregnancy-mid-heart-8", "pregnancy-mid-heart-22", "pregnancy-mid-heart-35",
    "pregnancy-mid-heart-42", "pregnancy-mid-heart-48",
)
OUTFLOW_REFERENCES = HEART_REFERENCES[1:]
MID_ABDOMEN_REFERENCES = (
    "pregnancy-mid-abdomen-10", "pregnancy-mid-abdomen-24", "pregnancy-mid-abdomen-36",
)
VIEW_REFERENCES = {
    "Locate the sac": ("pregnancy-early-sac", "pregnancy-early-crl"),
    "Document cardiac activity": ("pregnancy-early-cardiac",),
    "Count fetuses and date by CRL": ("pregnancy-fetus-12",),
    "Magnify the nuchal region": ("pregnancy-nuchal",),
    "Attempt and repeat nuchal plane": ("pregnancy-nuchal",),
    "Record cardiac activity and basic anatomy": ("pregnancy-fetus-48",),
    "Survey fetal outline and maternal landmarks": ("pregnancy-fetus-12", "pregnancy-placenta-12"),
    "Record heart rate and biometry": (
        "pregnancy-mid-brain-20", "pregnancy-mid-abdomen-10", "pregnancy-mid-spine-limbs-24",
    ),
    "Survey head and face": (
        "pregnancy-mid-brain-12", "pregnancy-mid-brain-28", "pregnancy-mid-brain-38",
        "pregnancy-mid-brain-48", "pregnancy-mid-brain-20",
    ),
    "Sweep thorax and heart": HEART_REFERENCES,
    "Repeat cardiac sweep": OUTFLOW_REFERENCES,
    "Assess abdomen and umbilical insertion": (*MID_ABDOMEN_REFERENCES, "pregnancy-mid-abdomen-48"),
    "Survey spine and extremities": (
        "pregnancy-mid-spine-limbs-10", "pregnancy-mid-spine-limbs-24",
        "pregnancy-mid-spine-limbs-36", "pregnancy-mid-spine-limbs-48",
    ),
    "Document placenta, cervix and fluid": (
        "pregnancy-related-placenta-cervix", "pregnancy-mid-placenta-48",
    ),
    "Confirm lie and assess fluid": (
        "pregnancy-late-presentation-12", "pregnancy-late-presentation-48",
    ),
    "Acquire fetal biometry": (
        "pregnancy-late-biometry-12", "pregnancy-late-biometry-30", "pregnancy-late-biometry-48",
    ),
    "Record usable biometry": ("pregnancy-late-biometry-12", "pregnancy-late-biometry-48"),
    "Sample umbilical artery flow": ("pregnancy-late-cord-48",),
    "Attempt clinically indicated Doppler": ("pregnancy-late-cord-48",),
}
REFERENCE_EXCEPTIONS = {
    ("abnormal", "Assess abdomen and umbilical insertion"): MID_ABDOMEN_REFERENCES,
}


def view(title, caption, *panels, measurement=None):
    return title, caption, panels, measurement


def case(stage, kind, title, summary, views, impression, limitations, *sources):
    return stage, kind, title, summary, views, impression, limitations, sources


OMPHALOCELE_ILLUSTRATION = {
    "file": "omphalocele-transverse-cutaway.svg",
    "chapterId": "insertion",
    "sha256": "dacaf62df2cbdc0e1a10c841c9b3b720d2038318bb2c053f0bd3515bd2b328eb",
    "title": "Bowel and cord attachment in omphalocele",
    "alt": "Transverse fetal abdominal diagram showing bowel passing through a midline wall opening into a membrane-covered sac, with the umbilical cord attached to the sac apex.",
    "caption": "ImageGen illustration traced to editable vectors. Anterior is at the right in the drawing and at the top in the scan. On the modeled replay, turn on Tissue overlay and follow the membrane from the wall opening to the cord attachment. Dahal et al., Figure 1B, marks bowel herniation in a separate twin pregnancy.",
}


def early_cases():
    mm = 10
    age = crl_age(mm)
    return [
        case("early", "normal", "Intrauterine pregnancy with cardiac activity",
             "Stable patient with spotting and uncertain dates. Start with transabdominal orientation, then use the transvaginal approach to resolve early structures.",
             [
                 view("Locate the sac", "Follow the uterine cavity through the cervix. The closer transvaginal section resolves the yolk sac and embryo.",
                      ("Transabdominal orientation", early_uterus("normal")),
                      ("Transvaginal magnification", embryo(mm)),
                      measurement=f"CRL {mm} mm → 8.052 × √{mm} + 23.73 ≈ 49 days ({age})."),
                 view("Document cardiac activity", "Place the M-mode line through the embryonic cardiac region. Count cycles between matching phases of the sampled motion trace.",
                      ("Transvaginal embryo", embryo(mm) + line(136, 19, 136, 118, "#9dcfe4", 1)),
                      ("M-mode · depth over time", m_mode(3, 1.25)),
                      measurement="3 cycles in 1.25 s × 60 = 144 bpm."),
                 view("Check adnexa and cul-de-sac", "Sweep both ovaries and adjacent tubes. No discrete mass in either adnexa and no pelvic free fluid are depicted.",
                      ("Right adnexa", adnexa("normal")), ("Left adnexa", adnexa("normal")),
                      ("Posterior cul-de-sac", pelvic("first") + label(31, 152, "No visible fluid collection")),
                      ("Cervix and uterine cavity", early_uterus("normal"))),
             ],
             f"Single intrauterine pregnancy, measured CRL dates to {age} with embryonic cardiac activity.",
             "All measurements derive from authored geometry or temporal samples. Adnexal and pelvic views are simplified.",
             DATING),
        case("early", "abnormal", "Tubal ectopic pregnancy",
             "Stable patient with unilateral pain and a positive pregnancy test. Transabdominal imaging shows no intrauterine sac, so the exam proceeds transvaginally.",
             [
                 view("Sweep uterine cavity", "The cavity is empty on the transvaginal longitudinal section. An empty uterus alone does not localize the pregnancy.",
                      ("Transvaginal uterus", early_uterus("abnormal")), ("Left adnexa", adnexa("normal"))),
                 view("Localize the right adnexal sac", "Sweep through the ovary and the separate right adnexal sac. A yolk sac within the extraovarian sac establishes an ectopic pregnancy. Document cul-de-sac fluid.",
                      ("Right adnexa", adnexa("abnormal")),
                      ("Cul-de-sac", pelvic("first") + path("M85 109Q145 124 211 108Q167 151 85 109Z", "#131b25") + pointer("Trace fluid", 26, 145, 106, 118)),
                      measurement="Right extraovarian sac 18 mm across its outer boundary in this section. CRL and rate are unassigned."),
             ],
             "Definite right tubal ectopic pregnancy in this modeled presentation. Communicate promptly to the treating team.",
             "The diagram illustrates a yolk sac separate from the ovary. It does not encode hemodynamic status.",
             ("Acquired ectopic comparisons · SRU lexicon, Fig. 8 and sliding-sign cine", PROTOCOL["early"][1])),
        case("early", "limited", "Pregnancy of unknown location",
             "Stable patient with spotting and a positive pregnancy test. Both transabdominal and transvaginal approaches are attempted.",
             [
                 view("Check cavity and adnexa", "Transvaginal imaging shows no probable or definite intrauterine pregnancy. The left adnexal sweep reveals no mass.",
                      ("Transvaginal uterus", early_uterus("limited")), ("Left adnexa", adnexa("normal"))),
                 view("Repeat right adnexal view", "Re-angle after changing bladder filling and use gentle probe pressure. Bowel shadow still hides part of the right adnexa. No probable or definite extrauterine gestation is identified in the visible field.",
                      ("Initial transverse view", adnexa("limited")), ("Repeat oblique view", adnexa("limited")),
                      measurement="No established sac or embryo for dating or rate measurement."),
             ],
             "Pregnancy of unknown location with limited right adnexal assessment. Arrange clinical follow-up with serial hCG and repeat transvaginal imaging per the treating team.",
             "Both an early intrauterine pregnancy and ectopic pregnancy remain possible. The right adnexa is incompletely observed. This descriptive PUL impression requires follow-up because exclusion of ectopic pregnancy is incomplete."),
    ]


def first_cases():
    records = []
    for kind, crl, nt, title in [
        ("normal", 60, 1.5, "Singleton with a measurable nuchal profile"),
        ("abnormal", 62, 4.5, "Increased nuchal translucency"),
        ("limited", 59, None, "Unobtainable nuchal measurement"),
    ]:
        # BMUS implements the corrected Robinson–Fleming curve at this stage.
        days = round(8.052 * sqrt(crl * 1.037) + 23.73)
        age = f"{days // 7} wk {days % 7} d"
        views = [
            view("Count fetuses and date by CRL", "Survey the uterus for fetal number and position, then align the fetal midsagittal plane in neutral posture. Measure crown to rump without including limbs.",
                 ("Singleton overview", cavity("first")), ("Crown–rump length", profile(crl)),
                 measurement=f"One fetus, CRL {crl} mm. Using the BMUS curve, 8.052 × √(1.037 × {crl}) + 23.73 rounds to {days} days ({age})."),
            view("Record cardiac activity and basic anatomy", "Use the cardiac motion line for a time sample. Rotate to axial head and abdominal planes to check the calvarium, midline and choroid plexuses, left-sided stomach and abdominal wall.",
                 ("M-mode · depth over time", m_mode(3, 1.2)),
                 ("Axial brain", landmarks([(123, 60, 25, 9, "Choroid plexus", 7, 34),
                                            (121, 112, 25, 9, "Choroid plexus", 12, 149)])
                                  + line(54, 85, 264, 85, "#d7e0e6")),
                 ("Upper abdomen", landmarks([(102, 75, 23, 15, "Stomach", 12, 30)])),
                 ("Pelvic section", landmarks([(152, 82, 21, 16, "Bladder", 209, 138)])),
                 ("Cardiac orientation", heart("Four chamber")),
                 ("Abdominal cord insertion", cord("normal")),
                 measurement="3 cycles in 1.20 s × 60 = 150 bpm."),
            view("Survey fetal outline and maternal landmarks", "Confirm the facial profile, four limbs, longitudinal spine and abdominal wall. Save the placental location and cervix relationship.",
                 ("Fetal profile", profile(crl)), ("Four extremities", limbs()),
                 ("Longitudinal spine", spine()), ("Posterior placenta", pelvic("first"))),
        ]
        if nt is None:
            views.insert(1, view("Attempt and repeat nuchal plane",
                                 "Wait for movement and rescan after maternal position change. The repeat remains oblique, with the amnion close to the posterior neck. Defer NT and arrange a repeat within the sampling window.",
                                 ("Initial flexed / obscured", profile(crl, limited=True)),
                                 ("Repeat oblique", profile(crl, limited=True) + shade("M160 44L234 74L281 148L225 152Z")),
                                 measurement="NT unavailable. CRL comes from a separate acceptable acquisition."))
            impression = f"Single fetus dated by CRL to {age} with cardiac activity. NT assessment incomplete."
            limits = "Fetal position and poorly separated amnion prevent a reliable NT measurement. The acquired image demonstrates an obtainable plane in a separate pregnancy."
            extras = ()
        else:
            views.insert(1, view("Magnify the nuchal region",
                                 "Distinguish amnion from skin. In a neutral midsagittal profile, caliper the inner borders at the widest clear space.",
                                 ("Midsagittal profile", profile(crl)),
                                 ("Magnified neck", nuchal(nt)),
                                 measurement=f"CRL {crl} mm; NT {nt:.1f} mm."))
            if kind == "abnormal":
                impression = f"Single fetus dated by CRL to {age} with cardiac activity and increased NT of {nt:.1f} mm. Refer for specialist counseling and assessment."
                limits = "An increased NT is a risk marker. No genetic diagnosis or complete structural assessment is encoded."
                extras = (("Acquired increased NT example · case report, Fig. 1", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3671815/"),)
            else:
                impression = f"Single fetus dated by CRL to {age} with cardiac activity and NT {nt:.1f} mm. No major finding in the modeled early anatomy views."
                limits = "Early anatomy coverage is schematic. A later anatomy survey remains part of routine care."
                extras = ()
        records.append(case("first", kind, title, "Routine first-trimester visit with one fetus.", views,
                            impression, limits,
                            ("BMUS · fetal measurement and corrected CRL dating curve", "https://www.bmus.org/static/uploads/resources/Aug_2009_Fetal_Measurements_D3NApK5.pdf"), *extras))
    return records


def mid_cases():
    records = []
    for kind, bpd, hc, ac, fl, title in [
        ("normal", 47, 178, 153, 33, "Routine anatomy survey with documented views"),
        ("abnormal", 46, 173, 146, 32, "Midline abdominal wall defect"),
        ("limited", 48, 180, 156, 34, "Cardiac outflow views remain incomplete"),
    ]:
        views = [
            view("Record heart rate and biometry", "At 20 weeks by prior dating, record cardiac activity and fetal number. Measure BPD and HC at the transthalamic plane, AC at stomach and portal sinus, and the ossified femoral diaphysis.",
                 ("Transthalamic head", head(hc, bpd)), ("Abdominal circumference", abdomen(ac)),
                 ("Femoral diaphysis", femur(fl)), ("M-mode · depth over time", m_mode(3, 1.25)),
                 measurement=f"Singleton. BPD {bpd} mm; HC {hc} mm; AC {ac} mm; FL {fl} mm. 3 cycles / 1.25 s = 144 bpm."),
            view("Survey head and face", "Sweep from transventricular to posterior fossa. Save orbits, coronal upper lip and profile as distinct planes.",
                 ("Transventricular plane", landmarks([(114, 84, 31, 14, "Ventricle", 4, 43),
                                                        (191, 84, 15, 11, "Choroid plexus", 223, 125)])),
                 ("Posterior fossa", landmarks([(118, 84, 21, 12, "Cerebellum", 12, 32),
                                                 (181, 84, 20, 12, "Cisterna magna", 184, 134)])),
                 ("Orbits", landmarks([(106, 76, 28, 24, "Globe", 27, 25),
                                        (208, 76, 28, 24, "Globe", 219, 25)])),
                 ("Upper lip", ellipse(150, 83, 90, 55, "#495763")
                              + path("M93 102Q120 82 150 96Q176 81 207 103", "none", "#e3e9ec", 5)
                              + pointer("Continuous lip", 126, 146, 151, 96)),
                 ("Profile", profile(59, annotate=False)
                             + pointer("Profile", 185, 39, 158, 63)),
                 ("Cavum and thalami", head(hc))),
            view("Sweep thorax and heart", "Document cardiac situs, four chambers, both outflow tracts and three-vessel planes. Inspect lungs and the diaphragm.",
                 ("Chest and diaphragm", pleural()), ("Four chamber", heart("Four chamber")),
                 ("LV outflow", heart("LVOT", kind == "limited")),
                 ("RV outflow", heart("RVOT", kind == "limited")),
                 ("Three vessels", heart("3VV", kind == "limited")),
                 ("Three vessels and trachea", heart("3VT", kind == "limited"))),
            view("Assess abdomen and umbilical insertion",
                 "Confirm stomach position, both kidneys and bladder. At the anterior midline opening, trace bowel into the membrane-covered sac and follow the cord to the sac apex."
                 if kind == "abnormal" else
                 "Confirm stomach position, both kidneys and bladder, then track the cord to its insertion at the fetal abdominal wall.",
                 ("Both kidneys", landmarks([(103, 90, 29, 16, "Right kidney", 12, 36),
                                               (205, 90, 29, 16, "Left kidney", 213, 38)])),
                 ("Pelvis", landmarks([(152, 87, 31, 23, "Bladder", 210, 130)])),
                 ("Fetal cord insertion", cord(kind)),
                 ("Stomach and portal sinus", abdomen(ac)),
                 measurement="Anterior midline defect 15 mm at its neck." if kind == "abnormal" else None),
            view("Survey spine and extremities", "Trace the spine longitudinally and through transverse levels, then document left and right arms and legs, hands and feet.",
                 ("Longitudinal spine", spine()), ("Transverse spine", spine(True)),
                 ("Four extremities", limbs()), ("Hand", hand()), ("Foot", foot()),
                 ("Femur diaphysis", femur(fl))),
            view("Document placenta, cervix and fluid", "Identify placental position and its relation to the internal cervical os. Assess fluid and check the placental cord insertion.",
                 ("Placental edge and cervix", pelvic("mid")),
                 ("Placental cord insertion", path("M14 96Q177 118 309 88L309 148H14Z", "#727c88")
                     + path("M148 107Q152 67 207 55T276 27", "none", "#d5dce0", 9)
                     + pointer("Cord attachment", 19, 66, 148, 105)),
                 ("Fluid pocket", fluid(45)), ("Fetal lie overview", cavity("first")),
                 measurement="Deepest vertical pocket 4.5 cm in selected cord-free window."),
        ]
        extras = ()
        if kind == "abnormal":
            views.insert(4, view("Confirm the wall finding in another plane",
                                 "Use the sagittal plane to verify the membrane-covered herniation and the apex of the sac as the site of umbilical cord attachment.",
                                 ("Transverse defect", cord(kind)),
                                 ("Sagittal insertion", path("M28 51Q127 83 190 82M28 139Q127 123 188 116", "none", "#dce2e6", 4)
                                  + path("M188 82Q248 45 271 99Q246 150 188 116Z", "#4b5560")
                                  + ellipse(218, 89, 13, 10) + ellipse(238, 112, 13, 10)
                                  + path("M267 97Q284 87 306 65", "none", "#b9dce8", 6)
                                  + pointer("Cord into sac", 205, 27, 277, 91))))
            impression = "Midline membrane-covered abdominal wall defect with a cord inserting into the sac, consistent with omphalocele. Refer for detailed fetal assessment."
            limit = "The schematic illustrates attachment and the neck of the defect. Associated malformations and genetic conditions require additional assessment."
            extras = (("Dahal et al. · acquired bowel herniation, Fig. 1B",
                       "https://pmc.ncbi.nlm.nih.gov/articles/PMC12323075/"),
                      ("Som and Naik · acquired cord attachment at the sac apex, Fig. 2",
                       "https://pubmed.ncbi.nlm.nih.gov/27408166/#figures"),)
        elif kind == "limited":
            views.insert(3, view("Repeat cardiac sweep",
                                 "Repeat after maternal repositioning and a lateral approach. Persistent spine shadow leaves the outflows and three-vessel views incomplete. The independent acquired images show the views needed at targeted completion.",
                                 ("First oblique LVOT", heart("LVOT", True)),
                                 ("Repeat lateral RVOT", heart("RVOT", True) + shade("M71 11L122 10L188 148H113Z"))))
            impression = "Modeled anatomy survey incomplete for cardiac outflow tracts and three-vessel views. Other depicted anatomy has no major finding."
            limit = "The four-chamber image does not resolve the outflow tracts or great-vessel relationships."
        else:
            impression = "Singleton with cardiac activity and biometry concordant with prior dates in this example. No major finding among the modeled anatomy views."
            limit = "Only representative sections are illustrated. Segments and subtle malformations that depend on full cine sweeps remain outside schematic fidelity."
        records.append(case("mid", kind, title, "Anatomic survey at 20 weeks by prior dating.", views,
                            impression, limit, FETAL_HEART, *extras))
    return records


GROWTH = ("Hadlock et al. 1991 · sonographic weight centiles, Table 1",
          "https://obgyn.utoronto.ca/sites/default/files/Hadlock%20Growth%20Chart-Radiology-1991.pdf")
AEDF = ("Acquired comparison · umbilical artery spectra, Fig. 6",
        "https://pubs.rsna.org/doi/full/10.1148/rg.2019180152")


def growth(prior, current):
    def y(weight):
        return round(146 - (weight - 850) / 12, 2)

    panel = line(54, 19, 54, 148) + line(54, 148, 283, 148)
    for previous, now, name in [(908, 1465, "3rd"), (1004, 1621, "10th"), (1210, 1953, "50th")]:
        panel += line(68, y(previous), 234, y(now), "#788a98")
        panel += label(239, y(now) + 3, name, "#c4d1db")
    panel += ellipse(68, y(prior), 5, 5, "#ffdf81", "none")
    if current is not None:
        panel += line(68, y(prior), 234, y(current), "#ffdf81", 2)
        panel += ellipse(234, y(current), 5, 5, "#ffdf81", "none")
    return panel + label(12, 36, "g") + label(58, 160, "28 wk") + label(200, 160, "32 wk")


def late_cases():
    records = []
    for kind, hc, ac, fl, prior, pocket, title in [
        ("normal", 292, 284, 63, 1190, 46, "Interval growth with forward diastolic flow"),
        ("abnormal", 279, 239, 55, 1130, 17, "Fetal growth restriction with absent end-diastolic flow"),
        ("limited", 286, None, 61, 1205, None, "Growth and fluid assessment incomplete"),
    ]:
        views = [
            view("Confirm lie and assess fluid",
                 "The head is near the lower uterine segment. Locate the placenta, then seek the deepest cord-free vertical pocket with the probe perpendicular to the floor.",
                 ("Cephalic presentation", cavity("late")),
                 ("Cord-free vertical pocket", fluid(pocket)) if pocket else
                 ("Pocket obscured by fetal parts", fluid(37, annotate=False)
                  + shade("M117 12L179 11L256 149H168Z") + label(130, 143, "No reliable endpoint")),
                 measurement=f"DVP {pocket / 10:.1f} cm." if pocket else "DVP unavailable after lateral repositioning."),
        ]
        if ac is None:
            views.extend([
                view("Record usable biometry", "Save HC and FL. Posterior shadow removes part of the abdominal circumference. Repeat from a lateral window, retaining the limited view in the record.",
                     ("Axial head", head(hc)), ("Femoral diaphysis", femur(fl)),
                     ("Initial abdominal window", abdomen(270, annotate=False) + shade("M98 13L143 17L206 153H129Z")),
                     ("Repeat lateral window", abdomen(270, annotate=False) + shade("M177 16L215 17L264 147H212Z")),
                     measurement=f"HC {hc} mm; FL {fl} mm. AC and EFW unavailable."),
                view("Compare with previous scan",
                     "Prior weight can be retrieved, but today lacks a complete biometric set. Keep existing dating and defer the interval assessment.",
                     ("Hadlock reference · no current point", growth(prior, None)),
                     measurement=f"Prior EFW {prior} g at 28 wk; no current EFW."),
                view("Attempt clinically indicated Doppler", "Re-angle to a second free cord loop. Motion and poor alignment obscure the diastolic envelope in both samples. The independent acquired image illustrates a clearly resolved envelope.",
                     ("Free-loop gate", cord_gate()),
                     ("Motion-contaminated repeat", doppler(40, 10, annotate=False)
                      + shade("M56 43L77 38L133 151H101Z") + shade("M191 22L219 28L273 151H242Z")),
                     measurement="UA ratio unavailable. End-diastolic flow remains unclassified."),
            ])
            impression = "The current exam does not resolve interval growth, fluid or placental resistance. Document limitations and arrange targeted follow-up."
            limits = "Shadow and motion prevent a valid AC, fluid pocket and waveform in this modeled visit."
            extras = ()
        else:
            efw = fetal_weight(hc, ac, fl)
            is_abnormal = kind == "abnormal"
            description = "below the 3rd percentile (1465 g)" if is_abnormal else "between the 10th and 90th percentile reference values (1621–2285 g)"
            peak, edv = (44, 0) if is_abnormal else (42, 16)
            ratio = ("S/D undefined because EDV is zero."
                     if is_abnormal else f"S/D = {peak} ÷ {edv} = {peak / edv:.2f}.")
            views.extend([
                view("Acquire fetal biometry", "Save the transthalamic outer head ellipse, the abdominal skin-line ellipse at stomach and portal sinus, and the complete visible femur diaphysis.",
                     ("Head circumference", head(hc)), ("Abdominal circumference", abdomen(ac)),
                     ("Femoral diaphysis", femur(fl)),
                     measurement=f"HC {hc} mm; AC {ac} mm; FL {fl} mm."),
                view("Calculate estimated weight and compare",
                     f"Convert lengths to centimetres. Use log₁₀(EFW g) = 1.326 + 0.0107 × HC + 0.0438 × AC + 0.158 × FL − 0.00326 × AC × FL. At 32 wk the result is {description} on Hadlock.",
                     ("Hadlock growth reference", growth(prior, efw)),
                     measurement=f"Prior {prior} g at 28 wk → current {efw} g at 32 wk (change +{efw - prior} g over 4 wk)."),
                view("Sample umbilical artery flow",
                     "Select a free loop with color guidance. Keep the beam aligned to flow, use a low wall filter and save four similar pulses during fetal quiescence."
                     + (" Repeat at a second free-loop site and check the baseline before reporting absent end-diastolic flow. The separate acquired comparison shows forward diastolic flow." if is_abnormal else ""),
                     ("Free-loop gate", cord_gate()),
                     ("Pulsed-wave sample", doppler(peak, edv)),
                     *((("Repeat sample · low wall filter", doppler(43, 0)),) if is_abnormal else ()),
                     measurement=f"PSV {peak} cm/s; EDV {edv} cm/s. {ratio}"),
            ])
            if is_abnormal:
                impression = f"Growth restriction at 32 wk (EFW {efw} g, below the 3rd percentile) with a 1.7-cm fluid pocket and persistent absent umbilical artery end-diastolic flow. Communicate promptly for specialist assessment."
                limits = "The repeat spectrum demonstrates the pattern with simulated signal. Other fetal surveillance findings and management are outside this acquisition."
                extras = (FGR, AEDF)
            else:
                impression = f"Interval growth with EFW {efw} g at 32 wk and fluid pocket 4.6 cm. Umbilical artery flow remains forward in diastole."
                limits = "Two simulated visits demonstrate comparison. The chart shows reference positions at the two sampled weeks."
                extras = (AEDF,)
        records.append(case("late", kind, title,
                            "Singleton visit at 32 weeks by established dating. The referral asks whether interval growth is appropriate.",
                            views, impression, limits, HADLOCK, GROWTH, DOPPLER, *extras))
    return records


def build():
    illustration = Path(__file__).with_name(OMPHALOCELE_ILLUSTRATION["file"])
    illustration_bytes = illustration.read_bytes()
    if sha256(illustration_bytes).hexdigest() != OMPHALOCELE_ILLUSTRATION["sha256"]:
        raise ValueError(f"Unexpected bytes for retained case illustration: {illustration.name}")
    outputs = {illustration.name: illustration_bytes.decode("utf-8")}
    payload = []
    for stage, kind, title, summary, views, impression, limits, sources in (
        early_cases() + first_cases() + mid_cases() + late_cases()
    ):
        identifier = f"pregnancy-{stage}-{kind}"
        case_views = []
        for index, (view_title, caption, panels, measurement) in enumerate(views, start=1):
            image = f"views/{stage}-{kind}-{index:02d}.svg"
            outputs[image] = diagram(view_title, *panels)
            row = {"title": view_title, "image": image, "caption": caption}
            if measurement is not None:
                row["measurement"] = measurement
            refs = REFERENCE_EXCEPTIONS.get((kind, view_title), VIEW_REFERENCES.get(view_title))
            if refs:
                row["referenceIds"] = list(refs)
            if identifier == "pregnancy-mid-abnormal" and view_title == "Assess abdomen and umbilical insertion":
                row["illustration"] = OMPHALOCELE_ILLUSTRATION
            case_views.append(row)
        payload.append({
            "id": identifier, "family": f"pregnancy-{stage}", "title": title,
            "indication": INDICATION[stage], "kind": kind,
            "summary": f"Modeled teaching case. {summary}",
            "views": case_views, "impression": impression, "limitations": limits,
            "sources": [{"title": name, "url": url} for name, url in
                        (PROTOCOL[stage], REFERENCE[stage], *sources)],
        })
    outputs["cases.json"] = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--check", action="store_true", help="Verify checked-in output matches replay")
    args = parser.parse_args()
    outputs = build()
    if args.check:
        mismatches = []
        for relative, contents in outputs.items():
            destination = args.output / relative
            if not destination.is_file() or destination.read_bytes() != contents.encode("utf-8"):
                mismatches.append(relative)
        extra = {path.relative_to(args.output).as_posix() for path in (args.output / "views").glob("*.svg")} - outputs.keys()
        if mismatches or extra:
            parser.exit(1, f"Replay mismatch: {', '.join(mismatches + sorted(extra))}\n")
        print(f"Verified {len(outputs) - 2} schematic images, the retained illustration and cases.json")
        return
    for relative, contents in outputs.items():
        destination = args.output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8")


if __name__ == "__main__":
    main()
