# Testis–epididymis native study — issue #150

Started: a separate 3D supplement for `draft_testes`. The historical flat-strip
baseline remains preserved; completed 2D transport teaching issue #129 is outside
this scope. This is not a full-organ acceptance or ledger count change.

The [retained baseline](../../2026-10-23-v10-exterior-review/draft_testes/screenshots/contact.png)
shows smooth ellipsoids, flat pink attachment strips and uniform tubes. Its exact
artifact is `71c760a96d57798b83bfc4af9d94c577606591f13d59c6c102be79986e500f09`
(80,204 bytes); the original GLB is external to this checkout. Its preserved
image is inspected evidence, not a matched render of the new source model.

## Bounded acceptance

- Show a source-backed epididymal head/body silhouette and its native testis
  relationship in whole context and a single-side close-up.
- Preserve native effective transforms and evaluated source geometry; explain
  any source selection or display change. Do not invent a missing connector.
- Inspect actual clean-import pixels independently, including a matched v1/v2
  comparison, and correct visible export/presentation defects.
- Validate exact source, export, replay and scoped geometry; retain unresolved
  anatomy, lumen, physical-scale and runtime gates.

## V1 checkpoint

The source is pinned [Z-Anatomy](../../../sources/datasets/z-anatomy/testicular-region/provenance.json)
under the [retained attribution and license](../../../sources/datasets/z-anatomy/testicular-region/ATTRIBUTION.md).
Six native objects exported to a 261,972-byte GLB:
`1442a5d7f90bc301467e819e0467e01bafbac4c145e5131ffd832b8e3c3453a2`.
V1 uses the source viewport subdivision setting. Whole and two detail views were
rendered from a clean GLB import. Independent review and source-export checks are
pending. The full deferens includes an uncertain lower junction; no continuity
claim is made. The side detail currently superimposes both sides.

Recipe: [build.py](../../../models/testes/source/z-native-epididymis-r01/build.py)
and [render.py](../../../models/testes/source/z-native-epididymis-r01/render.py).
Run with Blender 4.3.2, `--factory-startup`, the pinned source and a new output
directory. No upstream scripts are executed.

Media are local pending scoped review and normal permitted transport. No new
LFS pointers, public image evidence, clinical approval or viewer-runtime pass
are claimed by this checkpoint.
