# AssetKit migration acceptance

Use the [migration specification](../../docs/MIGRATION_SPEC.md) for the gates and the [landscape](../../docs/ASSET_LANDSCAPE.md) for the initial inventory. Local package commits and consumer integrations land on `asset-governance-v1`.

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
