# AssetKit migration acceptance

Use the [migration specification](../../docs/MIGRATION_SPEC.md) for the gates and the [landscape](../../docs/ASSET_LANDSCAPE.md) for the initial inventory. Local package commits and consumer integrations land on `asset-governance-v1`.

## Wave 0

| Check | Evidence |
| --- | --- |
| s1233 export | The owner recipe rebuilt the 2,217,704-byte mesh from its pinned mask. The 61,604 vertices, 123,204 triangles and SHA-256 matched the existing r01 export. The normal builder rejected missing bytes, an LFS pointer, same-size digest drift, an unknown revision and a shifted grid origin. [Record](../../models/liver_s1233/asset.record.json) |
| s1233 lesson | Locally tested pilot sources at `48c9df94` with the retained eight companion sweeps. All 49 liver poses, scans and overlays matched the preceding lesson. Chrome for Testing 158 opened frame 12, fetched the mesh once, showed the acquired image and its credit, and retained the 3D scene and overlay on a forced comparison-image 404. Changing the frame label survived rebuild and playback with the same mesh and images. Native impact returned the exact liver sweep pin. Local receipts and screenshots are under `.artifacts/assetkit-liver-wave0/`. [Owning track](../../experiments/ultrasound-sweep/abdomen-tracks.json) |
| HRA liver | `2cee5d27` registers the selected 595,352-byte export. Fresh replay, all eight selectors and 41,470 triangles matched. The Gallery selection resolves through the maintained teaching register. The package remains provisional in the native HRA frame. [Record](../../models/liver/asset.record.json) |

Canonical record tooling landed at `85365926`. Writer regressions cover conflicting pins, missing payloads, recipe input drift, stale plans, concurrent writers and exact repeat application. The real HRA suite covers hydrated and pointer checks, scoped task evidence, the replay input, selectors, and rejection by the s1233 placement handoff. [Writer tests](../../src/assetkit/tests/test_record_sync.py) · [HRA acceptance](../../src/assetkit/tests/test_hra_port.py)

## First ultrasound batch expectation

The abdomen surface-fit recipe reads two BodyParts3D inputs. Both source GLBs retain their original atlas frames. The sweep owns the fit to the case surface. Preserve its output and exercise the actual lesson before assigning the rest of the ultrasound packages.

| Expected package record and native key | Reader input before migration | Placement in the sweep |
| --- | --- | --- |
| `models/skin/asset.record.json` · `anatomy:bp3d:skin@bp3d-envelope-r01:envelope` | `models/skin/exports/bp3d-envelope-r01/skin_source_frame.glb` | Outer envelope used by the display fit. [Source and review](../../models/skin/exports/bp3d-envelope-r01/README.md) |
| `models/skeleton/asset.record.json` · `anatomy:bp3d:skeleton@teaching-economy-r01:skeleton` | `models/skeleton/exports/teaching-economy-r01/skeleton_source_frame.glb` | Right rib landmarks establish the bounds for that fit. [Recipe and export pin](../../models/skeleton/recipes/teaching-economy-r01.json) |
