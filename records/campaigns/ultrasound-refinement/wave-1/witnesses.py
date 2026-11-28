"""Render matched measurements and live-player crops for the right-kidney trial."""

import argparse
import json
from pathlib import Path

import numpy as np
from measure import dot, mesh, unit_vector
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

BG = "#101820"
WHITE = "#f1f6f9"
MUTED = "#becbd4"
GOLD = "#ffd166"
CYAN = "#6ee4ff"


def font(size):
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def text(canvas, xy, value, size, color=WHITE, anchor=None):
    ImageDraw.Draw(canvas).text(xy, value, font=font(size), fill=color, anchor=anchor)


def mark(draw, xy, color, radius=5):
    x, y = xy
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=BG, width=5)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=color, width=2)


def protected_planes(bundle, output):
    receipt = json.loads((bundle / "reference.json").read_text())
    result = json.loads((bundle / "measurements.json").read_text())
    reference = np.load(bundle / "reference.npz")
    candidate = np.load(bundle / "candidate-sections.npz")
    panel_w, panel_h = 426, 254
    figure = Image.new("RGB", (1326, 402), BG)
    text(figure, (16, 12), "Right kidney on three parallel s1233 sections", 25)
    text(
        figure,
        (16, 46),
        "Gold  CT half-label   ·   Cyan  packed surface   ·   Rings  maximum directional contour errors",
        17,
    )
    width, beam = map(np.array, (receipt["widths"]["lateral"], receipt["widths"]["beam"]))
    # The reference CT canvas samples a 0.25 mm grid starting at (-70, 35) mm.
    left, top, right, bottom = -66, 54, 62, 54 + (62 + 66) * panel_h / panel_w
    pitch = (right - left) / panel_w
    for i, (plane, check) in enumerate(
        zip(receipt["planeSections"], result["sections"], strict=True)
    ):
        x0 = 16 + i * (panel_w + 8)
        ct = np.clip((reference[f"ct{i}"].astype(float) + 130) / 330, 0, 1)
        raster = Image.fromarray(np.uint8(12 + ct * 134)).convert("RGB")
        panel = raster.resize(
            (panel_w, panel_h),
            Image.Resampling.LANCZOS,
            box=((left + 70) * 4, (top - 35) * 4, (right + 70) * 4, (bottom - 35) * 4),
        )
        origin = np.asarray(plane["originRasMm"])

        def pixels(points, origin=origin):
            rel = points - origin
            return np.stack(
                ((dot(rel, width) - left) / pitch, (dot(rel, beam) - top) / pitch), axis=-1
            )

        draw = ImageDraw.Draw(panel)
        for segments, color in (
            (reference[f"outline{i}"], GOLD),
            (candidate[f"candidate{i}"], CYAN),
        ):
            for a, b in pixels(segments):
                draw.line((*a, *b), fill=color, width=2)
        gold = pixels(reference[f"poles{i}"])
        cyan = pixels(np.asarray(check["meshPolesRasMm"]))
        for direction, color in (("referenceToMesh", GOLD), ("meshToReference", CYAN)):
            mark(draw, pixels(np.array(check[direction]["maxLocationRasMm"])), color)
        for j, label in enumerate(("Superior", "Inferior")):
            draw.line((*gold[j], *cyan[j]), fill=WHITE, width=2)
            for point, color in ((gold[j], GOLD), (cyan[j], CYAN)):
                x, y = point
                draw.rectangle((x - 2, y - 2, x + 2, y + 2), fill=color)
            label_offset = (9, 22) if j == 0 else (-9, -18)
            text(panel, tuple(gold[j] + label_offset), label, 15, WHITE, "lm" if j == 0 else "rm")
        if i == 1:
            draw.line((*gold[0], *gold[1]), fill=GOLD, width=1)
        y0 = 75
        figure.paste(panel, (x0, y0))
        title = (
            "Saved plane"
            if not plane["offsetMm"]
            else f"{plane['offsetMm']:+.1f} mm from saved plane"
        )
        text(figure, (x0, 336), title, 19)
        a, b = (check[key]["maxMm"] for key in ("referenceToMesh", "meshToReference"))
        text(figure, (x0, 364), f"Max {a:.2f} / {b:.2f} mm   ·   pole shifts about 3 mm", 15, MUTED)
    figure.save(output / "protected-planes.webp", "WEBP", quality=88, method=6)


def ellipsoid():
    theta = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    phi = np.linspace(0, np.pi, 25)[1:-1]
    theta, phi = np.meshgrid(theta, phi)
    unit = np.column_stack(
        (
            np.sin(phi).ravel() * np.cos(theta).ravel(),
            np.sin(phi).ravel() * np.sin(theta).ravel(),
            np.cos(phi).ravel(),
        )
    )
    unit = np.vstack((unit, [0, 0, -1], [0, 0, 1]))
    return unit * [24, 21, 53.5], ConvexHull(unit).simplices


def render_surface(points, indices, view, size, pixels_per_mm, focus):
    side = unit_vector(np.cross([0, 0, 1], view))
    up = unit_vector(np.cross(view, side))
    space = points - focus
    w, h = size
    scale = 2 * pixels_per_mm
    projection = np.column_stack((w + scale * (dot(space, side)), h - scale * (dot(space, up))))
    triangles = points[indices]
    normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    orientation = np.sign(np.einsum("ij,ij->i", normal, triangles.mean(axis=1)))
    # The hull facets of the analytic baseline can have either vertex order.
    if len(indices) < 2000:
        normal *= orientation[:, None]
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    light = unit_vector(0.57 * view - 0.48 * side + 0.67 * up)
    illumination = 90 + 142 * np.clip(dot(normal, light), 0, 1)
    order = ((dot(space, view))[indices].mean(axis=1)).argsort(kind="stable")
    raster = Image.new("RGB", (w * 2, h * 2), "#071017")
    layer = ImageDraw.Draw(raster)
    pixels = projection[indices]
    for index in order:
        gray = int(illumination[index])
        layer.polygon([tuple(v) for v in pixels[index]], fill=(gray, gray, gray))
    raster = raster.resize(size, Image.Resampling.LANCZOS)
    marker = ImageDraw.Draw(raster)
    length = 20 * pixels_per_mm
    marker.line((16, h - 22, 16 + length, h - 22), fill=WHITE, width=2)
    text(raster, (16, h - 20), "20 mm", 12)
    return raster


def surface_comparison(delivery, output):
    vertices, faces = mesh(delivery / "sweeps/kidney-right/scenes/kidney_right.mesh")
    # Align bounding-box centers by translation for this isolated form comparison.
    centered = vertices - (vertices.max(axis=0) + vertices.min(axis=0)) / 2
    original, original_faces = ellipsoid()
    figure = Image.new("RGB", (1112, 688), BG)
    text(figure, (16, 12), "Right kidney surface at matched physical scale", 24)
    text(
        figure,
        (16, 45),
        "Isolated shape comparison. Centers aligned for viewing. The s1233 mesh keeps its source scale.",
        16,
        MUTED,
    )
    views = [
        ("Coronal overview", unit_vector([0, -1, 0]), 2.0, np.zeros(3)),
        (
            "Reverse oblique · pole and hilar detail",
            unit_vector([0.6, 1, 0.12]),
            3.0,
            np.array([0, 0, 13]),
        ),
    ]
    for i, (name, view, scale, focus) in enumerate(views):
        x = 16 + i * 544
        text(figure, (x, 77), name, 20)
        for j, (points, indices, label) in enumerate(
            (
                (original, original_faces, "Schematic baseline · 107 mm ellipsoid"),
                (centered, faces, "s1233 exact packed mesh · held trial"),
            )
        ):
            y = 111 + j * 279
            figure.paste(render_surface(points, indices, view, (536, 245), scale, focus), (x, y))
            text(figure, (x, y + 249), label, 16, MUTED)
    figure.save(output / "matched-surfaces.webp", "WEBP", quality=86, method=6)


def live_player(bundle, output):
    capture = bundle / "captures"
    figure = Image.new("RGB", (1324, 730), BG)
    text(figure, (16, 12), "Saved frame 12 in the survey and the separate s1233 sweep", 25)
    text(
        figure,
        (16, 47),
        "Live 3D, B-mode and overlay. The s1233 calipers were added to the player from the frozen CT endpoints.",
        17,
        MUTED,
    )
    titles = ("3D probe and scan plane", "B-mode with calipers", "Registered tissue overlay")
    for row, (name, label) in enumerate(
        (
            ("baseline", "Survey schematic · 107 mm"),
            ("s1233", "Separate s1233 teaching exemplar · 104.3 mm half-label chord · held"),
        )
    ):
        y = 90 + row * 318
        text(figure, (16, y), label, 20)
        for column, (kind, title) in enumerate(
            zip(("contact", "scan", "overlay"), titles, strict=True)
        ):
            x = 16 + column * 433
            text(figure, (x, y + 33), title, 15, MUTED)
            image = Image.open(capture / f"{name}-{kind}.png").convert("RGB")
            image.thumbnail((425, 235), Image.Resampling.LANCZOS)
            figure.paste(image, (x + (425 - image.width) // 2, y + 60))
    figure.save(output / "live-frame-12.webp", "WEBP", quality=88, method=6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("delivery", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protected_planes(args.bundle, args.output)
    surface_comparison(args.delivery, args.output)
    if (args.bundle / "captures/s1233-overlay.png").is_file():
        live_player(args.bundle, args.output)


if __name__ == "__main__":
    main()
