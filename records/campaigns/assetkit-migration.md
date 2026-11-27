# AssetKit migration acceptance

Use the [migration specification](../../docs/MIGRATION_SPEC.md) for the gates and the [landscape](../../docs/ASSET_LANDSCAPE.md) for the initial inventory. Waves 0–3 are complete on the local `asset-governance-v1` branch. The [final integration results](#final-integration) cover all three readers and the [disposition inventory](assetkit-dispositions.md) identifies every deferred path.

## Wave 0

| Check | Evidence |
| --- | --- |
| s1233 export | The owner recipe rebuilt the 2,217,704-byte mesh from its pinned mask. The 61,604 vertices, 123,204 triangles and SHA-256 matched the existing r01 export. The normal builder rejected missing bytes, an LFS pointer, same-size digest drift, an unknown revision and a shifted grid origin. [Record](../../models/liver_s1233/asset.record.json) |
| s1233 lesson | Locally tested pilot sources at `48c9df94` with the retained eight companion sweeps. All 49 liver poses, scans and overlays matched the preceding lesson. Chrome for Testing 158 opened frame 12, fetched the mesh once, showed the acquired image and its credit, and retained the 3D scene and overlay on a forced comparison-image 404. Changing the frame label survived rebuild and playback with the same mesh and images. Native impact returned the exact liver sweep pin. Local receipts and screenshots are under `.artifacts/assetkit-liver-wave0/`. [Owning track](../../experiments/ultrasound-sweep/abdomen-tracks.json) |
| HRA liver | `2cee5d27` registers the selected 595,352-byte export. Fresh replay, all eight selectors and 41,470 triangles matched. The Gallery selection resolves through the maintained teaching register. The package remains provisional in the native HRA frame. [Record](../../models/liver/asset.record.json) |

Canonical record tooling landed at `85365926`. Writer regressions cover conflicting pins, missing payloads, recipe input drift, stale plans, concurrent writers and exact repeat application. The real HRA suite covers hydrated and pointer checks, scoped task evidence, the replay input, selectors, and rejection by the s1233 placement handoff. [Writer tests](../../src/assetkit/tests/test_record_sync.py) · [HRA acceptance](../../src/assetkit/tests/test_hra_port.py)

At `2d406f93`, 41 focused tests, the offline suite, and hydrated payload verification succeeded. The six s1233 PRD checks and HRA package acceptance passed on the local integration branch.

## First ultrasound batch expectation

The abdomen surface-fit recipe reads two BodyParts3D inputs. Both source GLBs retain their original atlas frames. The sweep owns the fit to the case surface. Preserve its output and exercise the actual lesson before assigning the rest of the ultrasound packages.

| Expected package record and native key | Reader input before migration | Placement in the sweep |
| --- | --- | --- |
| `models/skin/asset.record.json` · `anatomy:bp3d:skin@bp3d-envelope-r01:envelope` | `models/skin/exports/bp3d-envelope-r01/skin_source_frame.glb` | Outer envelope used by the display fit. [Source and review](../../models/skin/exports/bp3d-envelope-r01/README.md) |
| `models/skeleton/asset.record.json` · `anatomy:bp3d:skeleton@teaching-economy-r01:skeleton` | `models/skeleton/exports/teaching-economy-r01/skeleton_source_frame.glb` | Right rib landmarks establish the bounds for that fit. [Recipe and export pin](../../models/skeleton/recipes/teaching-economy-r01.json) |

The package records landed at `67fcdf6a`. The local reader integration at `4ac8727b` gives the exterior fitter a single pair of native recipe pins. Hydrated and pointer-only tests passed for both exports. All 14 affected sweeps reproduced the existing 3D, pose, scan and overlay payloads. Eleven sampled browser views and the end-diastolic cardiac torso matched. A comparison-image 404 left the liver scene usable; the browser fetched neither source atlas GLB. The AAA build reproduced 1,256 payloads. A changed or missing atlas, a pointer, an incompatible frame/owner, or swapped slots failed at the reader. Local receipts are in `.artifacts/assetkit-bp3d-wave1/`. Legacy discovery still exposes historical sibling paths separately from a governed lineage (`a05a281a`).

## Remaining ultrasound inputs

The independent pre-port inventory at `67fcdf6a` identifies ten workbench source GLBs and 43 named output parts in `gallery_reference_sources.py`. Only the mammary donor also feeds the breast acquisition builder. Expected families are mammary, female pelvic context, ovary/tubal, full-term placenta, lymph node, pelvic bladder base, pancreatic context, left and right kidney, and diaphragm. Keep the original donor editions for pelvis, ovary, placenta and pancreas even where Gallery selects a different edition. Acquired comparisons, the separate external female skin, CT masks, gestational simulations and new geometry requests remain with their owners. [Workbench and acquisition contracts](../../experiments/ultrasound-sweep/README.md)

The ten package records landed in `5553dd2b` and `1134059a`. The config and normal readers landed in `ebabc8e0`. [Donor configuration](../../experiments/ultrasound-sweep/gallery-reference-assets.json) · [Workbench reader](../../experiments/ultrasound-sweep/gallery_reference_sources.py) · [Mammary acquisition](../../experiments/ultrasound-sweep/breast_anatomy.py).

The workbench reproduced the complete 43-mesh donor inventory. All 422 breast, nipple and axilla payloads matched the pre-port build. The native index identifies the ten recipe dependencies and the second mammary reader. Compact assembly passed 36 failure paths. Chrome compared seven views, including a case-scoped workbench bookmark, with no source GLB downloads. The offline and hydrated payload gates passed. Raw placental and ovarian atlas reconstruction requires external pinned originals; their retained derivatives and teaching editions were checked locally. See `.artifacts/assetkit-donors-wave1/` for local receipts.

## Body Systems and Gallery baseline

The independent candidate compiler produced 97 Library families and 205 listed paths before Gallery integration. Of those, 201 tracked payloads matched their declared identities. Two legacy dental tools and two unavailable historical paths retain their existing delivery dispositions. The named selection register contains 81 selections. Counts are supporting observations; compare exact paths, digests, bytes, family membership, and routes.

Body Systems has 70 plate placements keyed by system, plate kind and ID. Its 66 unique render pairs use 21 GLB inputs: seven tracked, twelve restored archive members and two local Workshop s1233 outputs. The 132 delivered WebPs are the runtime payloads for stills. Two detailed pelvic stops additionally use live tracked GLBs. Preserve independent bindings for survey replay, optional 3D and supplemental images. The original s1233 compositions and the HRA/BodyParts3D alternatives have separate identities.

The [Workshop](../../body/anatomy-workshop-r1/asset.record.json) and [breathing](../../body/breathing/asset.record.json) records in `bb6adfc6` cover 33 export identities. Source surfaces, authored details, component motion and editable Blender inputs retain their individual limits. The original skeleton and muscle used for survey rendering have distinct identities from their compact editions (`104d3b23`). The three cardiac owner records in `69fffce4` cover 15 exports. The ten original RAS-millimetre STL files stay with the frozen Gallery deliveries, and the fitted animation lacking exact bytes remains explicitly unavailable. Original model/showcase, focused ventricular motion, and opaque static/animated identities stay distinct.

The assembly records in `77ae3abf` and `893ea605` cover ten tracked exports. The femoral exterior, measured trabecular specimen and illustrative marrow container have separate owners. The dated Achilles evidence once again binds the exact historical replay receipt. The dated package README carries the current command. The historical replay receipt used the same script bytes at the earlier path. Restored endocrine, knee and calf replay assets remain identified by their archived bytes. Hydrated and actual LFS pointer checks passed on the package records.

## Reading the preserved review evidence

Gallery serves these documents at content-addressed URLs. Replaying a current package requires the following details alongside the dated evidence.

| Evidence document | Current replay guidance |
| --- | --- |
| [HRA liver exterior](../../models/liver/README.md) | The [selected teaching edition](../../models/liver/exports/teaching-economy-r02/README.md) uses the original exterior as its pinned input. The maintained task is locating the posterior bare area relative to the anterior surface. |
| [Placenta](../../models/placenta/README.md) | Git LFS supplies the tracked derivative. To repeat the original material replay, supply the external GLB at the [source pin](../../sources/datasets/hra/placenta-full-term-v1.1/source.json) and verify its size and digest. |
| [Ovary and tubal context](../../sources/datasets/hra/ovary-tubal-context/README.md) | Source metadata and attribution are tracked. Replaying from upstream requires the four external original GLBs identified by the [manifest](../../sources/datasets/hra/ovary-tubal-context/source-manifest.json). |
| [Achilles replay](../../assemblies/musculoskeletal-teaching/2026-10-23/README.md) | Use the documented assembly recipe path. The [receipt](../../reviews/draft_muscle/2026-10-23-achilles-context/independent-export-replay.json) records the earlier invocation at `tests/achilles_context/build_proposal.py`, before commit `5331ea07` relocated the script. |
| [Original cardiac exterior guide](../../heart/exterior-presentation-r01/README.md) | The [November fitted-heart review](../../reviews/heart_exterior/2026-11-01-fitted-applicability/README.md) subsequently verified the exact fit transform and opaque-exterior rule. The historical Gallery download still lacks the fitted file at its expected path. |
| Skeleton and muscle original edition READMEs | Frozen review evidence keeps its original bytes. The current [skeleton](../../models/skeleton/README.md) and [muscle](../../models/muscle/README.md) package guides identify the separate compact editions. |
| [Anterior eye package](../../models/eye_anterior_segment/README.md) and [attribution](../../models/eye_anterior_segment/ATTRIBUTION.md) | Both derivatives are retained. A fresh replay of the original seven-component study requires the external provider GLB identified in the [source receipt](../../sources/datasets/hra/eye-male-right-v1.3/source.json). The receipt and attribution preserve its identity and credit. |

## Body Systems acceptance

At `c339adab`, the [display bindings](../../lessons/body-systems/display/replay-bindings.json) associate every plate with its original view and mesh inputs. The normal exporter reproduced all 132 display WebPs plus the display, replay and delivery indexes byte for byte. Re-encoding unchanged source PNGs with a different WebP encoder had changed 101 display files during the initial rehearsal. The exporter now keeps verified results and rejects a reconstruction that disagrees with an approved identity. The [pelvic export pins](../../lessons/body-systems/pelvic-exports.json) match both live actions to the selected exports and parts. At `6ccad0c5` those pins moved beside the lesson, preserving the client layer configuration. The browser exercised six layer lessons, including changing layers, exact GLB downloads, failed downloads, corrupt bytes and recovery. The elbow test now follows its actual entrance under Lessons.

## Gallery package ports

The first Gallery package group registered the anterior eye, lungs, independent joints and other selected editions in `64320449` through `3b6045e0`. The second group registered the nerve, spine, spleen, skin, nail and related lineages in `2b391863` through `41be7794`. Full-resolution and historical paths with documented replay or delivery duties retain those roles. The independent HRA and s1233 spleens, skin envelope and authored nail, and all four joints and three nerve studies retain distinct owners.

The [full disposition inventory](assetkit-dispositions.md) reconciles the 85 directory candidates and the independently maintained cutaway under One Breath. The terminal geometry and retained dental review landed in `f691f6f1`. The original s1233 pilot now declares its voxel-index frame against the Workshop grid evidence in `7d47c7f1`. All 83 owner records passed strict admission on both a hydrated checkout and a depth-one Git LFS pointer checkout.

## Final integration

Tested local integration revision `4068489e` against the original `48c9df94`. All 83 native owners and 160 exports passed hydrated `check-port` with independent identities. The s1233 packed liver mesh is the one native export used exclusively outside the candidate Library.

| Candidate Gallery coverage | Result |
| --- | --- |
| Catalog | 97 families in the compiled Library. The 205 distinct 3D file paths occur in 75 of those families. All 81 maintained selections match their current task, assessment, native owner and export. |
| Native entries | 159 file paths have native export bindings. Exact `impact` queries found the expected 117 Gallery routes across 234 distinct route/file pairs. Every catalog-only bundle has zero runtime bytes. |
| Remaining entries | 18 replay inputs, 13 historical editions, 11 frozen evidence deliveries, two external dental tools and two unavailable historical files. Each has its own [disposition and evidence](../../sites/anatomy-gallery/library-admission.json). |
| Release parity | An isolated checkout of the original revision restored all 1,704 LFS files from local bytes. Both ordinary offline bootstraps used the same framework, seed and viewer. All 379 assembled files outside installed dependencies matched byte for byte, including the candidate HTML, selected Library, generated Worker, release resources and transport indexes. The 10,066 installed dependency files and symlinks also matched. The HTML SHA-256 is `81eb4694138ff973f693627b6694a56b4bc2f50a3e3de303893ffced8bb2524e`. |
| Maintainer workflow | The [admission preview](../../sites/anatomy-gallery/README.md#candidate-library-admission) reproduced the committed file byte for byte. The normal build rejected a stale route, and the preview produced the new reader binding with the original native export identity. An invalid file identity failed with the prior build output intact. The existing teaching registers continue to own selection and assessment. |
| Repository and package gates | Hydrated verification covered all 1,704 LFS files (1,156,950,093 bytes). All 63 AssetKit tests, three Body Systems exporter tests, and the separate seven-check UFF dental gate passed. A fresh depth-one LFS-pointer checkout installed the locked dependencies offline and passed the repository gate and 62 AssetKit tests. The hydrated HRA geometry/replay test skipped there and passed on the hydrated checkout. |
| Ultrasound | A fresh s1233 mesh rebuild and all 49 liver poses, scans and overlays matched. Chrome reproduced the entire pre-port frame 12 screenshot and fetched the governed mesh once. The final compact replay reused the retained non-liver stages. A missing acquired image kept the 3D scene, simulated scan and overlay usable. The two exterior inputs, ten donor sources and 43 packaged donor files retained their named uses. |
| Release rehearsal | The final generated candidate and frozen v10 Workers passed on both test origins with local storage fixtures. Chrome checked candidate and public route differences, archive playback and fallback against two loopback servers. The final Library suite exercised 151 routes and checked 101 exact download responses. The collections, six layer lessons, lesson plates and ovary checks passed. |

Local receipts are under `.artifacts/assetkit-gallery-original-final/`, `.artifacts/assetkit-migration-review/`, and `.artifacts/assetkit-liver-final/`. The downloadable assets, teaching assessment register, public transport configuration and frozen release selection retain their pre-migration identities. New geometry, rights resolution, cold storage, live publication and remote availability have separate owners and evidence requirements.
