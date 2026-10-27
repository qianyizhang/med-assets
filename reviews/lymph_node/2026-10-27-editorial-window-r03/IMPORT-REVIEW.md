# R03 import: surface support, winding and display — WIP

Follow-up to [issue 101](https://github.com/qianyizhang/med-assets/issues/101)
and [draft PR 105](https://github.com/qianyizhang/med-assets/pull/105).
The candidate bytes and previous failed receipts remain unchanged.

## What the missing faces mean

The 18 medulla and 88 network faces removed by Blender 4.3.2 are exact
coincident, opposite-winding indexed pairs inherited from the pinned source.
Each pair maps back to its original source triangle indices and coordinates.
They do not supply separate tissue surfaces or thickness. Fresh import retains
every distinct triangle support at exact coordinates.

That does **not** establish display equivalence. All five source materials omit
`doubleSided`; its [glTF default is false](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/schema/material.schema.json).
Dropping one orientation removes front-facing support from one side. The summed
removed oriented areas are 1.7017843619916802e-8 m² for medulla and
1.1708176106324657e-7 m² for the network (about 0.13410 mm² combined).
These are triangle-area accounting, not lost tissue or visible-pixel measures.

Keeping both records is not automatically a correctness fix: it double-counts
geometric support and gives the same patch contradictory windings for topology
or volume analysis. It can also provide intentional visibility from both sides.
The available evidence does not establish that intention or a unique correct
orientation. Therefore this pass neither deduplicates the candidate nor restores
faces discarded by Blender. Exact source multiplicity is not an acceptance goal.

## Additional criterion; original failure retained

The new `import_audit.py` diagnoses this particular teaching cutaway:

- Require the same exact-coordinate triangle supports; reject movement, additions
  and missing distinct faces. No nearest-neighbor matching or tolerance snapping.
- Require exact winding and multiplicity everywhere except individually proven
  source-indexed reversed pairs. Each exception must have exactly two opposite
  occurrences before import and exactly one original orientation afterward.
- Preserve all other coincidences, including 10 medulla and 67 network extra
  occurrences with different indices. This is not a general deduplication rule.
- Check effective exported material parameters, alpha/culling, assignments and
  transforms. Measure corner normals separately. Vertex colors remain outside
  this audit; no appearance equivalence follows from its material check.

| Decision | Fresh result |
| --- | --- |
| Distinct surface support and unambiguous winding | Passed under the explicit, source-traced exception above. |
| Full oriented triangle multiset / single-sided front-face support | **Failed**, unchanged. This new diagnostic does not replace either check. |
| First import → export → reimport geometry | Exact oriented coordinates and multiplicities pass for all seven meshes. |
| Exact corner-normal preservation | **Failed** separately; differences and zero input normals are reported, not hidden by an enlarged tolerance. |
| Visual usefulness | Prior matched front/detail/reverse pixels independently reinspected: clearer provider-named regions, lost continuity and reverse pink fringe remain explicit. |
| Anatomy / clinical / browser runtime | No new acceptance; vessel identity remains unresolved and browser runtime untested. |

The matched-corner audit finds 6 medulla and 40 network zero input normals;
19 network corners remain zero after first import. Nonzero-input component
differences also reach about 0.999 and occur away from the duplicate pairs.
Component differences use the best available matching corners when several
coincident faces exist; they do not prove a unique correspondence or shading
equivalence. The exact-normal gate additionally accounts for multiplicity, so
one source normal tuple cannot justify multiple replacement copies. This pass
does not attribute every difference to rounding or duplicate removal and does
not repair those normals.

Retain r03 as a local editorial inspection candidate. It is not a faithful
single-sided viewer replacement or a topology/volume-analysis mesh. A later
display acceptance needs a justified culling/normal policy and supported viewer
evidence. A provider correction or validated mesh correspondence is still needed
before resolving the [vascular name](LABEL-DECISION.md).

## Reproduce

After the existing [build/check commands](README.md#reproduce-into-new-output-directories),
use a fresh output directory:

```sh
blender --background --factory-startup --disable-autoexec --threads 4 \
  --python-exit-code 1 \
  --python tools/lymph_node/editorial_window_r03/import_audit.py -- \
  --source models/lymph_node/exports/hra-v1.2/NIH_M_Lymph_Node.glb \
  --candidate-dir /tmp/lymph-r03-new --output /tmp/lymph-r03-import-audit-new

python3 tools/verify.py offline
```

Successful audit execution means the scoped diagnosis completed; read the
separate failed/unverified fields in `surface-audit.json`. Offline CI exercises
synthetic verifier tests only; it does not run Blender or verify payload bytes.
The pinned source/candidate identities, prior evidence and new receipt are
recorded in [decision.json](decision.json). Issue 101 remains open and PR 105 WIP.
