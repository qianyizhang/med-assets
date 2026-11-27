# AssetKit batch migration

**Wave 1 opens when the HRA liver package port passes the acceptance test below and the Wave 0 changes are merged.** Use the s1233 liver sweep to prove that a lesson can load a governed export. Use the HRA liver to prove that a second maintainer can register an existing package, reproduce its selected bytes, and preserve its readers. These livers have separate sources, frames, and teaching uses.

## Scope and ownership

| Decision | Batch rule |
| --- | --- |
| D1 · Reusable 3D outputs | Port models, multi-part atlases, assemblies, independent rigs, and shared instrument geometry. Lesson owners keep acquisition, motion, simulation, overlays, 2D illustrations, and acquired media. |
| D2–D3 · Package identity | Declare one independently maintained asset per `asset.record.json`. A shared-frame atlas can own several exports. For independent assets under `models/joints` or `models/peripheral_nerves`, put each record in an owning subdirectory and reference the existing payload paths. The metadata fixture retains its own schema. |
| D4–D5 · Metadata-only ports | Preserve editable sources, payloads, local paths, public URLs, and R2 keys. Give new geometry, probe extraction, trims, merges, and archival their own changes with the relevant authoring or recovery evidence. |
| D6 · Consumer ownership | Ultrasound Anatomy, Body Systems, and Gallery each declare 3D references in their own configuration. Frozen builds keep their exact delivery receipts. Existing standalone lessons keep their current paths until a named migration needs them. |
| D7–D8 · Evidence | Use stable IDs and explicit frames. Register newly ported assets and uses as provisional. Preserve rights, exact assessments, their scope, and independently owned selections. Record each unknown source, right, frame, or selector against the affected item. |
| D9–D10 · Delivery | Complete Wave 0 before parallel package PRs. Each package PR owns its records and optional package README. One serialized integration PR per wave owns shared concepts, reader configuration, and the wave coverage result. |

The [design](../src/assetkit/DESIGN.md#decisions) owns the architecture. The [landscape](ASSET_LANDSCAPE.md) inventories candidate packages, including recipe-only and multi-asset directories. Directory counts estimate effort. Each wave measures coverage by exact owner records, exports, and reader pins. Record temporary migration adapters in the integration PR with their owner, remaining readers, and removal condition.

## Record contract

**Identity.** Use three lowercase ASCII kebab-case segments, `<domain>:<lineage-or-subject>:<slug>`. Existing examples include `anatomy:s1233:liver-window` and `anatomy:heart:cardiac-atlas`. The other planned domains are `assembly`, `prop`, and `rig`. Bind each revision/export ID to its repository-relative path, exact SHA-256, byte count, and evidenced part selectors. Keep the source, license, and recipe or replay reference with the package. Use the [s1233 record](../models/liver_s1233/asset.record.json) for a voxel-grid example and the [Cardiac Atlas record](../heart/Cardiac_Atlas_Animated/asset.record.json) for task-specific uses. The accepted HRA record becomes the batch example.

**Coordinates.** Declare the convention of the stored coordinates for every revision and export, with units and axes where known. Preserve source/subject identity separately. Compatibility for placement requires the expected frame or an evidenced source-to-target transform for that use.

| Proposed controlled convention | Evidence required by the consumer |
| --- | --- |
| `glb-y-up-m` | The file uses a right-handed, Y-up convention in metres. Establish patient axes, origin, scale, and placement from package evidence before combining different sources. |
| `voxel-index` | Vertices are voxel indices. Bind case, grid shape, and the complete `rasMmFromVoxel` affine. Applying the affine once yields RAS millimetres. The s1233 handoff checks all three fields. Use the same rule for s1127 or s0189 with their own grids. |
| `blender-z-up-m` | Use for metre-valued authoring coordinates. Record scene scale and the export transform for assets authored in Blender units. |
| `tool-probe-m` | A probe's owner defines its footprint origin, beam and marker axes, dimensions, and placement transform. |
| `unverified-frame` | Name the missing frame evidence in `unresolved`. Provisional registration may proceed. Consumers requiring spatial placement must reject the handoff. |

**Sync.** Extend `assetkit sync` to the canonical record before package authors use it. Plan against the exact record and input identities. An initial registration may fill absent identity fields from verified evidence. An identical repeat must produce no changes. Apply rechecks preconditions and writes the complete record atomically. Reject a stale plan, conflicting existing digest or size, missing payload, or inconsistent duplicate export declaration with the record untouched. Changed geometry needs a new reviewed revision. A matching LFS pointer can corroborate a pinned digest and size in offline CI. Mesh statistics and selector checks require hydrated bytes. [Package change safeguards](../src/assetkit/DESIGN.md#safeguards-for-package-changes)

## Local execution

Integrate on `asset-governance-v1`. A package PR in this specification corresponds to a separately reviewable local commit during this migration. Workers own assigned files; the lead reviews, verifies, and integrates. A passing gate must be present on that branch before dependent packages start. After Wave 0, integrate two or three ultrasound packages and exercise their shared reader before assigning the rest of Wave 1. The existing teaching registers retain the HRA selection and assessment. The HRA package owns the selected teaching export and its pinned rebuild input; the older metadata-cleanup export awaits lineage evidence.

## Wave 0 baseline

Local checkout on 2026-11-28, commit `1b135799`. This table records the starting state. The [local campaign record](../records/campaigns/assetkit-migration.md) owns subsequent results and evidence.

| Item | Evidence at the baseline | Remaining before dispatch |
| --- | --- | --- |
| s1233 lesson integration | The [track](../experiments/ultrasound-sweep/abdomen-tracks.json) pins `anatomy:s1233:liver-window@r01:liver`. Native dependency indexing returns the liver sweep. The [regression suite](../src/assetkit/tests/test_assetkit.py) includes rejection of a shifted grid origin. | Attach or verify the tested revision and results for all [six PRD checks](../src/assetkit/PRD.md#acceptance-checks-for-the-integration), including fresh rebuild, frame 12 playback, author edits, and storage. Confirm merge into the integration base. |
| Canonical record tooling | The current [sync writer](../src/assetkit/build.py) handles `assets.json`. Structural validation alone can succeed for a declaration whose payload is missing. | Merge record sync and machine checks for IDs, frame declarations, artifact identities, and claimed selectors. Preserve the two existing governed identities and the sweep's full-grid check. |
| HRA batch acceptance | The selected HRA export, recipe, and assessment exist. `models/liver/asset.record.json` is pending at this baseline. | Land the metadata-only HRA port and the automated acceptance checks below. Record the passing revision on the integration base. |
| Legacy Governance CLI | Local commit `1b135799` retired the former CLI, modules, and tests. | Track the existing AssetKit interfaces and fixture readers. The old CLI has no outstanding removal step. |

### HRA liver acceptance test

**First package PR:** `models/liver/asset.record.json` registers `anatomy:hra:liver@r02:teaching-economy`. Use the existing HRA female v1.10 exterior in its original frame. Its maintained task is locating the posterior bare area relative to the anterior surface. The s1233 ultrasound reader continues to pin its own mesh. [Package](../models/liver/README.md) · [Credits and license](../models/liver/ATTRIBUTION.md) · [Teaching edition and rebuild](../models/liver/exports/teaching-economy-r02/README.md)

Put the reusable assertions in the tooling PR and exercise them against the actual package port. Run negative cases on disposable copies. Wave 1 requires the following results on the same candidate revision.

| Check | Passing evidence | Failure the test must detect |
| --- | --- | --- |
| Native lookup | `show` with `--native-only` returns `found: true`, the exact asset ID, `models/liver/asset.record.json` as owner record, and the expected revision, export, and path. The asset and any newly recorded use remain provisional. | Removing the owner record or changing the requested export fails the assertion even if legacy discovery finds a liver directory or the CLI exits successfully. |
| Exact payload and replay | Rebuild the [edition recipe](../models/liver/recipes/teaching-economy-r02.json) into a fresh directory. The rebuilt and hydrated maintained GLBs both match the recipe's output SHA-256 and **595,352 bytes**. Hydrated inspection reports **41,470 triangles**. | Missing bytes or a digest mismatch fails hydrated acceptance. A matching pointer passes only the offline identity check. |
| Parts and frame | Inspect the GLB for each claimed selector, including `VH_F_bare_area_of_liver` and `VH_F_capsule_of_the_liver`. Preserve the original HRA frame and the documented limit on registration to s1233 or the body. | Substituting `Liver` for a named node fails selector verification. Supplying the HRA export to the s1233 voxel-grid handoff fails placement. |
| Review, reader, and replay dependency | Trace the exact GLB to task `liver` in the [maintained selection](gallery/maintained-selections.json) and the matching assessment digest in the [teaching register](../reviews/teaching-assessments/current-assessments.json). Preserve the package's [liver/spleen source replay](../assemblies/liver-spleen/recipes/README.md) and the edition recipe's pinned input. | A sibling export, missing replay reference, different assessment digest, or inferred qualification fails. A reader query for the HRA export must never claim the s1233 sweep pin. |
| Writer integrity | Initial sync fills absent identity fields. Applying the same result twice preserves identical record bytes. A dry run reports proposed changes and affected readers. | Modify an input or the record after planning, or change bytes under a pinned revision. Apply must fail and leave the record byte-for-byte unchanged. |

Run this ownership and payload check from the repository root in the project Python environment on a hydrated port candidate. In the baseline checkout it fails at the first assertion.

```python
import json
from pathlib import Path

from assetkit import ShowAssetResult, Workspace, inspect_mesh, verify

ws = Workspace.load(Path.cwd(), include_legacy_adapters=False)
asset_id = "anatomy:hra:liver"
asset = ws.show(asset_id)
assert isinstance(asset, ShowAssetResult), asset
assert asset.asset.id == asset_id
assert asset.asset.source_manifest == "models/liver/asset.record.json"
binding = ws.registry.resolve_export(asset_id, "r02", "teaching-economy")
assert binding is not None
_, revision, export = binding
assert revision.status == "provisional"
assert export.path == "models/liver/exports/teaching-economy-r02/liver.glb"
recipe = json.loads(Path("models/liver/recipes/teaching-economy-r02.json").read_text())
pin = recipe["output"]
assert (export.path, export.sha256, export.bytes) == (pin["path"], pin["sha256"], pin["bytes"])
assert verify(ws.repository, export.path, pin["sha256"], pin["bytes"]).status == "verified"
mesh = inspect_mesh(ws.repository, export.path)
assert mesh is not None and mesh.triangles == export.triangles == 41_470
claimed = {selector for part in export.parts for selector in part.selectors}
assert {"VH_F_bare_area_of_liver", "VH_F_capsule_of_the_liver"} <= claimed
assert claimed <= set(mesh.node_names)
```

Read the maintained assessment and Gallery selection through their owning registers. Native-only lookup tests ownership of the 3D export. The registers supply the evidence and selection pins.

Run the focused AssetKit tests and [applicable repository gates](WORKFLOW.md#verification). Attach the native query assertions, hydrated replay result, rejection results, and tested commit to the port. Confirm the HRA port, tooling, and s1233 integration are merged before assigning Wave 1 packages.

## Package and wave acceptance

1. **Before assignment**, list expected package record paths, asset/revision/export IDs, payload paths, and each intended consumer config and pin. Mark recipe-only inputs, deferred packages, and missing geometry with their reason and owner. Use this list as the independent expectation for the wave.
2. **Package PRs** may cover one to five packages. Add only package-local records and optional README updates. Assert the native record and exact export identity for every assigned item. Check pointer identity in shallow CI and claimed mesh parts on a hydrated checkout. Run the focused tests and offline gate. Preserve current package-specific gates.
3. **The integration PR** wires the named reader configs and adds needed concepts. Query `impact` on each exact export and assert `found: true`, the expected owner path, and the reader's asset/revision/export pin. Check the reader through its normal entry point. For records with no runtime reader, document the known replay, evidence, or retention use. Unknown targets and missing expected pins fail acceptance.
4. **Close the wave** by comparing its expected set with owner records and real readers at the tested revision. Report unresolved and deferred items individually. Count a Gallery item only when its record, export identity, and intended Gallery entry agree. The default compiler also lists legacy discoveries.

| Wave | Scope | Exit condition |
| --- | --- | --- |
| 0 · First package | s1233 integration, record tooling, and one HRA liver port | All Wave 0 requirements above pass on the merged base. |
| 1 · Ultrasound Anatomy | Existing reusable exports for named sweeps, including Workshop s1233, endocrine locator, and organ models in the [inventory](ASSET_LANDSCAPE.md). | Every assigned export resolves through its declared sweep config. List acquisition-owned inputs and remaining gaps. Probe extraction and new gap geometry have separate authoring PRs. |
| 2 · Body Systems | Existing system assemblies, organ exports, breathing and cardiac packages; integrate the named Body Systems and Gallery readers. | Each assigned stop or plate resolves its intended export. Verify its owning config and any maintained Gallery selection. |
| 3 · Gallery tail | Remaining maintained 3D packages, including independent joint and nerve assets. Standalone lessons keep their existing references until edited. | Compare expected owner-record/export pairs and intended Gallery entries. Record each deferred item and verify affected public paths through their existing owners. |

## Post-port cleanup

Review candidates after Wave 1 for ultrasound-specific work and after Wave 3 for Gallery-wide changes. Each change follows [retention and recovery](WORKFLOW.md#retention). Query `tools/verify.py retained` on exact files, check dynamic and external readers, record each reader's disposition, and verify any required restore before removal. Publication, upload, and deletion follow the existing authorization rules.

| ID | Separate work | Evidence needed |
| --- | --- | --- |
| CLN-01 | Consider cold storage for infrequently replayed Blender and raw sources. | Named recovery use, verified archive, and successful restore of exact source bytes. |
| CLN-02 | Triage historical review images. | Current claims keep their bound evidence; superseded evidence needs a recorded disposition. |
| CLN-03 | Generate routine sweep frames and overlays during assembly. | Identify and preserve frozen lesson bytes and active review evidence. |
| CLN-04 | Evaluate heavy GLB splits against named runtime loads. | Compare measured load savings and matched views for the teaching task. Package LFS size includes sources and previous editions. |
| CLN-05 | Evaluate paired kidney, lung, eye, salivary, and cardiac lineages for consolidation. | Establish shared source, registration, consumer parity, and replay before merging. |
| CLN-06 | Evaluate a local `assets/` rehome or R2 namespace changes. | Check import identities, public URLs, frozen receipts, and recovery with the owning systems. |
| CLN-07 | Review the metadata fixture and remaining adapters when their readers have migrated. | Keep `assemblies/liver-spleen` for liver/spleen replay and `assemblies/bladder-pancreas` for bladder/pancreas replay. Gallery lists both `heart/exterior-presentation-r01` exports in its [library](../sites/anatomy-gallery/app/src/content/gallery/library-packages.json) and [delivery index](../sites/anatomy-gallery/app/src/content/assets/delivery-index.json). Migrate and verify each reader before considering retirement. |
| CLN-08 | Add scoped hydration for named consumers or assets if needed. | Prove the restore path for LFS or cold members and verify the requested identities. |
