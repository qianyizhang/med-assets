# Bronchial tree: accepted repairs and remaining defects

The authored tree remains **Needs revision**. These are narrow surface/connectivity
improvements, with zero study-count increase. Angular routes, thin schematic
branches, closed ends and unresolved junction defects remain. None establishes
anatomical, clinical, lumen, motion or browser-runtime approval.

| Review | Decision | Evidence and reconstruction |
| --- | --- | --- |
| 2026-10-25 · r07 | Accept scoped authored connectivity/join repair. Remove duplicated distal stem segments before screened unions; retain end→destination controls/radii. Main/lobar ridge and dimple remain. | [Decision](2026-10-25-authored-junction-repair-r07/record.json), [exact export checks](2026-10-25-authored-junction-repair-r07/independent-export-qa.json), [bound whole/context/detail images](2026-10-25-authored-junction-repair-r07/evidence-bindings.json), [recipe](../../models/bronchial_tree/recipes/authored-junction-repair-r07/README.md). |
| 2026-10-26 01:49 UTC · r09 | Independent pixel review accepts reduced near-side dimple/collar and softened opposite collar. No obvious new waist, swelling, flattening or boundary crease in inspected views. Foreground crossing remains. | [Independent export checks](2026-10-26-authored-lobar-fairing-r09/independent-export-check.json), [bound images](2026-10-26-authored-lobar-fairing-r09/evidence-bindings.json), [recipe](../../models/bronchial_tree/recipes/authored-lobar-fairing-r09/README.md). |
| 2026-10-26 02:27 UTC · r13 | Independent pixel review accepts central-Y focal dimple reduction only. Opposite collar is subtly blended; rotated lower junction is still angular/asymmetric and the right-lobar pocket persists. No stronger smoothing was requested. | [Independent export checks](2026-10-26-authored-central-fairing-r13/independent-export-check.json), [six bound images, including the negative rotated view](2026-10-26-authored-central-fairing-r13/render-bindings.json), [recipe](../../models/bronchial_tree/recipes/authored-central-fairing-r13/README.md). |

## Source chain and technical limits

Retain the original baseline and the exact **r07 → r09 → r13** chain: each later
recipe consumes its predecessor. The independent reviews inspected actual
matched whole, close and opposite/rotated rendered views; numerical checks alone
did not establish the visual decisions.

| Export | SHA-256 |
| --- | --- |
| r07 | `3408ca8e8f394dd268b1dbeafdc59fdc8cc104c0976628e455dbc070ae0a7993` |
| r09 | `8820a14b820239c0ea53a3597ad7731b7c66eb41f05b197fde2e90ee08fb47e4` |
| r13 | `c9e2eb595d677203b52aa870a9f0203f059a8f686a65056983fcc59ccd607587` |

- **r07:** sampled source reconstruction discrepancy was zero; eight input meshes,
  15 control records and 16 terminal witnesses were retained. Repaired topology
  has Euler characteristic 2. Source-scene and independent reimport evidence are
  distinct in the bindings; the original baseline was not replaced.
- **r09:** raw export reordered vertices/indices. Independent unique-coordinate
  mapping proved oriented triangles unchanged, 8,026 serialized vertices changed,
  maximum displacement 0.420132 mm and exact coordinates outside support.
  Float32 mapping error was at most 4.15 nm; no degenerate or nonpositive-normal-dot
  triangles were found. Global signed volume changed about −0.0664%.
  Builder checks (reviewed, not independently rerun) preserve 16 terminal 6 mm
  neighborhoods, with local selected area −1.55% and maximum sampled x-plane area
  change 3.27%. Whole-mesh planes include unchanged crossings; these are not local
  lumen/caliber bounds. The 10 mm support and 0.5 mm cap are editorial limits.
- **r13:** independent raw-export mapping proved oriented triangles unchanged,
  6,476 serialized vertices changed, maximum displacement 0.185060 mm, exact
  coordinates outside support and no degenerate/nonpositive-normal-dot triangles.
  Left 12 mm / 11,246 vertices remain exact; right 12 mm / 12,178 vertices are
  unchanged in builder arrays, supported by export/outside-support checks.
  Builder closed parent-normal sections from −8 to 0 mm changed at most 0.235%
  in area; aperture-open +1 to +4 mm cuts were excluded. This is sampled evidence.

Closed topology, positive face-normal dots and sampled sections do not prove
absence of all self-intersections, correct clinical routes, lumen or patency.

## Rejected approaches

| Approach | Decision and reason |
| --- | --- |
| r07 direct union of original surfaces | Rejected: duplicated AUTO-Bezier stems formed two unintended handles (Euler −2). Reconstruct and trim the graph before union; smooth shading cannot repair topology. |
| r08 paired volume-preserving smoothing | Rejected after actual close/rotated inspection: small safe movement did not usefully remove the collar/pit. Numerical safety alone is not a visual improvement. |
| r10/r11 right-junction diffusion | Excluded from r13: the cap pocket persisted despite 0.5/0.75 mm displacement bounds. |
| r12 cap taper from 4.8 to 1.2 mm | Rejected: a new visible waist and up to 40.3% loss of sampled closed-section area. Removing a lip does not justify narrowing the parent junction. |

[OpenStax §22.1](https://openstax.org/books/anatomy-and-physiology/pages/22-1-organs-and-structures-of-the-respiratory-system)
was consulted on 2026-10-25/26 for general branching hierarchy only, not these
authored routes or dimensions. No reference image was copied. Source licenses
and attribution remain with the exports. Publication and integration require
separate checks; this ledger records existing decisions and grants no new pass.
