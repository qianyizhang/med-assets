# Independent review: r09 local lobar surface refinement

2026-10-26 01:49 UTC. **Accept scoped improvement; whole model remains Needs revision.**

## Compared actual rendered pixels
- Baseline r07 `canonical/reviews/bronchial_tree/2026-10-25-authored-junction-repair-r07/evidence/export-lobar-close.png` and `candidate-oblique.png`.
- Rejected r08 `r08/renders/after-close.png`, `after-rotated-close.png`: safe-looking small displacement did not visibly remove collar/pit. No useful visual pass.
- r09 `r09/renders/before-close.png`, `after-close.png`, `after-rotated-close.png`, `after-whole.png`, `before-opposite-close.png`, `after-opposite-close.png`.

## Finding
- Near-side focal dimple removed at displayed resolution; narrow collar substantially reduced.
- Opposite-side collar step also softened. No obvious new waist, swelling, flattened branch or transition-boundary crease in inspected views.
- Unrelated foreground crossing retained. Whole angular branching, very thin schematic offshoots and closed ends remain; this is not a fully approved bronchial anatomy model.

## Independent raw export checks
Candidate SHA256 `8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4`.
- Raw exporter changed vertex/index order: exact byte-index identity is NOT claimed.
- Unique position bijection to preserved builder coordinate arrays: source error0; candidate maximum4.15nm (float32 serialization).
- Full oriented triangle set identical after bijection; 8026 serialized vertices changed; maximum displacement0.420132mm; outside support bit-exact.
- 0 degenerate triangles and0 nonpositive baseline/candidate triangle-normal dot products.
- Global enclosed signed volume decreased approximately0.0664%. This is not a local caliber bound.
- See `r09-mapped-check.json` and reproducible `check_mapped.py` + `check_export.py`.

## Builder checks reviewed, not independently rerun
- `r09/local-geometry-check.json` and `check_geometry_r09.py`: 16 terminal6mm neighborhoods unchanged; local selected-triangle area−1.55%;12 x-plane section maximum absolute area change3.27%.
- Section calculation includes whole mesh at each plane (including unchanged thin crossings). It is sampled planar section evidence, **not** a junction-only maximum narrowing, centerline-normal lumen caliber, or clinical patency measurement.
- Euler2/closed-manifold baseline topology retained by proven triangle bijection. Face-normal check is not an exhaustive self-intersection test.

## Reference and scope
https://openstax.org/books/anatomy-and-physiology/pages/22-1-organs-and-structures-of-the-respiratory-system — verified2026-10-26; supports general conducting-tree hierarchy only, not these authored routes/calibers. No clinical, lumen, complete branch-map, animation or browser runtime pass. Engineering10mm support and0.5mm displacement cap are editorial bounds, not anatomical standards.

Recommendation: preserve r07 baseline and r08 rejection evidence; package r09 with exact-export matched views and limits. No stronger smoothing needed for this scoped defect.
