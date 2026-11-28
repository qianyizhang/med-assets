# AssetKit product requirements

Prove that a reusable 3D export can be rebuilt, verified, and loaded by an existing lesson. An asset maintainer should be able to trace that lesson before changing the export. The [design decisions](DESIGN.md#decisions) set the ownership and retention rules.

## Liver sweep pilot

Use the existing **Oblique portal view** at frame 12 of the liver sweep. AssetKit supplies the s1233 liver surface to the 3D scene. The sweep still computes the probe pose, simulated B-mode, and overlay from its acquisition inputs. The acquired panel shows an epigastric view alongside the modeled right subcostal view. [Liver track](../../experiments/ultrasound-sweep/abdomen-tracks.json) · [Acquisition recipe](../../experiments/ultrasound-sweep/build_abdomen.py) · [Acquired reference](../../experiments/ultrasound-sweep/research/hepatopancreatic.json)

```text
Pilot handoff

AssetKit rebuilds and verifies one liver surface
                       │
                       ▼
Existing liver sweep config pins that export
                       │
                       ▼
Existing player opens “Oblique portal view” (frame 12)
  3D scene       Load the verified liver surface and place the probe
  Simulated scan Use the sweep pose, CT and masks to produce the overlay
  Comparison     Read the acquired panel from its existing source catalog
```

### What belongs where

| Item | AssetKit scope | Pilot treatment |
| --- | --- | --- |
| s1233 liver surface | Maintain one reusable export with a recipe, exact identity, source-mask binding and coordinate frame. | Start with the packed liver mesh that the sweep already loads. Reuse the existing mesh-generation routine for an asset-only rebuild. Preserve the s1233 voxel frame and scale used by the scene. |
| Shared curved probe geometry | An independently reusable instrument belongs in the 3D registry. | Keep this pilot to one migrated export. Continue loading the probe from the existing shared geometry builder. |
| Portal and splenic veins, cava, gallbladder and fitted exterior | Consider separate exports when independent reuse warrants them. | Keep the existing sweep inputs and fitting recipe. Preserve source distinctions between s1233 anatomy and the fitted atlas exterior. |
| Probe poses, imaging field, CT sampling, overlay and player | The sweep owns acquisition and playback. | Keep the existing track, builder, generated receipt and player. The scan still uses the CT and masks. The 3D display mesh is a separate input to the player. |
| Acquired WebP, credit and license | The source catalog owns acquisition media and its reuse terms. | Keep the catalog and the sweep's comparison choice. Surface the different imaging window in the existing viewer. |
| Review and delivered bytes | AssetKit can trace evidence for the exact 3D export. | Keep frame and lesson evidence with the sweep. Use existing retention and release rules for any byte-pinned output. |

### Reference in the existing sweep config

The example shows the reference in the existing `liver` row in `abdomen-tracks.json`. The [owning asset record](../../models/liver_s1233/asset.record.json) supplies the export path, digest, and grid. The sweep compares the case, shape, and voxel-to-RAS-millimetres affine with its [pinned case inputs](../../assemblies/workshop-s1233/inputs.json). Its delivery receipt captures the resolved digest for the frozen lesson build.

```json
{
  "id": "liver",
  "sceneAssets": {
    "liver": {
      "asset": "anatomy:s1233:liver-window",
      "revision": "r01",
      "export": "liver"
    }
  }
}
```

The scene builder and AssetKit's read-only dependency index consume that same reference. Assembly rechecks the staged mesh against the exact export. The acquisition pipeline continues to own `sweep.js`, `scan-12.webp`, `section-12.webp`, and the comparison link to `liver-12`.

### Acceptance checks for the integration

| Check | Observable result |
| --- | --- |
| Rebuild one 3D export | The existing s1233 mask produces the liver surface in a fresh directory. Record the source, recipe, frame, output digest, bytes and supported mesh statistics. Compare to the existing mesh by digest or by the owner's recorded geometric and spatial tolerances. |
| Resolve through the normal builder | The sweep resolves the configured revision and export to verified local bytes. Missing bytes, a pointer-only artifact, a wrong digest, or an incompatible frame blocks the handoff with a specific diagnostic. |
| Exercise frame 12 | The existing player opens the same pose, simulated scan and overlay, and labels the acquired comparison with its own credit and window. With the reference image unavailable, the 3D view and simulated scan still work. |
| Test what a lesson author can change | Change a keyframe label or comparison in the sweep-owned config and replay the lesson. The same asset revision and digest still resolve. There is one declaration for the 3D dependency. |
| Trace the real reader | AssetKit's `impact` identifies the live sweep config as an indexed reader of the exact export. An unresolved reference is visible, and the recorded dependency carries no implied anatomical or teaching qualification. |
| Bound the storage cost | Record the 3D export's size and load count. List any new retained payloads and their named uses. Keep routine frames and overlays in the build output. |

Use a local replay to compare against the current sweep. Record the tested revision and exact inputs, and identify any scientific or clinical checks that lack evidence. Follow the repository [verification gates](../../docs/WORKFLOW.md#verification) and the sweep's [replay, assembly and playback checks](../../experiments/ultrasound-sweep/README.md#replay).

## Existing interfaces and migration

| Workflow | Current entry point | Pilot use |
| --- | --- | --- |
| Discover and inspect 3D assets | `assetkit find` and `assetkit show` | Inspect the maintained identity, revision and selectors. |
| Build and inspect an export | `assetkit build` and `assetkit sync` | Use package recipes. Verify the output identity and named dependencies before updating a maintained revision. |
| Validate and assess delivery | `assetkit validate`, `assetkit bundle`, `assetkit economy` | Use declared plans for planning and check artifact identity at the actual 3D handoff. |
| Trace dependencies | `assetkit impact` | The owning sweep appears as a reader of the exact export. |
| Inspect downstream projections | `assetkit compile --target gallery` or `--target r2` | Keep Gallery selection and transport admission with their current owners. |

1. Follow the [existing pilot fixture](pilot/README.md) for metadata-only checks. It illustrates declared costs and anatomy gaps. The liver sweep above is the integration pilot with real bytes and an existing player.
2. Complete the single-export pilot before extending it to the shared probe or other anatomy. Use its results to decide how much indexing and build integration authors actually need.
3. Bring a second real consumer across the same interface when there is a maintained reuse case. Expand asset coverage through existing package owners. Evaluate shared lesson tooling when two workflows need the same behavior.
