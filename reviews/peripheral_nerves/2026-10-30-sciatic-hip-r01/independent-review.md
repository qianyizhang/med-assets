# Independent static review

Reviewer: a separate read-only agent, `/root/median_wrist_review`.
No reviewer edits, rerenders or publication actions.

| Stage | Actual evidence and decision |
|---|---|
| Source preflight · 07:34:18 UTC | Personally inspected all five native PNGs. Useful sciatic course against posterior hip/proximal femur. Four-object skeletal scope accepted; soft-tissue relationship excluded. |
| V1 export · 07:41:00 UTC | Personally inspected all three clean-reimport PNGs and verified the exact GLB hash/size. No teaching-scale geometry, material or framing defect. Requested labels, orientation, whole-region locator and endpoint notes. |
| V2 · 07:47:06 UTC | Personally inspected final 1900×1130 color and grayscale. Accepted with stated limitations; no further image iteration requested. Input/output hashes and true grayscale independently verified. |

All times **2026-10-30 UTC**. Canonical identities are in
[source bindings](source-bindings.json), [V1 capture bindings](v1/bindings.json)
and [V2 composition](v2/composition.json); duplicate hash inventories are omitted.

The labels identify the visible sciatic trunk, ischial-tuberosity region and
greater-trochanter region. Posterior/oblique pairing clarifies the close
nerve–ischium boundary. The whole-view box is explicitly a region locator.
Partial proximal strands and the distal source-end marker prevent an inference
of a complete nerve. Color is preferred; grayscale reduces tissue separation.

The [shown soft-tissue views](preflight/bindings.json) make the nerve appear to
emerge through the piriformis surface. Reported overlap candidates reinforce an
unresolved relationship; they do not establish penetration, clearance or a
variant. Omission is not an anatomical repair. Do not teach a complete foramen,
piriformis layer, exact midpoint, plexus completeness or surgical safe zone.

Primary gross-landmark reference screening:
[Ma et al., cadaveric landmark measurements](https://pmc.ncbi.nlm.nih.gov/articles/PMC10772174/)
and [Reynoso et al., piriformis relationship variation](https://pubmed.ncbi.nlm.nih.gov/36412694/).
These support the bounded question and variation caveat, not validation of this
source's coordinates. No reference images or passages are copied.

The reviewer read the six passing visible-target checks without rerunning them.
Source-preservation QA is separate; the visual acceptance does not settle the
documented exporter/importer behavior. Clinical and browser-runtime gates remain
unverified.
