# Bronchial first-fork fairing r15

Use [this authored exterior](bronchial-first-fork.glb) to trace the trunk into the two main branches. The [neutral task plate](../../../../reviews/teaching-assessments/target-form/plates/bronchial-first-fork-teaching.webp) shows the whole schematic and the fork from two matched close angles. The [r14/r15 comparison](../../../../reviews/teaching-assessments/target-form/plates/bronchial-comparison.webp) shows the underside and opposing collar at the prior 45 mm scale.

| Export | SHA-256 | Bytes | Triangles |
| --- | --- | ---: | ---: |
| r15 | `dec2886f07745086e56a31676b96005e0741d4475782fd879f47faf15769a42e` | 7,401,468 | 308,288 |
| [r14](../distal-sampling-r14/README.md) | `f8d78751f47cf14311138a3c7e2e35d6e28415c9f6e1d2a0e4f6ca2bf1a07fc9` | 7,401,328 | 308,288 |

The local fairing modifies the collar and underside of the first split. It keeps exact topology, triangle order and distal surfaces outside the 24 mm source-frame support. The clean import measured 36,067 moved vertices and a maximum displacement of 0.791 mm. The finite-precision contact check found zero new nonadjacent triangle contacts in the moved neighborhood. The solid fork silhouette stays distinct in front, lower oblique and reverse views. A small low-contrast highlight persists on one branch. The farther right lobar pocket and schematic terminal caps remain outside this first-fork study.

OpenStax depicts the first tracheal split into the right and left main bronchi. This edition illustrates that route on the authored exterior, with the split fixed by the original authored tree. Its surface treatment has no case-specific anatomical or lumen interpretation. [OpenStax respiratory anatomy](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system)

The [r14 attribution](../distal-sampling-r14/README.md#attribution-and-delivery) and [r13 source attribution](../authored-central-fairing-r13/ATTRIBUTION.md) apply. The original schematic used display lung bounds derived from TotalSegmentator case s1233. Retain credit to Jakob Wasserthal, the TotalSegmentator contributors and University Hospital Basel under CC BY 4.0. The source attribution declares the terms and modification history.

Recover into a fresh directory from the exact hydrated r14 with Python 3.12 and NumPy.

```sh
python3.12 models/bronchial_tree/recipes/first-fork-fairing-r15/build.py .artifacts/bronchial-r15-replay
```

Verify the replay identity above before installing the payload. [Render and integrity evidence](../../../../reviews/teaching-assessments/target-form/README.md)
