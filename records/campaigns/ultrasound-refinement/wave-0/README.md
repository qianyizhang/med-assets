# Ultrasound refinement · Wave 0 audit

The local audit traces **28 standalone sweeps and all 410 chapters across 32 worked cases**. The s1233 liver is the only directly pinned native export in the standalone playback catalogue. The 410 chapter readers have **zero direct AssetKit export pins**. They use recipe-backed geometry, fitted context, packed AAA scene data and independent reference panels. The liver remains on `r01` under the pretrial decision. [Summary ledger](audit-summary.json) · [Assembly receipt](assembly.json) · [Liver pretrial](../pretrial/README.md)

Wave 0 closed before Wave 1 authorization. The [Wave 1 record](../wave-1/README.md) contains the local trial and proposed disposition.

| Delivery | Standalone sweeps | Chapters | Review identities matched | Matched reviews with four evidenced 4/4 scores |
| --- | ---: | ---: | ---: | ---: |
| Regional liver pretrial | 17 | 410 | 8 / 71 | 1 |
| First complete assembly | 28 | 410 | 26 / 71 | 14 |
| Complete assembly with bilateral carotid survey | 28 | 410 | 71 / 71 | 15 |

The eleven pregnancy inputs restore the pregnancy family fingerprint in the first complete assembly. The rebuilt bilateral carotid survey supplies context meshes included in the organ and vascular family fingerprints. It has its own reader outside the 28 standalone sweeps and 32 worked case tours. Both additions restore earlier review bindings without changing the case chapter count. [Regional audit](../pretrial/audit.json) · [Assembly receipt](assembly.json) · [Recipe fingerprint implementation](../../../../lib/med_assets/ultrasound_review.py)

Of the 71 retained review rows, 59 have observations for all four axes. Eleven organ reviews lack readability observations. The pregnancy Fluid pocket boundary lacks a fidelity observation. All 12 stay incomplete at their matching identities. The 80 additional uses remain on their authored assessments. Case-level bindings carry their own scope in the ledger. A case-level result is distinct from an assessment of the saved chapter. The 15 top scores apply to their stated tasks and evidence. [Review records](../../../../experiments/ultrasound-sweep/development/asset-reviews/) · [Rubric](../../../../docs/guides/asset-quality.md)

At the saved frames, **283 of 410 chapters** instantiate at least one analytic primitive or coarse voxel surface. The total comprises 86 chapters with primitives and 197 with coarse voxel surfaces. These counts include context anatomy and identify candidates for task-specific review. A further 70 vascular chapters instantiate modeled vessel lofts. The [right-kidney brief](right-kidney-brief.md) follows one measured primitive from its 3D scene to its scan and calipers.

## Reading the ledger

For the hepatic vein task, find `abdomen-survey / abd-hepatic-vein-doppler` at frame 12. Its actual 3D model draws an analytic hepatic vein and IVC. The workbench links the standalone IVC and liver as independent references and calls for a separately traced hepatic vein. The held claim is an evidenced continuation into the IVC in one registered source; the analytic case lesson remains playable within its stated scope. [Abdominal model](../../../../experiments/ultrasound-sweep/cases/organs/playable-abdomen.js) · [Workbench requirements](../../../../experiments/ultrasound-sweep/development/assets-abdomen.js)

| Ledger section | Evidence |
| --- | --- |
| `sweeps` | Player route, named scene parts, packed mesh identities, authored stop poses and image files, acquired comparison credits, and staging receipts with source pins and registration checks. |
| `chapters` | Chapter task, exact reader link, saved-frame pose and named measurement data, and part occurrences placed in the actual evidence-frame model. Workbench reference requests, unavailable surfaces, and named scan labels or acquisition states have separate bindings. |
| `sources` and `files` | Recipe, representation, source or donor identity, coordinate convention and relevant packed file or module identities. Input mesh shape, triangle and byte counts come from the delivered bytes. |
| `nativeExports` | Exact keys and package records for the direct liver export, upstream atlas inputs and independent Gallery donors. Only a direct payload binding counts toward native runtime coverage. |
| `reviews` | Separate authored task, part, reviewer, revision, rubric, observations, witness identities and additional uses. `identityMatches` measures fingerprint currency. `missingAxes` reports the limits on rating completeness. |
| `dispositionDefinitions` | Action, accountable owner and evidence needed next. Unrated geometry remains context pending task review. A source/rebuild requirement needs a reference and an evidenced placement. Acquisition claims need reader-level evidence. |

In the ledger, an instantiated mesh is present in the scene assembly at the saved frame. Camera framing, section intersection, occlusion and teaching legibility need their own witnesses. Repeated supports and other contextual parts are counted as uses across chapters. A named label can describe a sampled tissue without a separately selectable 3D surface.

`workbenchSelection` records whether the workbench chooses that runtime part for its retained-geometry panel. `acquisitionBinding` records exact part-name matches to chapter labels or measurement marks. For example, the modeled right kidney carries the width mark in the long-axis chapter. The workbench opens an independent sweep surface for that task.

| Runtime example | Representation and decision |
| --- | --- |
| `abdomen-biliary-stone / biliary-stone-roll`, frame 12 | Scaled analytic primitives support the modeled scan action. A depicted calculus and shadow establish the case behavior. The requested independently sourced wall, lumen and mobile calculus require their own evidence. |
| `pregnancy-mid-normal / mid-overview` | The case fits the packed stage fetus to the biometry model. Other visible tissue groups are reconstructed from a coarser sampled voxel field or use distinct packed stage parts. The matched exterior review covers its named limb-tracing task. |
| `aaa-positive / sac-maximum`, frame 14 | The wall, lumen and vein are authored meshes placed in the s1233 acquisition frame. The torso and vertebrae use the exact packed screening context. Mural thrombus has a scan representation and an open selectable-surface gap. Scene data, packed geometry and frame images are checked against the specific AAA acquisition receipt. |
| `echo-aortic-stenosis / psax-av-section` | The reader samples authored leaflet patches in the registered chest model. The current cusp 1 review covers an inspectable open sheet at the saved frame and closure, with a modeled anatomy limit. |

## Reproduce and inspect

Run from the repository root with the tested source inputs and the assembled delivery recorded in the receipt. Under [retention](../../../../docs/WORKFLOW.md#retention), the full 3,633,862-byte per-occurrence report (`SHA-256 f85458d3c67fd0f16b40f2c0285fb221df3de95b5038b8882ef43a529e925a8e`) stays in ignored `.artifacts/us-wave0/audit.json`, while the compact [summary ledger](audit-summary.json) and generator stay in Git.

```sh
node records/campaigns/ultrasound-refinement/wave-0/audit.mjs \
  .artifacts/us-wave0/browser-delivery .artifacts/us-wave0/browser-stage \
  /tmp/ultrasound-wave-0-audit.json /tmp/ultrasound-wave-0-summary.json
shasum -a 256 /tmp/ultrasound-wave-0-audit.json
cmp records/campaigns/ultrasound-refinement/wave-0/audit-summary.json /tmp/ultrasound-wave-0-summary.json
```

The audit invokes the delivered scene adapters, walks their selectable meshes at the saved chapter frame and checks packed identities, authored review images and the AAA acquisition seal. The runtime mesh fingerprints describe vertex and index buffers and the scene transform at that frame. They are local audit witnesses. The owning workbench recipe hashes continue to bind the assessments. The [assembly receipt](assembly.json) records the full delivery replay and family-specific geometry checks. The ledger records local coverage, provenance and task evidence. Anatomical and clinical qualification remain limited to individual reviewed claims. [Runtime scene checks](../../../../experiments/ultrasound-sweep/tours/verify-case-geometry.mjs) · [Assembly receipt](assembly.json)

## Local verification

The final delivery passed the repository browser checks on loopback in Chrome for Testing 158. The standalone player exercised all 28 sweep routes. The exam tour harness covered 390 non-AAA chapters and the AAA harness covered the other 20. The worked-case browser opened all 32 case routes, decoded 239 distinct images and checked the study entry points, including the separate carotid survey. These checks establish playback and routing. The kidney comparison still needs a task-specific witness after Wave 1 authorization.

The assembly replay reproduced all 6,068 files. Its validator rejected 46 independent invalid-input cases. The audit regenerated byte for byte and all 962 delivery-file identities referenced by the ledger were independently checked. The repository offline and hydrated payload gates, AssetKit lint, type checks, 81 tests and maintained teaching-register validation passed locally. [Assembly receipt](assembly.json)
