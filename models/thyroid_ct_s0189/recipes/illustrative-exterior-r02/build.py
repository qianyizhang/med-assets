"""Rebuild the exact r02 thyroid teaching exterior from its retained label baselines."""

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "lib"), str(ROOT)]
from med_assets.surface_fairing import blend, export_trial, fair, load_mesh

THYROID_SOURCE = {
    "path": "models/thyroid_ct_s0189/exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb",
    "sha256": "4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883",
    "bytes": 151580,
}


CONTROL = {
    "path": "models/thyroid_ct_s0189/exports/illustrative-exterior-r01/thyroid-illustrative-exterior.glb",
    "sha256": "4c2dee513f713fd8d649e7d1928ba3859ce1d25e81468e707b65a5fbeeee216a",
    "bytes": 152124,
}

EXPECTED = {"sha256": "6bc4f4da8bc91a058da8f9c78fca8618e3ace90580cac499adf48981bc18608e",
            "bytes": 152288}


def thyroid_trial(row, output, file_name="thyroid-trial.glb"):
    doc, binary, ids, pos, normals, faces = load_mesh(row)
    _, _, _, original, _, reference_faces = load_mesh(THYROID_SOURCE)
    if not np.array_equal(reference_faces, faces) or np.max(np.linalg.norm(pos - original, axis=1)) > .00062:
        raise ValueError("Source-to-baseline vertex correspondence changed")
    # Coordinates are source-frame glTF metres. This panel addresses the rear-facing
    # mid-to-lower band, protecting the bridge, upper lobes and outer contour.
    weight = (blend((np.abs(pos[:, 0]) - .009) / .004) *
              blend((-normals[:, 2] - .35) / .40) *
              blend((pos[:, 1] - .601) / .005) *
              blend((.642 - pos[:, 1]) / .008))
    updated = fair(pos, faces, weight, .00045, 32)
    # Bound combined presentation change against the unretouched retained surface.
    delta = updated - original
    bounds = np.minimum(1, .00075 / np.maximum(1e-30, np.linalg.norm(delta, axis=1, keepdims=True)))
    updated[weight > 0] = (original + delta * bounds)[weight > 0]
    return export_trial(doc, binary, ids, pos, normals, faces, updated, weight,
                        output / file_name,
                        "Rear-facing localized ridge treatment; representative trial on the retained s0189 label exterior. The midline bridge is pinned. No new segmentation.",
                        weight == 0, original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Fresh scratch output directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = thyroid_trial(CONTROL, args.output, "thyroid-illustrative-exterior.glb")
    if {k: receipt[k] for k in EXPECTED} != EXPECTED:
        raise ValueError("Rebuilt thyroid differs from the reviewed output")
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
