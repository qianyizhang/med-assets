"""Build the modeled organ sections and their visit records."""
import argparse
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGES = {}


def path(d, fill, stroke="#9a9992", width=1.4):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def oval(x, y, rx, ry, fill, stroke="#a5a39a"):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'


def view(key, title, caption, tissue, labels, scale=2, calipers=(), linear=False, orientation=None):
    image = f"images/{key}.svg"
    measurements = []
    marks = []
    for axis, (x1, y1), (x2, y2) in calipers:
        length = ((x2-x1)**2 + (y2-y1)**2)**0.5 / scale
        measurements.append(f"{axis} {f'{length:.1f}'.removesuffix('.0')} mm")
        marks.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="#facd71" stroke-dasharray="4 4"/>')
        for x, y in [(x1, y1), (x2, y2)]:
            marks.append(f'<path d="M{x-4} {y}h8 M{x} {y-4}v8" stroke="#facd71" stroke-width="1.5"/>')
    for label, (x, y), (tx, ty) in labels:
        marks.append(f'<path d="M{x} {y}L{tx} {ty-4}" stroke="#68e3ca" opacity=".8"/>'
                     f'<circle cx="{x}" cy="{y}" r="2.5" fill="#68e3ca"/>'
                     f'<text x="{tx+4}" y="{ty}" font-size="12" fill="#a3f5e2" stroke="#131820" '
                     f'stroke-width="4" paint-order="stroke">{escape(label)}</text>')
    ruler = []
    tick_mm = 5 if scale >= 5 else 20
    for mm in range(tick_mm, int(242 / scale), tick_mm):
        y = 62 + mm * scale
        ruler.append(f'<path d="M624 {y}h8" stroke="#adb6c1"/>'
                     f'<text x="639" y="{y+4}" font-size="11">{mm}</text>')
    field = "M78 62H590V305H78Z" if linear else "M266 62Q334 42 402 62L608 272Q334 350 60 272Z"
    orientation = orientation or ("Linear section" if linear else "Curvilinear section")
    IMAGES[image] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 338" font-family="system-ui,sans-serif" fill="#adb6c1" role="img" aria-label="{escape(title)}">
<defs>
  <clipPath id="field"><path d="{field}"/></clipPath>
  <linearGradient id="gain" x2="0" y2="1"><stop stop-color="#777774"/><stop offset=".55" stop-color="#454642"/><stop offset="1" stop-color="#202020"/></linearGradient>
  <filter id="speckle" x="0%" y="0%" width="100%" height="100%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency=".39 .67" numOctaves="2" seed="37"/><feColorMatrix type="saturate" values="0"/></filter>
</defs>
<rect width="680" height="338" fill="#10151c"/>
<text x="30" y="29" font-size="12" fill="#dce6ec">MODELED SECTION</text><text x="650" y="29" text-anchor="end" font-size="12">{escape(orientation)}</text>
<g clip-path="url(#field)"><rect x="50" y="50" width="570" height="265" fill="url(#gain)"/>
{tissue}
<rect x="50" y="50" width="570" height="265" filter="url(#speckle)" opacity=".25" style="mix-blend-mode:soft-light"/>
</g><path d="{field}" fill="none" stroke="#52636b"/>
<text x="633" y="59" font-size="10">mm</text>{''.join(ruler)}{''.join(marks)}
</svg>
'''
    record = {"title": title, "image": image, "caption": caption}
    if measurements:
        record["measurement"] = " · ".join(measurements)
    return record


PRACTICE_ABD = ("AIUM · Abdomen or retroperitoneum practice parameter", "https://doi.org/10.1002/jum.70430")
ACQ_ABD = ("Acquired normal hepatobiliary and pancreatic landmarks · Okaniwa et al., Fig. 1", "https://doi.org/10.1007/s10396-022-01272-w")
ACQ_RENAL = ("Acquired right and left kidneys · Yadav et al., Figs. 4–6", "https://www.mdpi.com/2075-4418/15/24/3208")
ACQ_SPLEEN = ("Acquired long-axis spleen · Demissie et al., Fig. 1", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8642847/#Fig1")
PRACTICE_THY = ("AIUM · Extracranial head and neck practice parameter", "https://www.aium.org/docs/default-source/resources/guidelines/extracranial_head_neck.pdf")
ACQ_THY = ("Acquired normal lobes and isthmus · Choi, Fig. 1", "https://clinicalultrasound.org/upload/pdf/cu-8-1-7.pdf#page=3")
TIRADS = ("ACR · TI-RADS assessment system", "https://www.acr.org/clinical-resources/clinical-tools-and-reference/reporting-and-data-systems/ti-rads")
BIRADS = ("ACR · Breast ultrasound reporting and BI-RADS assessment", "https://accreditationsupport.acr.org/support/solutions/articles/11000067043-reporting-breast-ultrasound")
ACQ_NIPPLE = ("Acquired nipple and duct landmarks · Chiorean et al., Fig. 1", "https://doi.org/10.3348/kjr.2019.0831")
ACQ_AXILLA = ("Acquired normal and abnormal nodes · Chang et al., NAUTILUS protocol, Fig. 1", "https://doi.org/10.4048/jbc.2021.24.e47")


def case(id_, family, kind, title, indication, summary, views, impression, limits, sources):
    return {
        "id": id_, "family": family, "kind": kind, "title": title, "indication": indication,
        "summary": summary, "views": views, "impression": impression,
        "limitations": "Fictional visit. Measurements come from the modeled sections. " + limits,
        "sources": [{"title": title, "url": url} for title, url in sources],
    }


LIVER = path("M98 141Q187 79 272 66Q371 54 481 108Q530 145 545 184Q493 253 291 268Q162 252 98 198Z", "#797a75")
GB_LONG = path("M220 162Q235 146 279 158Q325 180 377 173Q397 168 411 184Q381 199 352 197Q281 203 228 185Q214 178 220 162Z", "#101111", "#dbdcd5", 3)
SPLEEN = path("M183 207Q219 107 320 119Q377 116 403 148Q371 205 278 224Q221 235 183 207Z", "#888880")
BOWEL = path("M180 109Q233 103 273 130Q302 153 341 147Q387 128 436 157L449 171Q390 143 341 166Q303 172 266 146Q227 120 180 126Z", "#dfdcd2", "#eee9d9")
SHADOW = path("M184 126Q227 120 266 146Q303 172 341 166Q390 143 449 171L523 305H112Z", "#181b1c", "none")
DUCT = path("M269 146Q327 138 382 162L381 170Q328 146 269 154Z", "#101319", "#c5c5ac")
PORTAL = path("M220 176Q302 161 397 187L398 209Q306 185 219 197Z", "#222622", "#e2e1c9", 2)


def liver_view():
    return view("abd-liver", "Right hepatic lobe and portal branches",
                "Sweep both lobes in long and transverse planes. Document the right lobe span and portal branches. In the modeled color and spectral sample, main portal flow is hepatopetal.",
                LIVER + path("M247 217Q296 197 344 201L413 170L420 179L365 213L427 233L420 239L343 218Q303 214 249 230Z", "#232523", "#dad9c7", 2)
                + ''.join(oval(x, y, 7, 3, "#d5815d" if x % 2 else "#ba6850", "none") for x, y in [(286, 216), (302, 212), (326, 209), (350, 209), (367, 201), (385, 192)]),
                [("Right lobe", (255, 143), (140, 132)), ("Portal flow overlay", (355, 211), (380, 247))],
                calipers=[("Craniocaudal span", (201, 86), (463, 207))], scale=2,
                orientation="Long axis · right subcostal")


def gallbladder(key, title, caption, stone_x=None):
    stone = ""
    if stone_x:
        x = stone_x
        y = 181 if x < 300 else 187
        stone = path(f"M{x-9} {y}L{x+9} {y}L{x+23} 287H{x-9}Z", "#131415", "none")
        stone += path(f"M{x-9} {y}Q{x} {y-13} {x+9} {y}", "#fef9e3", "#fef9e3", 2)
    labels = [("Gallbladder lumen", (318, 176), (351, 122)), ("Liver", (286, 116), (218, 97))]
    if stone_x:
        labels.append(("Dependent stone + shadow", (stone_x, 190), (118 if stone_x < 300 else 415, 239)))
    return view(key, title, caption, LIVER + GB_LONG + stone, labels,
                scale=3, calipers=[("Anterior wall", (260, 151), (260, 157))])


def bile_duct():
    return view("abd-cbd", "Porta hepatis and extrahepatic duct",
                "Follow the duct along the portal vein. The duct walls are sampled inner edge to inner edge. In the modeled color check, flow fills the portal vein while the duct remains unfilled.",
                LIVER + PORTAL + DUCT + ''.join(oval(x, y, 9, 4, "#a97660", "none") for x, y in [(256, 183), (278, 180), (300, 179), (322, 182), (345, 184), (368, 189)]),
                [("Extrahepatic duct", (333, 152), (354, 119)), ("Main portal vein", (352, 187), (390, 232))],
                scale=2, calipers=[("Duct lumen", (312, 145), (312, 153))])


def kidney(key, side, length, enlarged=False, short=False, postvoid=False):
    cx, cy = 331, 186
    width = 54 if short else length
    cortex = oval(cx, cy, width, 40 if short else 42, "#535750")
    sinus = oval(cx+6, cy, width*.90 if short else width*.66, 23 if short else 22, "#c7c5b8", "none")
    fluid = path("M278 174Q303 168 310 177Q321 183 336 178Q349 176 361 162L372 165Q366 182 352 192L370 201L362 211Q344 201 333 198Q316 198 306 210L297 200L308 189Q297 187 281 192Z", "#0b0d12", "none") if enlarged else ""
    if enlarged and short:
        fluid = path("M301 178L319 173L328 182L350 172L360 183L345 190L356 201L346 208L329 197L315 202L309 191L296 190Z", "#0b0d12", "none")
    caption = "Branching fluid separates the bright sinus echoes in the pelvis and calyces." if enlarged else "Cortex surrounds a bright central sinus without visible collecting-system dilatation."
    labels = [("Cortex", (331, 151), (347, 118)), ("Dilated pelvis and calyces" if enlarged else "Renal sinus", (337, 190), (393, 238))]
    if postvoid:
        caption += " After voiding, the right collecting system remains dilated, with the same appearance as on the prevoid section."
    return view(key, f"{side} kidney · {'short' if short else 'long'} axis" + (" postvoid" if postvoid else ""), caption, cortex + sinus + fluid, labels,
                calipers=[] if short else [("Pole-to-pole", (cx-width,cy), (cx+width,cy))])


def bladder():
    tissue = path("M228 139Q333 120 437 139L424 217Q335 246 246 214Z", "#0e1012", "#c9ccbe", 3)
    return view("renal-bladder", "Urinary bladder · transverse",
                "Survey the distended bladder in transverse and sagittal planes and inspect both UVJs. No distal stone or UVJ mass is demonstrated in the modeled views.",
                tissue, [("Bladder lumen", (345, 180), (393, 116)), ("Posterolateral UVJ region", (399, 217), (436, 245))])


def pancreas(key, tail=False, limited=False):
    tissue = path("M227 163Q277 141 318 151Q363 164 428 155L451 172Q414 193 370 187Q332 181 303 179Q270 186 227 181Z", "#9b9a8c")
    vessel = oval(356, 192, 59, 11, "#191c1c")
    if tail:
        tissue = SPLEEN + path("M331 183Q368 181 414 158L431 155L438 175Q403 196 341 203Z", "#beb8a5")
    if limited:
        return view(key, "Pancreatic window · bowel gas",
                    "The bright gas interface casts obscuring artifact over the body and tail. Left lateral positioning and deep inspiration improve the near field but fail to recover the target.",
                    tissue + vessel + SHADOW + BOWEL, [("Gas interface", (280, 156), (128, 108)), ("Obscured target", (347, 193), (370, 239))])
    return view(key, "Pancreatic tail through the splenic window" if tail else "Pancreatic head and body",
                "From the splenic window, follow the pancreatic tail toward the hilum." if tail else "Pan across head, uncinate region and body with the splenic vein along the posterior body as a landmark.",
                tissue + ("" if tail else vessel),
                [("Spleen", (256, 168), (176, 121)), ("Pancreatic tail", (383, 185), (402, 129))] if tail else [("Pancreas", (299, 168), (264, 110)), ("Splenic vein", (380, 193), (405, 236))])


def vessels():
    tissue = oval(283, 170, 22, 18, "#141818", "#d9d9c9") + oval(371, 174, 26, 12, "#20221d", "#9f9e89")
    tissue += oval(323, 226, 48, 17, "#b0aa93") + path("M277 236H369L392 303H246Z", "#111315", "none")
    return view("abd-vessels", "Abdominal aorta and IVC · transverse",
                "Trace the abdominal aorta in short and long axes. The depicted AP measurement is from the widest modeled segment. Scan the IVC through its hepatic segment and inspect patency.",
                tissue, [("Aorta", (282, 163), (213, 122)), ("IVC", (368, 173), (408, 134)), ("Vertebra", (321, 224), (405, 242))],
                calipers=[("Aorta outer-wall AP", (283, 152), (283, 188))])


def thyroid_lobes():
    lobes = oval(229, 157, 62, 45, "#8c8e84") + oval(437, 157, 57, 42, "#8c8e84")
    isthmus = path("M277 126Q335 114 388 130L388 148Q332 131 277 144Z", "#8c8e84")
    trachea = path("M278 165Q329 137 383 165L397 286H265Z", "#141714", "none")
    air = path("M278 165Q329 137 383 165", "none", "#efede2", 4)
    strap = path("M102 102Q210 78 324 103Q448 80 558 104L548 117Q441 96 325 117Q207 96 113 118Z", "#454a46")
    carotids = oval(143, 173, 18, 18, "#101414") + oval(527, 173, 18, 18, "#101414")
    return strap + lobes + isthmus + trachea + air + carotids


def thyroid_axial(level='middle'):
    return view("thyroid-axial" if level == "middle" else "thyroid-axial-superior",
                "Both lobes and the isthmus · transverse" if level == "middle" else "Superior transverse overview · above the right nodule",
                "Sweep transversely from upper to lower poles. Record each lobe's AP and transverse dimensions and the midline isthmus AP thickness."
                if level == "middle" else "This plane lies superior to the index nodule. Continue caudally through the right mid lobe to the dedicated lesion views.",
                thyroid_lobes(),
                [("Right lobe", (224, 154), (146, 235)), ("Left lobe", (435, 154), (448, 235)),
                 ("Isthmus", (327, 125), (309, 83)), ("Trachea", (334, 151), (303, 224)), ("Carotid", (528, 175), (500, 214))],
                linear=True, scale=6, calipers=[("Right W", (167, 157), (291, 157)), ("Right AP", (229, 112), (229, 202)),
                    ("Left W", (380, 157), (494, 157)), ("Left AP", (437, 115), (437, 199)),
                    ("Isthmus AP", (335, 121), (335, 139))], orientation="Transverse · patient right at screen left")


def thyroid_long(side, key, half_length, limited=False, nodule=False):
    ap_half = 45 if side == "Right" else 42
    tissue = oval(334, 155, half_length, ap_half, "#84867e")
    tissue += path("M120 101Q335 77 550 101L552 114Q336 94 119 114Z", "#434842")
    if nodule:
        tissue += oval(340, 155, 42, 33, "#555852", "#999a90")
    if limited:
        tissue += path("M384 93L405 91L485 305H385Z", "#12161a", "none")
        tissue += path("M383 93L406 91", "none", "#f4ecda", 5)
    return view(key, f"{side} lobe · longitudinal" + (" reattempt" if limited else ""),
                "With gentle extension and an angled suprasternal approach, the lower pole remains hidden by a clavicular shadow. Full length is unrecordable."
                if limited else "Sweep medially and laterally. The maximal longitudinal section includes both poles and closes the three-dimensional lobe record.",
                tissue, [("Clavicular shadow", (420, 222), (429, 241)), ("Visible lobe", (251, 156), (171, 214))]
                if limited else [("Superior pole", (334-half_length, 155), (123, 218)), ("Inferior pole", (334+half_length, 155), (460, 216))]
                + ([("Index nodule", (340, 169), (311, 230))] if nodule else []),
                linear=True, scale=6, calipers=[] if limited else [("Lobe length", (334-half_length, 155), (334+half_length, 155))],
                orientation="Longitudinal · cranial at screen left")


def neck_node():
    return view("thyroid-node", "Cervical node survey · representative lateral level III",
                "Scan the central and lateral compartments bilaterally. This lateral node retains an elongated shape and echogenic fatty hilum. No suspicious node is seen on the completed modeled survey.",
                oval(334, 170, 48, 15, "#555952") + oval(334, 170, 27, 6, "#b9b9a5") + oval(412, 147, 31, 21, "#151816"),
                [("Fatty hilum", (330, 170), (260, 227)), ("Jugular vein", (415, 146), (423, 115))],
                linear=True, scale=6, calipers=[("Short axis", (334, 155), (334, 185))])


def thyroid_nodule(long=False):
    background = oval(330, 161, 160 if long else 89, 80, "#96968a") + path("M130 83Q330 73 528 83L525 109Q325 94 130 108Z", "#444940")
    radius = 42 if long else 24
    nodule = oval(330, 160, radius, 33, "#555852", "#999a90")
    caption = "Record maximum craniocaudal extent in the right mid lobe." if long else "Solid (2), hypoechoic relative to thyroid (2), AP greater than width (3), smooth margin (0), and no echogenic foci (0). The strap muscle is darker than the nodule."
    return view("thyroid-nodule-long" if long else "thyroid-nodule-trans", f"Right mid-lobe nodule · {'longitudinal' if long else 'transverse'}",
                caption, background+nodule,
                [("Solid nodule", (351, 183), (388, 222)), ("Thyroid tissue", (275, 157), (153, 259)), ("Strap muscle", (299, 96), (207, 123))],
                linear=True, scale=6, calipers=[("Length" if long else "Width", (330-radius, 160), (330+radius, 160))]
                    + ([] if long else [("AP", (330, 127), (330, 193))]))


BREAST = (
    path("M74 81Q328 74 593 81L593 90Q322 86 74 92Z", "#c5c3bc", "#dfdcd0", 2)
    + path("M74 92Q337 91 595 90L595 139Q462 162 354 120Q210 165 74 138Z", "#656861", "none")
    + path("M74 143Q165 153 217 128Q280 107 354 128Q455 168 595 141L595 222Q473 209 396 236Q280 244 201 218Q129 208 74 226Z", "#87877c", "#acac99")
    + path("M74 252Q261 237 418 252Q497 259 594 249L594 263Q530 271 418 266Q237 249 74 268Z", "#d4d0bd", "#e3e0cb")
    + path("M74 268Q234 249 418 266Q530 271 594 263L594 305H74Z", "#42463f", "none")
)
DUCT_BREAST = path("M302 98Q318 141 431 198L437 207Q320 153 299 105Z", "#232723", "#c2c0ad")


def frame_breast(side, key, band):
    index = ["Upper breast and axillary tail", "Central breast and nipple", "Lower breast and inframammary fold"].index(band)
    fat = oval([211, 278, 424][index], 150, 53, 16, "#71726a", "none")
    return view(key, f"{side} breast · {band.lower()}",
                "Representative frame from overlapping medial-to-lateral passes. Track each band from skin to chest wall, including the full medial and lateral margins. "
                + ["Extend the upper pass through the axillary tail.", "Angle through the nipple shadow from both directions.", "Continue to the inframammary fold and overlap the adjacent band."][index],
                BREAST + fat + (DUCT_BREAST if index == 1 else ""),
                [("Fibroglandular tissue", (354, 183), (196, 209)), ("Pectoral fascia", (427, 254), (448, 290))],
                linear=True, scale=5, orientation=f"{side} breast · screening pass")


def retroareolar(radial=True, limited=False):
    tissue = BREAST + DUCT_BREAST
    labels = [("Nipple", (302, 86), (252, 112))]
    if limited:
        tissue += path("M293 88Q304 80 315 88L363 270H273Z", "#141717", "none")
        labels.append(("Persistent shadow", (309, 180), (360, 217)))
        return view("breast-retro-limited", "Left retroareolar window · incomplete",
                    "Angle around the nipple, add gel and repeat with light peripheral compression. Pain stops the reattempt before the shadowed zone can be assessed in both planes.",
                    tissue, labels, linear=True, scale=5)
    radius = 30 if radial else 25
    tissue += path("M326 180H390L400 248Q361 253 325 244Z", "#a7a99a", "none")
    tissue += oval(358, 162, radius, 20, "#080b0b", "#d9d6c3")
    labels += [("Simple cyst", (362, 163), (412, 143)), ("Posterior enhancement", (365, 215), (420, 226))]
    return view("breast-cyst-radial" if radial else "breast-cyst-anti",
                f"Left 12 o’clock, 1 cm from nipple · {'radial' if radial else 'antiradial'}",
                "The same circumscribed, anechoic oval lesion is visible in the orthogonal plane. Posterior enhancement and absence of internal echoes support a simple cyst.",
                tissue, labels, linear=True, scale=5,
                calipers=[("Length" if radial else "Width", (358-radius, 162), (358+radius, 162))]
                    + ([("AP", (358, 142), (358, 182))] if radial else []))


def axilla(key, normal=False, short=False):
    width, height = (55, 23) if short else (70, 26)
    if normal:
        width, height = 65, 20
    cortex = oval(332, 168, width, height, "#4a4d43")
    hilum = oval(325, 171, 30 if short else 41, 9 if normal else 7, "#ccbea6", "none")
    vessels_ = oval(463, 210, 33, 11, "#222627", "#9ba195")
    hilar = path("M325 171L317 174L305 175", "none", "#f29769", 3)
    peripheral = path("M363 156Q367 147 381 149M351 151L358 147", "none", "#719ff0", 3) if not normal else ""
    return view(key, f"{'Left' if normal else 'Right'} level I axilla · {'short' if short else 'long'} axis",
                "A contralateral morphology comparison in the visit shows a thin cortex and preserved fatty hilum." if normal else
                "The palpable right level I node is oval with a retained but displaced hilum and focal eccentric cortical thickening. The modeled color overlay shows hilar and peripheral flow when the node is sampled.",
                path("M78 106Q323 83 590 108L590 122Q323 103 78 120Z", "#8d8b80") + vessels_ + cortex + hilum + hilar + peripheral,
                [("Fatty hilum", (321, 174), (218, 227)), ("Thin uniform cortex" if normal else "Eccentric cortex", (348, 153), (365, 127)),
                 ("Axillary vessel", (462, 212), (435, 250))],
                linear=True, scale=5,
                calipers=[("Cortex", (325, 148 if normal else (145 if short else 142)), (325, 162 if normal else 164))]
                    + ([] if normal else [("Short axis", (332, 145), (332, 191))] if short
                       else [("Length", (332-width, 168), (332+width, 168))]))


def spleen():
    return view("abd-spleen", "Spleen · long axis",
                "Use the left posterior intercostal window. Sweep from pole to pole and through the hilum, then rotate to record the short axis.",
                SPLEEN, [("Splenic parenchyma", (286, 164), (175, 134)), ("Hilum", (351, 193), (383, 236))],
                calipers=[("Maximal span", (183, 207), (403, 148))], scale=2)


def gallbladder_short():
    return view("abd-gb-short", "Gallbladder neck · short axis",
                "Fan from neck to fundus and use a left lateral repeat to look for dependent material. The lumen remains anechoic and the wall remains thin.",
                LIVER + oval(335, 187, 49, 22, "#101111", "#e0ded3"),
                [("Anechoic lumen", (333, 181), (350, 144)), ("Anterior wall", (321, 166), (229, 130))])


def bladder_sagittal():
    tissue = path("M216 153Q274 125 404 154Q409 183 362 228Q270 231 228 197Z", "#101215", "#bcbeb0", 3)
    return view("renal-bladder-sagittal", "Urinary bladder · sagittal",
                "Confirm bladder configuration in the orthogonal plane and inspect the posterior wall. In this modeled visit, the right-sided collecting-system dilatation remains after voiding.",
                tissue, [("Posterior wall", (333, 225), (395, 253)), ("Lumen", (299, 179), (317, 116))])


def left_liver():
    tissue = path("M118 220Q225 76 416 102L512 168Q444 206 350 214Q215 238 118 220Z", "#838479")
    tissue += path("M218 192Q294 169 346 172L424 149L434 158L349 186Q279 182 218 205Z", "#2c3028", "#e0dbca")
    return view("abd-left-liver", "Left hepatic lobe · subxiphoid window",
                "Sweep the thin lateral tip and medial segment. The echogenic-walled left portal branch helps orient the section.",
                tissue, [("Left lobe", (261, 147), (164, 125)), ("Left portal branch", (345, 178), (371, 237))])


def hepatic_flow(hepatic_vein):
    key = "hepatic-vein" if hepatic_vein else "portal"
    upper = path("M256 103Q339 91 423 114L417 127Q344 107 259 117Z", "#1c211f", "#c6c8b4", 2)
    color = "".join(oval(x, y, 8, 4, "#dd8451" if hepatic_vein else "#6f9aff", "none")
                    for x, y in [(290, 109), (308, 106), (326, 106), (344, 108), (362, 109), (380, 113)])
    trace = ("M133 238 C151 239 162 218 178 207 S200 224 214 244 S230 252 249 236 "
             "S272 198 284 211 S310 251 327 243 S350 216 365 209 S386 227 397 246 "
             "S417 246 432 233 S454 201 467 210 S493 243 523 234") if hepatic_vein else (
             "M133 220 C167 228 174 211 203 215 S242 229 267 220 S320 210 355 220 "
             "S392 231 414 218 S453 212 480 222 S510 228 523 219")
    graph = '<rect x="124" y="180" width="411" height="98" fill="#161819" stroke="#686e6b"/>'
    graph += path("M128 235H531", "none", "#78817e")
    graph += path(trace, "none", "#eee7d2", 2)
    graph += '<text x="134" y="200" font-size="11" fill="#cbd4cc">Illustrative spectral sample</text>'
    graph += '<text x="513" y="267" font-size="11" fill="#cbd4cc">time</text>'
    return view(f"abd-{key}-doppler", "Hepatic vein · color and spectral sample" if hepatic_vein else "Main portal vein · color and spectral sample",
                "Trace the hepatic vein into the IVC. The illustrative spectral trace depicts pulsatile, predominantly outflow phasicity with a brief reversal near the baseline."
                if hepatic_vein else "Confirm the direction of flow relative to the liver and the probe. The trace shows continuous hepatopetal flow in this modeled position.",
                upper + color + path("M335 102l19 14m-23-7l21 14", "none", "#f8d48a", 2) + graph,
                [("Sample gate", (345, 114), (370, 151))], linear=True, scale=5,
                orientation="Illustrative Doppler · qualitative trace")


def breast_coverage():
    silhouette = "M90 115Q174 82 221 101Q274 84 299 125Q319 184 281 232Q234 271 168 249Q108 232 88 190Z"
    outline = path(silhouette, "#234440", "#9ce3d2", 2)
    band = [
        ("M102 137Q176 102 271 129", "#c8a769"),
        ("M99 158Q194 125 285 149", "#c8a769"),
        ("M102 180Q194 153 289 175", "#75cbb8"),
        ("M114 199Q203 173 281 195", "#75cbb8"),
        ("M130 217Q201 195 269 214", "#9eb8d9"),
        ("M146 232Q211 213 251 227", "#9eb8d9"),
    ]
    one_side = outline + ''.join(path(d, "none", color, 5) for d, color in band)
    one_side += oval(200, 172, 8, 8, "#eff5ec") + path("M112 138L92 110L73 98", "none", "#c8a769", 5)
    key = "images/breast-screen-map.svg"
    IMAGES[key] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 338" font-family="system-ui,sans-serif" role="img" aria-label="Mirrored breast coverage map with overlapping sweeps">
<rect width="680" height="338" fill="#10151c"/>
<g fill="#dfede5" font-size="13"><text x="30" y="29">PROBE COVERAGE PLAN</text><text x="180" y="74">Patient right</text><text x="427" y="74">Patient left</text></g>
{one_side}<g transform="translate(680) scale(-1 1)">{one_side}</g>
<g font-size="13"><text x="31" y="297" fill="#c8a769">Upper bands + axillary tails</text><text x="250" y="297" fill="#75cbb8">Central bands + nipples</text><text x="460" y="297" fill="#9eb8d9">Lower bands + folds</text></g>
</svg>
'''
    return {"title": "Bilateral whole-breast coverage plan", "image": key,
            "caption": "Each line marks a probe pass. Overlap adjacent footprints and work to the peripheral margins, extending the superior passes to the axillary tails. The saved sections below show one depth checkpoint from each band."}


def build_cases():
    cases = []
    abd_liver, abd_duct = liver_view(), bile_duct()
    gb = gallbladder("abd-gb", "Gallbladder · long axis", "Trace the dependent wall, neck and fundus. In the modeled visit, probe pressure does not elicit focal tenderness.")
    kidney_r = kidney("abd-right-kidney", "Right", 107)
    kidney_l = kidney("abd-left-kidney", "Left", 113)
    kidney_r_short = kidney("abd-right-kidney-trans", "Right", 107, short=True)
    kidney_l_short = kidney("abd-left-kidney-trans", "Left", 113, short=True)
    cases.append(case("abdomen-survey", "abdomen", "normal", "Comprehensive abdominal survey",
        "Intermittent nonspecific upper abdominal discomfort. Assess abdominal organs, biliary tract and major vessels.",
        "The visit samples the liver, gallbladder, extrahepatic duct, pancreas, spleen, both kidneys, aorta and IVC. Save the measurements and resolve blind spots from alternate windows.",
        [abd_liver, left_liver(), hepatic_flow(False), hepatic_flow(True), gb, gallbladder_short(), abd_duct, pancreas("abd-pancreas"), pancreas("abd-tail", tail=True), spleen(), kidney_r, kidney_r_short, kidney_l, kidney_l_short, vessels()],
        "No sonographic explanation for the reported discomfort in the modeled survey. No gallstones, ductal dilatation, hydronephrosis or focal abnormality in the documented organs.",
        "Sections illustrate acquisition checkpoints. Grayscale and color are authored. The spectral figures are direction-of-flow illustrations.",
        [PRACTICE_ABD, ACQ_ABD, ACQ_RENAL, ACQ_SPLEEN]))
    cases.append(case("abdomen-biliary-stone", "abdomen", "abnormal", "Focused biliary exam · mobile stone",
        "Episodic postprandial right upper quadrant pain. Look for a gallstone and evidence of complication.",
        "At the first stop, an echogenic focus lies against the dependent wall and casts a shadow. Roll the patient onto the left side and rescan. The focus has shifted within the lumen and the wall remains thin.",
        [gallbladder("biliary-stone-supine", "Gallbladder · supine", "A bright dependent focus casts a clean posterior shadow. Inspect the surrounding fluid and anterior wall.", 360),
         gallbladder("biliary-stone-roll", "Gallbladder · left lateral decubitus repeat", "The echogenic focus has shifted away from the neck and still casts a shadow. Focal probe tenderness is absent in this visit.", 269), abd_duct],
        "Mobile cholelithiasis. No wall thickening, pericholecystic fluid, focal sonographic Murphy sign or duct dilatation in the modeled exam.",
        "Position and stone displacement are authored snapshots. The duct sample is proximal. The distal duct is only partly visible.",
        [PRACTICE_ABD, ("Acquired nonimpacted cholelithiasis clip · Bowra et al., The POCUS Atlas", "https://images.squarespace-cdn.com/content/v1/58118909e3df282037abfad7/1501699786061-K06INXJGQ9IPQB3MRVKG/ezgif.com-gif-maker.gif"), ACQ_ABD]))
    cases.append(case("abdomen-renal-obstruction", "abdomen", "abnormal", "Focused renal and bladder exam · right hydronephrosis",
        "Acute right flank pain. Assess the kidneys and bladder for evidence of urinary tract obstruction.",
        "Survey both kidneys in orthogonal planes. The right collecting system remains dilated on the postvoid recheck. The bladder is sufficiently filled for the prevoid survey.",
        [kidney("renal-right-hydro", "Right", 112, enlarged=True),
         kidney("renal-right-hydro-trans", "Right", 112, enlarged=True, short=True), kidney_l, kidney_l_short, bladder(), bladder_sagittal(), kidney("renal-right-postvoid", "Right", 112, enlarged=True, postvoid=True)],
        "Right hydronephrosis with preserved cortical thickness. No obstructing calculus is visualized. The level and cause of the dilatation are undetermined.",
        "The ureter cannot be traced throughout. The prevoid and postvoid views preserve right renal geometry to depict the persistent finding.",
        [PRACTICE_ABD, ACQ_RENAL, ("Acquired moderate hydronephrosis clip · The POCUS Atlas", "https://images.squarespace-cdn.com/content/v1/58118909e3df282037abfad7/1729635897189-M2B64Q14PMXSLFQDU7P0/image-asset.gif")]))
    cases.append(case("abdomen-limited-pancreas", "abdomen", "limited", "Abdominal survey · pancreas obscured",
        "Epigastric discomfort. Assess the abdominal organs with attention to the pancreas.",
        "The initial epigastric view shows the pancreatic head. Bowel gas obscures the body and tail despite deep inspiration and a left lateral repeat. Complete and report the visible liver, gallbladder, ducts, spleen, kidneys and vessels separately.",
        [pancreas("abd-pancreas-limited", limited=True), abd_liver, gb, abd_duct, spleen(), kidney_r, kidney_l, vessels()],
        "Limited pancreatic assessment. The visualized head is unremarkable. The body and tail remain obscured. The remaining documented organs show no modeled explanation for symptoms.",
        "The obscuration is drawn. The limited target has no dimensions or negative finding assigned.",
        [PRACTICE_ABD, ACQ_ABD]))

    thy_ax, thy_r, thy_l, thy_node = thyroid_axial(), thyroid_long("Right", "thyroid-right-long", 144), thyroid_long("Left", "thyroid-left-long", 132), neck_node()
    cases.append(case("thyroid-normal", "thyroid", "normal", "Thyroid survey · no focal lesion",
        "Suspected enlargement on examination. Evaluate gland size, parenchyma and the relevant cervical nodes.",
        "Measure right and left lobes in transverse and longitudinal views and the isthmus in transverse. Survey the central and lateral neck on both sides.",
        [thy_ax, thy_r, thy_l, thy_node], "Homogeneous thyroid without enlargement or a discrete nodule. No suspicious cervical node in the modeled survey.",
        "Representative frames show middle and maximal planes. Pole sweeps are recorded in the captions.", [PRACTICE_THY, ACQ_THY]))
    cases.append(case("thyroid-nodule", "thyroid", "abnormal", "Right thyroid nodule · TR5",
        "Incidental right thyroid nodule on cross-sectional imaging. Characterize the lesion and relevant cervical nodes.",
        "Survey both lobes and the isthmus, then acquire orthogonal dedicated views of the index lesion in the right mid lobe. The transverse plane establishes its taller-than-wide shape. Document the cervical compartments.",
        [thyroid_axial("superior"), thyroid_long("Right", "thyroid-right-long-nodule", 144, nodule=True), thy_l, thyroid_nodule(), thyroid_nodule(True), thy_node],
        "Right mid-lobe nodule, 14 × 8 × 11 mm (longitudinal × transverse × AP). ACR TI-RADS 5, 7 points. The 14 mm maximum dimension meets the ACR size criterion for FNA. No suspicious cervical node in the modeled survey.",
        "The transverse gland overview is superior to the nodule. Feature scoring and measurements come from the dedicated lesion sections.",
        [PRACTICE_THY, TIRADS, ("Acquired solid hypoechoic taller-than-wide nodule · Pires et al., Fig. 9", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8864691/#f9")]))
    cases.append(case("thyroid-limited", "thyroid", "limited", "Thyroid survey · left inferior pole hidden",
        "Outside imaging describes a possible left inferior-pole nodule. Evaluate its location and morphology.",
        "Use high-frequency transverse and longitudinal views. A mid-gland frame and the right long axis are obtainable. Repeat the left lower-pole view with gentle extension and a lower angled approach.",
        [thy_ax, thy_r, thyroid_long("Left", "thyroid-long-limited", 132, limited=True), thy_node],
        "Left inferior pole obscured on both attempts. The reported target cannot be characterized. Left lobe length and a TI-RADS score for the reported target remain unassigned.",
        "Measurements on the transverse frame refer to the visible mid gland only.", [PRACTICE_THY, TIRADS, ACQ_THY]))

    diagnostic = ("ACR · Diagnostic breast ultrasound practice parameter", "https://gravitas.acr.org/PPTS/GetDocumentView?docId=124")
    screening = ("ACR · Supplemental screening based on breast density", "https://acsearch.acr.org/docs/3158166/Narrative/")
    axilla_ref = ("ACR · Imaging of the axilla", "https://acsearch.acr.org/docs/3158165/Narrative/")
    retro_ref = ("Acquired retroareolar simple cyst · Ferré et al., Fig. 9a", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5295772/#f9")
    bands = ["Upper breast and axillary tail", "Central breast and nipple", "Lower breast and inframammary fold"]
    cases.append(case("breast-supplemental-screening", "breast", "normal", "Bilateral supplemental screening",
        "Asymptomatic patient with heterogeneously dense breasts and negative screening mammography. Supplemental handheld ultrasound selected for this modeled visit.",
        "Cover both breasts with overlapping upper, central and lower bands. Work across each band from medial edge to lateral edge and depth from skin to pectoral fascia. Include both nipples, inframammary folds and axillary tails.",
        [breast_coverage()] + [frame_breast(side, f"breast-screen-{side.lower()}-{i}", band)
                              for side in ("Right", "Left") for i, band in enumerate(bands)],
        "BI-RADS 1. No suspicious finding on the modeled bilateral supplemental ultrasound survey.",
        "One authored section represents each band. This visit does not model population screening performance.",
        [screening, ("ACR · Whole-breast supplemental ultrasound screening", "https://gravitas.acr.org/PPTS/GetDocumentView?docId=61"), BIRADS, ("Acquired normal breast layers · Shah and Jankharia, Fig. 2", "https://doi.org/10.4103/0971-3026.63045"), ACQ_NIPPLE]))
    cases.append(case("breast-retroareolar-cyst", "breast", "abnormal", "Targeted breast exam · retroareolar simple cyst",
        "Palpable tender left retroareolar lump at 12 o’clock. Clarify its mammographic correlate.",
        "Center the finding at 12 o’clock, 1 cm from the nipple. Angle through the near field to separate the lesion from the nipple and duct. Save orthogonal radial and antiradial sections and record three dimensions.",
        [retroareolar(), retroareolar(False)],
        "BI-RADS 2. A 12 × 10 × 8 mm simple cyst corresponds to the palpable and mammographic finding.",
        "The mammographic correlation and absence of internal color flow are assumed visit findings. The displayed sections are grayscale.",
        [diagnostic, BIRADS, ACQ_NIPPLE, retro_ref]))
    cases.append(case("breast-axillary-node", "breast", "abnormal", "Targeted axillary exam · abnormal node",
        "New palpable right axillary lump without an evident infectious or recent vaccination explanation. Diagnostic mammography shows no suspicious breast lesion.",
        "Locate the palpable level I node in long and short axes and measure the thickest cortex perpendicular to its surface. Compare the left axillary morphology and inspect the ipsilateral axillary tail.",
        [axilla("axillary-node-long"), axilla("axillary-node-short", short=True), axilla("axillary-node-opposite", normal=True),
         frame_breast("Right", "axillary-tail-diagnostic", bands[0])],
        "BI-RADS 4. Unexplained unilateral right axillary node with focal cortical thickening and retained hilum. Tissue sampling is recommended in this modeled diagnostic report.",
        "The flow overlay is illustrative and etiology remains undetermined. The breast workup and clinical history are visit assumptions.",
        [BIRADS, axilla_ref, ACQ_AXILLA]))
    cases.append(case("breast-limited", "breast", "limited", "Targeted breast exam · incomplete retroareolar views",
        "Focal left retroareolar pain. The visit ends before a complete targeted assessment can be obtained.",
        "Document the adjacent tissue and attempt to recover the shadowed area with altered angle, gel and light compression. The patient leaves because of pain before orthogonal documentation of the symptomatic site.",
        [frame_breast("Left", "breast-limited-adjacent", bands[1]), retroareolar(limited=True)],
        "BI-RADS 0. Incomplete evaluation of the symptomatic retroareolar region. Complete targeted imaging to assign a final assessment.",
        "There is no measured lesion or presumed negative result for the obscured region.", [diagnostic, BIRADS, ACQ_NIPPLE, retro_ref]))
    landmarks = {
        'abd-liver': ['liver-12'], 'abd-left-liver': ['liver-12'], 'abd-portal-doppler': ['portal-vein-12'],
        'abd-hepatic-vein-doppler': ['hepatic-vein'], 'abd-gb': ['gallbladder-12'], 'abd-gb-short': ['gallbladder-48'],
        'abd-cbd': ['extrahepatic-duct'], 'abd-pancreas': ['pancreas-12', 'pancreas-48'], 'abd-tail': ['pancreatic-tail'],
        'abd-spleen': ['spleen-12'], 'abd-right-kidney': ['kidney-right-12'], 'abd-right-kidney-trans': ['kidney-right-48'],
        'abd-left-kidney': ['kidney-left-12'], 'abd-left-kidney-trans': ['kidney-left-48'], 'abd-vessels': ['aorta-48'],
        'thyroid-axial': ['thyroid-isthmus'], 'thyroid-right-long': ['thyroid-right-48'],
        'thyroid-left-long': ['thyroid-left-48'], 'axillary-node-long': ['axilla-12'],
        'biliary-stone-supine': ['gallbladder-12'], 'breast-cyst-radial': ['breast-48'],
        'renal-right-hydro': ['kidney-right-12'], 'renal-right-hydro-trans': ['kidney-right-48'],
        'breast-screen-right-1': ['breast-12', 'breast-subareolar-12'],
    }
    for record in cases:
        for image_view in record['views']:
            key = Path(image_view['image']).stem
            if key in landmarks:
                image_view['referenceIds'] = landmarks[key]
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare replayed sections and case data with the delivered files")
    check = parser.parse_args().check
    cases = build_cases()
    files = {**IMAGES, "cases.json": json.dumps(cases, indent=2, ensure_ascii=False) + "\n"}
    for relative_name, content in files.items():
        destination = ROOT / relative_name
        if check:
            if not destination.is_file() or destination.read_bytes() != content.encode("utf-8"):
                raise SystemExit(f"Missing or stale case file: {relative_name}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
    extra_images = {str(p.relative_to(ROOT)) for p in (ROOT / "images").glob("*.svg")} - IMAGES.keys()
    if extra_images:
        raise SystemExit(f"Unreferenced images: {', '.join(sorted(extra_images))}")
    print(f"{'Verified' if check else 'Built'} {len(cases)} visits and {len(IMAGES)} modeled sections")


if __name__ == "__main__":
    main()
