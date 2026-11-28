"""Check the approved s1233 pancreatic exterior task against a Wave 2A measurement report."""

import argparse
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRIAL = HERE.parent / "contour-trial"
VERIFIER = HERE.parents[1] / "spleen/measure.py"
EXPECTED = "16919fa7975eca4d8e3b2c0de47d30490b823810daa2b8878d6baab432bc6b96"


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("case", "mesh", "measurements"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    measure = module(VERIFIER)
    trial = module(TRIAL / "trial.py")
    geo = measure.wave_module("wave-1")
    data = json.loads(args.measurements.read_bytes())
    frozen, reference = trial.source_data(args.case)
    if (
        data["frozen"] != frozen
        or data["export"]["sha256"] != sha256(args.mesh.read_bytes()).hexdigest()
    ):
        raise ValueError("Measurement inputs differ from the frozen case or packed mesh")
    exterior = data["pancreasExteriorDiagnostic"]
    if sorted(pocket["voxels"] for pocket in exterior["excludedEnclosedMaskPockets"]) != [
        4,
        16,
        22,
    ]:
        raise ValueError("Unexpected enclosed mask regions in the exterior reference")
    areas = exterior["delineation"]
    if [row["offsetMm"] for row in areas["protectedPlanes"]] != [-1.5, 0, 1.5]:
        raise ValueError("Missing frozen exterior sections")
    if set(exterior["localExterior"]) != {
        "tailSuperiorTo370mm",
        "neckRasXMinus8To4AndZ340To357mm",
        "uncinateInferiorTo312mm",
    }:
        raise ValueError("Missing protected 3D landmarks")
    # Reuse the original thresholds and mesh checks with the approved exterior reference.
    failures = measure.gate_failures(data | {"candidate": exterior["delineation"]})
    for region, directions in exterior["localExterior"].items():
        for direction in ("referenceToMesh", "meshToReference"):
            result = directions[direction]
            if not (result["p95Mm"] <= measure.P95_MM and result["maxMm"] <= measure.MAX_MM):
                failures.append(f"{region}: landmark exceeds the original 3D distance limits")
    vertices, faces = geo.mesh(args.mesh)
    surface = vertices[faces]
    normal = np.array(frozen["normalRas"])
    origin = np.array(frozen["protectedPlanes"][1]["originRasMm"])
    checks = []
    for offset in (-2.25, -0.75, 0.75, 2.25):
        anchor = origin + offset * normal
        a, b = (geo.cut(tris, anchor, normal) for tris in (reference, surface))
        for direction, source, target, target3d in (
            ("referenceToMesh", a, b, surface),
            ("meshToReference", b, a, reference),
        ):
            cut = geo.compare(source, target)
            marker = np.array(cut["maxLocationRasMm"])
            error3d = float(np.linalg.norm(trial.closest_point(marker, target3d) - marker))
            if not error3d <= measure.MAX_MM:
                failures.append(f"{direction} at {offset} mm: exterior miss exceeds 3 mm in 3D")
            checks.append(
                dict(
                    offsetMm=offset,
                    direction=direction,
                    sectionMaxMm=cut["maxMm"],
                    nearestSurfaceMm=error3d,
                    locationRasMm=marker.tolist(),
                )
            )
    if failures:
        raise ValueError("; ".join(failures))
    if data["export"]["sha256"] != EXPECTED:
        raise ValueError("The orientation decision is restricted to pancreas r02")
    print(
        json.dumps(
            dict(
                export=data["export"],
                rawFailures=measure.gate_failures(data),
                interleavedSections=checks,
                orientation="passed",
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
