"""Trace the retained ImageGen PNG for the omphalocele review candidate."""

import argparse
from pathlib import Path

import cv2
import numpy as np


PALETTE = {
    "background": (255, 255, 255),
    "abdomen": (253, 221, 178),
    "wall": (221, 133, 97),
    "warm-outline": (176, 78, 57),
    "bowel": (253, 151, 122),
    "sac": (177, 216, 215),
    "membrane": (14, 106, 108),
    "cord": (203, 167, 224),
    "cord-outline": (100, 62, 131),
}
WRAPPER = """\
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1120" viewBox="0 0 1920 1120" role="img" aria-labelledby="title description">
  <title id="title">Fetal omphalocele</title>
  <desc id="description">AI-generated, vector-traced teaching illustration of the modeled mid-trimester case. The fetal anterior abdominal wall opens at the midline. Bowel extends through the opening into a membrane-covered sac. The umbilical cord attaches to the apex of the sac.</desc>
  <defs>
    <linearGradient id="open-neck-fill" gradientUnits="userSpaceOnUse" x1="1148" y1="0" x2="1240" y2="0">
      <stop offset="0" stop-color="#fdddb2"/>
      <stop offset="1" stop-color="#b1d8d7"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1120" fill="#fff"/>
  <g id="heading" fill="#172e3e" font-family="system-ui, sans-serif">
    <text x="76" y="87" font-size="59" font-weight="700">Fetal omphalocele</text>
    <text x="78" y="137" font-size="30">AI-generated teaching illustration · Modeled mid-trimester transverse section</text>
  </g>
  <g id="anatomy" transform="translate(0 169)">
{anatomy}
  </g>
  <g id="leaders" fill="none" stroke="#263e50" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 1001 509 H 1079 L 1135 537"/>
    <path d="M 1360 328 V 361 L 1374 390"/>
    <path d="M 1193 1001 H 1260 L 1311 733"/>
    <path d="M 1625 870 V 645 L 1598 595"/>
  </g>
  <g id="leader-endpoints" fill="#263e50" stroke="#fff" stroke-width="2">
    <circle cx="1135" cy="537" r="7"/>
    <circle cx="1374" cy="390" r="7"/>
    <circle cx="1311" cy="733" r="7"/>
    <circle cx="1598" cy="595" r="7"/>
  </g>
  <g id="labels" fill="#172e3e" font-family="system-ui, sans-serif" font-size="36" font-weight="600">
    <text id="defect-label" x="984" y="521" text-anchor="end">Midline wall defect</text>
    <text id="membrane-label" x="1360" y="308" text-anchor="middle">Covering membrane</text>
    <text id="bowel-label" x="1177" y="1013" text-anchor="end">Bowel in sac</text>
    <text id="cord-label" x="1625" y="915" text-anchor="middle">Cord inserts on sac apex</text>
  </g>
</svg>
"""


def classify(image):
    """Assign each pixel to a hand-picked material color in CIELAB."""
    pixels = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    palette_bgr = np.array([[color[::-1] for color in PALETTE.values()]], dtype=np.uint8)
    palette_lab = cv2.cvtColor(palette_bgr, cv2.COLOR_BGR2LAB)[0].astype(np.float32)
    delta = pixels[:, :, None, :] - palette_lab
    labels = np.argmin(np.sum(delta**2, axis=3), axis=2).astype(np.uint8)
    labels = cv2.medianBlur(labels, 3)
    return {name: labels == index for index, name in enumerate(PALETTE)}


def curves(mask, *, tolerance=1.7, minimum_area=40):
    """Fit closed cubic paths to the outside and hole contours of a color mask."""
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    paths = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(contour) < minimum_area:
            continue
        points = cv2.approxPolyDP(contour, tolerance, True).reshape(-1, 2).astype(float)
        if len(points) < 4:
            continue
        # Shorten the tangent at tight corners so rounded joins stay within the mask.
        before = points - np.roll(points, 1, axis=0)
        after = np.roll(points, -1, axis=0) - points
        before_length = np.linalg.norm(before, axis=1)[:, None]
        after_length = np.linalg.norm(after, axis=1)[:, None]
        direction = before / before_length + after / after_length
        tangent = direction * np.minimum(before_length, after_length) / 6
        commands = [f"M {points[0, 0]:.0f},{points[0, 1]:.0f}"]
        for i, start in enumerate(points):
            j = (i + 1) % len(points)
            a, b, end = start + tangent[i], points[j] - tangent[j], points[j]
            commands.append(
                f"C {a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {end[0]:.0f},{end[1]:.0f}"
            )
        paths.append(" ".join(commands) + " Z")
    if not paths:
        raise ValueError("Expected an anatomical contour in every trace layer")
    return " ".join(paths)


def trace(image):
    masks = classify(image)
    y, x = np.ogrid[:819, :1920]
    bowel_area = (x > 919) & ((x > 1173) | ((y > 352) & (y < 518)))
    bowel_edge = masks["warm-outline"] & bowel_area
    bowel = masks["bowel"] & (bowel_area | (x > 1173))
    lateral_wall = (masks["warm-outline"] & ~bowel_area) | (masks["wall"] & ~bowel_area)
    # Close the traced colored regions beneath adjacent artwork to avoid white seams.
    neck_overlap = (x >= 1135) & (x <= 1164) & (y >= 328) & (y <= 540)
    abdomen = lateral_wall | masks["abdomen"] | ((bowel | bowel_edge) & (x <= 1154)) | neck_overlap
    sac = masks["sac"] | masks["membrane"] | ((bowel | bowel_edge) & (x >= 1146))
    membrane = masks["membrane"] & (x >= 1155)
    # The generated image draws a vertical teal line across the neck. Only trace
    # the external membrane above, and blend the two interior fills at the opening.
    layers = (
        ("abdominal-cavity", (("cavity-fill", "#fdddb2", abdomen, 2.2, 1000),)),
        ("sac-membrane", (
            ("sac-interior", "url(#open-neck-fill)", sac, 1.3, 160),
            ("membrane-contour", "#086b6c", membrane, 1.1, 100),
        )),
        ("abdominal-wall", (
            ("wall-edge", "#a34e39", lateral_wall, 1.4, 100),
            ("wall-fill", "#dd8561", masks["wall"] & ~bowel_area, 1.4, 80),
        )),
        ("herniated-bowel", (
            ("bowel-silhouette", "#ad4538", bowel | bowel_edge, 1.25, 180),
            ("bowel-fill", "#fa9679", bowel, 1.2, 100),
        )),
        ("umbilical-cord", (
            ("cord-edge", "#643e83", masks["cord"] | masks["cord-outline"], 1.2, 90),
            ("cord-fill", "#cba7e0", masks["cord"], 1.2, 80),
        )),
    )
    artwork = []
    for group, items in layers:
        artwork.append(f'    <g id="{group}">')
        for name, fill, mask, tolerance, area in items:
            path = curves(mask, tolerance=tolerance, minimum_area=area)
            artwork.append(f'      <path id="{name}" fill="{fill}" fill-rule="evenodd" d="{path}"/>')
        artwork.append("    </g>")
    return WRAPPER.format(anatomy="\n".join(artwork))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    image = cv2.imread(str(args.source))
    if image is None or image.shape != (819, 1920, 3):
        parser.error("source must be the 1920 × 819 ImageGen raster")
    args.output.write_text(trace(image), encoding="utf-8")


if __name__ == "__main__":
    main()
