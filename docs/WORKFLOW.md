# Architecture and workflow

## Ownership

### Target layout

| Owner | Scope |
| --- | --- |
| [models](../models/) | Individual 3D assets with editable inputs, purposeful exports and asset-owned recipes. |
| [assemblies](../assemblies/) | Multi-asset compositions and registration. |
| [body](../body/), [heart](../heart/) | Imported atlas packages, coordinate frames and stable public export paths. Package-level pruning can proceed with reader and recovery checks. A major move to `atlases/` is [deferred outside the gallery campaign](../records/work-items/items/AG-ATL-001-rehome-imported-atlases.md). |
| [diagrams](../diagrams/) | Reusable illustrations with their editable sources, generators, exports and checks. |
| [lessons](../lessons/) | Authored teaching sequences and interactions, including plates made for a single lesson. Reference shared diagrams and exact asset revisions from their packages. Body Systems owns its maintained display export here. |
| [experiments](../experiments/) | Bounded trials with their replay, retained results and limits. |
| [reviews](../reviews/) | Findings, unresolved defects and exact evidence, including historical and rejected witnesses. |
| [sources](../sources/) | Shared inputs, acquisition records, licenses and unique recovery material. [Import records](../sources/imports/) hold the immutable import records and current-file exceptions. Single-use authored inputs live with their packages. |
| [docs](../docs/) | Product requirements, shared guides and repository policy. |
| [records](../records/) | Campaigns and work items with scope, acceptance and delivery evidence. |
| [sites](../sites/) | Anatomy Gallery source in `sites/anatomy-gallery/`. Keep report and replay tooling with its maintained collection or historical package. Publishing checkouts and inline media payloads stay ignored. |
| [tests](../tests/), [.github/workflows](../.github/workflows/) | Regression suites and pinned executable fixtures. Browser probes belong under `tests/runtime/` and source checks under `tests/source_checks/`. Workflow definitions own online invocation and guards. |
| [lib/med_assets](../lib/med_assets/) | Shared artifact, teaching and recipe contracts used by repository commands. |
| [tools](../tools/) | Repository-wide commands, including the offline verifier. Package-specific parameters and replay stay with their owners. |
| [transport](../transport/) | Content-addressed delivery, manifests and recovery policy. [Transport tools](../transport/tools/) hold fetch, upload, backup and restore implementations. Keep an old command path where an external consumer requires it. |

- **Discovery** · Start at the asset directory, export README and linked review. Use directory discovery as the inventory.
- **Variants** · Keep exports with a named use, replay dependency or unique evidence. Preserve snapshot layout where replay depends on it.

## Maintaining an asset

| Change | Edit | Verify the result |
| --- | --- | --- |
| Rebuild an export or lesson plate | Start with the package README and its recipe. Keep the selected inputs, camera, tolerances and export identity there. Use the existing [portable](../tools/rebuild_asset.py) or [Blender](../tools/rebuild_mesh.py) rebuild command when it supports the operation. | Replay into a fresh directory. Compare exact output bytes or the package’s declared geometry, motion or pixel tolerances. The [dependency check](../tools/verify_recipe_dependencies.py) follows the maintained recipe inputs. |
| Accept a reviewed teaching task | Put the observation and evidence with the exact export. Preview and apply the [promotion](guides/teaching-assessments.md) to select a starting file or retain an alternative. | `python3.12 tools/maintained_teaching.py --check` resolves every accepted export/task and compares the generated register and scorecard. |
| Make the revision available in Gallery | Declare the package, revision route, rights and teaching evidence in the [Gallery release inputs](gallery/asset-library.md#making-a-release-selection). The compiler assembles the Library, studies and resources for the selected release. | [Build the local release](../sites/anatomy-gallery/README.md#restore-and-build-locally) and check its model, evidence and behavior. Public download and upload admission have their own [transport acceptance](../transport/README.md#upload-acceptance). |
| Restore or retire a file | Check its known readers with `python3.12 tools/verify.py retained PATH`. For archived members, use the [collection restore command](../transport/README.md#restore-an-archived-collection). | Verify the restored bytes, or migrate the remaining readers and exercise them. The [retention policy](#retention) covers public URLs, source records and unique evidence. |

The [artifact module](../lib/med_assets/artifacts.py) owns path checks and file identity. Metadata checks can use an LFS pointer. Delivery and restore verify the actual bytes. [Display derivatives](../sources/display-derivatives.json) bind an output to its source, recipe and expected identity.

### Asset releases

Give new releases of a reusable asset a semantic version (`MAJOR.MINOR.PATCH`) within its lineage. Keep development revision IDs such as `r05`. The package identifies which exact revision and exports a release contains. Existing revision links and review bindings continue to identify those inputs.

Choose the increment by what a consumer must change. A coordinate-frame change that forces a scene to reposition the asset is **major**. Adding an optional shape key while existing controls still work is **minor**. Correcting a surface defect while preserving placement, named parts and controls is a **patch**. Lessons and assessments pin the revision and export they used, even across compatible releases.

Prioritize recovery of the current maintained release, including its editable inputs, replay instructions, attribution and exact exports needed by consumers. A major release is a useful point to select a rollback version. Keep older versions for a named use under [retention](#retention), including a lesson pinned to a patch release. A backup counts as recoverable after a verified restore. [Artifact backup procedure](../transport/README.md#artifact-backups)

## Asset admission

| Decision | Evidence in the issue or owning package |
| --- | --- |
| Teaching goal | Audience, task and observable learner outcome. |
| New asset or variant | Closest asset IDs and matched views or measurements. Show where reuse, adaptation or composition falls short or breaks a named use. |
| Maintenance | Expected improvement, owner, storage and review cost. For replacements, affected consumers, migration and retained recovery material. |

| Deliverable | Acceptance evidence |
| --- | --- |
| Every asset | Editable source or identified inputs, exact export, replay and [credits and terms](#import-and-source-integrity). Cite anatomical claims. Label inferred features, schematics and generated concepts. |
| 3D assembly | Units, axes, laterality, frame or transforms, and authored joins. Clean reimport shows parts alone and together. Claimed routes have visible junctions and traceable continuity. Disclose unresolved gaps, collisions and occlusion. Limit continuity claims accordingly. |
| Related 3D views | Consistent materials, matched-scale isometric and straight orthographic views by default, and sections or alternate angles for hidden relationships. [Visual comparisons](#visual-comparisons). |
| Diagram or lesson | Required relationship visible in the diagram or learner action demonstrated in the running lesson. |

- **Delivery evidence** · Link the admission decision, evidence, applicable checks and scoped review results in the handoff or PR.
- **Ultrasound acquisitions** · Use the [sweep and tour modeling standard](gallery/use-cases/ultrasound-anatomy.md#3d-modeling-standard-for-sweeps-and-tours) when choosing or changing scan anatomy. It defines the acquisition-specific evidence to use with the shared rubric.
- **Authorization** · Deletion, publication and merge require their own authority.

## Blender workflow

| Work | Use |
| --- | --- |
| Explore a cutaway, pose, camera angle or material when the next edit depends on what you see | **Blender MCP.** Open a scratch scene, change one variable at a time and inspect matched views. Read exact Blender coordinates when a rounded scene summary hides millimetre-scale differences. |
| Apply known edits, sweep predefined settings, build exports or verify the result | **Headless Blender.** Use the owning recipe. Batch known previews in one process when practical. On this Mac, request command-specific approval to run the first headless invocation outside the command sandbox. |

Carry an accepted live edit into the owning recipe or editable source. Replay from clean inputs, reimport the generated GLB and review the actual export using the [applicable checks](#verification) and [matched views](#visual-comparisons). Use this workflow's visual review guidance by default. Consider installing the credited `lookdev` and `qa-review` skills individually if the same review steps recur across projects.

### Local Blender MCP setup

The default setup includes the MCP server and Blender add-on. The tested pair is Blender 5.2.3 with [MCP for Blender 2.3.1](https://pypi.org/project/mcp-for-blender/2.3.1/). Use the version named by the owning recipe for headless replay. If `codex mcp get blender` already shows the server, start with step 3.

1. With `uv` installed, install the pinned server and its matching Blender add-on. The last command prints the absolute path to use in Codex.

   ```sh
   uv tool install mcp-for-blender==2.3.1
   blender_mcp="$(uv tool dir --bin)/mcp-for-blender"
   "$blender_mcp" install-addon
   printf '%s\n' "$blender_mcp"
   ```

2. In Codex Settings → MCP servers, add a **STDIO** server named `blender`. Use the absolute executable path and set `BLENDER_HOST=localhost`, `BLENDER_MCP_SAFE_MODE=1` and `DISABLE_TELEMETRY=true` in its environment. For manual configuration, add only the Blender entry to the [Codex MCP configuration](https://developers.openai.com/codex/mcp).
3. Open Blender and enable **Interface: MCP for Blender** under Preferences → Add-ons. In the 3D Viewport sidebar, open **MCP for Blender** and check that the server is running on localhost. Use **Start MCP Server** if needed.
4. Open a fresh Codex chat and ask it to inspect the scratch scene and return a preview. Successful setup returns the scene objects and an image. If discovery works but inspection fails, check that Blender is open and that the sidebar listener is running.

## Verification

**Runtime** · `uv` with Python 3.12 (pinned in `.python-version` and `pyproject.toml`), Git and Node.js 24. Run `uv sync` and `uv run pre-commit install` in a fresh checkout; invoke repository commands through `uv run` (without Python `-O`) instead of adding `sys.path.insert` shims.

| When | Gate | Acceptance |
| --- | --- | --- |
| Every change | `uv run python tools/verify.py offline` | Offline regressions, portable Gallery tests, the maintained recipe graph, all accepted teaching tasks and their generated views, import references, LFS identities, transport manifests and selected foundation records. Runs in a shallow LFS-pointer checkout. |
| Python style, lint & types | `uv run pre-commit run` (`ruff` + `ty` + hygiene hooks) | Enforces formatting, imports, lint, and static type checks defined in `pyproject.toml` and `.pre-commit-config.yaml`. |
| Focused Python tests | `uv run pytest [path]` | Fast local test runner for `pytest` and `unittest` suites (full offline CI still uses `tools/verify.py offline`). |
| Broad changes with hydrated LFS | `uv run python tools/verify.py payload-integrity` | Offline gate plus all indexed LFS bytes, foundation evidence bindings and selected package checks. Unresolved pointers fail. |
| UFF dental changes | `uv run python tools/verify.py dental` | Separate suite including the actual pinned GLB hash. Use an isolated environment with [UFF requirements](../models/dental_specimens/uff_tomo1b/recipes/requirements-uff.txt). Missing dependencies leave coverage unavailable. |
| Dental film production changes | [Film replay checks](../experiments/dental-video-treatments/REPLAY.md) | The ordinary gate pins the retained films, captions and credits. Run the package replay suite explicitly for renderer or production changes. |
| Changed recipes, consumers or recovery | Owning recipe and stable entry points | Representative source → export → clean reimport, consumer behavior and changed failure paths. Major refactors and releases need full applicable checks. |

- **Index** · Stage deliberate retirements before checks. [Verifier](../tools/verify.py) owns suite discovery, selection and failure rules.
- **Evidence** · Bind checks to exact inputs and outputs. Reuse evidence for unchanged inputs. Record unavailable checks. A replay exit records process completion. Verify output identities and inspect pixels separately.
- **Scope** · Offline coverage is selective. The scorecard verifies declared display bindings and source identities. Gallery assembly and serving verify actual display bytes. Payload coverage proves local byte identity and selected consistency. Geometry, pixels, anatomy, runtime and availability require their own evidence.

## Import and source integrity

| Record | Contract |
| --- | --- |
| [Original checksums](../sources/imports/SHA256SUMS), [import manifest](../sources/imports/asset-manifest.json) | Immutable 2026-10-22 import, 591 extracted members. Earlier records retain original archive identities. |
| [Current overrides](../sources/imports/current-import-overrides.json) | Changed indexed import paths record original/current hashes, reason and actual change commit. LFS also records `currentBytes`. Missing indexed paths fail. Retired paths remain in historical provenance. Commit fields are provenance declarations. |

- **Asset identity** · Preserve coordinates, transforms, materials, textures, source → export bindings, attribution and full source-specific licenses. See [source records](../sources/).
- **Public tree** · Use public-source or authorized evidence. Keep credentials, private/signed URLs, conversations and personal/internal paths outside Git.

## Review records

- **Owner** · Use the package record and its validator. [Foundation v1 validator](../tests/review_records/validate_record.py) owns schema, status values, containment and identity checks.
- **Accepted teaching** · Use the [promotion workflow](guides/teaching-assessments.md) to bind an exact owner review to a maintained selection or retained alternative.
- **Evidence** · Use immutable review identity and exact artifact/evidence bindings. Bind each comparison image to its actual artifact. Record gate scope, missing structures, limits and remaining checks.
- **Metadata-only exports** · [Shared replay, patches and exact reviews](../reviews/accounting/2026-10-23/README.md).
- **Failures** · Record observed failure, cause or labeled hypothesis, fix, retest and lesson.
- **Claims** · Technical, visual, anatomical/clinical, runtime and publication status are independent. Reference screening has its own scope. Motion claims need sampled transform, rig or deformation evidence for the claimed behavior.

## Visual comparisons

### Body-system gallery rubric

Use the [teaching-asset rubric](guides/asset-quality.md) for fidelity, form and surface, teaching readability, and mesh economy. The [scan-derived surface refinement guide](guides/scan-surface-refinement.md) covers shape, finish and mesh budget for an interpreted exterior. The [gallery design guide](gallery/design.md) covers discovery, inspection and handoff between collections.

### Evidence for comparison

| Goal | Required evidence |
| --- | --- |
| Valid geometry and teaching use | Source deviations, inferred reconstruction and tolerances tied to source resolution and intended use. Geometry simplification shows benefit and quality cost. Use soft efficiency targets unless the use requires a hard limit. |
| Representative export | Actual export reimported cleanly. Match camera, scale, projection, lighting, exposure and background. Bind artifact/evidence hashes and record decoded tolerances. For material-only geometry claims, compare meshes and transforms. |
| Readable comparison | Labeled **Original / Updated** overview and relevant detail with a short what/why caption. Close-ups use matched crop and zoom and an overview locator. Anchor legible labels to visible evidence. Verify legends and grayscale readability. |
| Bounded claims | Label source annotations, illustrative colors, inferred structures and fresh rerenders. Assess accessibility and runtime separately. Report bytes, triangles and build cost separately from measured runtime. Desktop is the primary target unless scope specifies otherwise. |
| PR evidence | Embed representative, authorized views for assets and visible changes. Reuse valid evidence. Record screenshots as inapplicable for docs-only or nonvisual changes. |

- **Credits** · Adapted from [lookdev](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/lookdev/SKILL.md) and [qa-review](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/qa-review/SKILL.md), blender-skills contributors © 2026, [MIT](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/LICENSE).

## Runtime and delivery boundaries

| Boundary | Owner and completion |
| --- | --- |
| Offline PR CI | [Workflow](../.github/workflows/offline-verification.yml). Every PR runs the read-only offline gate. The [FDI31 source check](../.github/workflows/fdi31-source-verification.yml) is a manual download and byte check for the five staged objects. |
| Viewer offline integration | [Legacy Anatomy Verification fixtures](../tests/viewer/README.md). Actual candidate modules with API doubles. For camera changes, run the [CPU test](../tests/candidate_camera/run_cpu.py) against pinned vendor inputs. WebGL and BFCache require runtime evidence. |
| Main-only browser runtime | [Guarded workflow](../.github/workflows/firefox-glb-runtime.yml) and [fixture](../tests/runtime/glb-runtime-fixture.json). Use only the guarded entry point. Preserve pinned expectations, source/animation/track checks and separate receipts for failed, limited and passing runs. |
| Missing live viewer access | Mark runtime `unverified`. Medical/dental delivery and authorized merge may proceed when other required checks, reviews, guards and known defects are satisfied. |
| Media transport | [Transport acceptance](../transport/README.md#upload-acceptance) covers routine local uploads and manual dispatch of a reviewed LFS manifest on main. |

## Retention

The repository is in beta. Prefer a small, verified iteration that migrates current readers and removes the superseded implementation in the same change. Backward compatibility is a low priority. Use Git history for ordinary retired beta artifacts. Keep an older file, route, shim or manifest entry only for a named consumer, required rebuild or recovery, attribution, import integrity, or evidence supporting an active teaching claim. A link or listing maintained solely for that retired artifact can be removed with it.

- **Keep** · Canonical editable inputs and current exports, licenses, source identities, replay, current decisions and exact evidence for active claims or defects. Keep unique recovery material independently of Git history. [Cold collection archives](../transport/README.md#restore-an-archived-collection) retain infrequently replayed inputs outside the normal checkout. Follow the [artifact backup policy](../transport/README.md#artifact-backups).
- **Derived files** · Keep the canonical input and a reproducible recipe. Generate display and delivery variants during assembly. Track a derivative when it supplies unique review evidence or a named consumer or recovery need requires the file. When a consumer requires exact bytes, verify them on replay or migrate the consumer to its reviewed replacement. Check live delivery before retiring an address used outside the repository.
- **Scratch** · Use ignored `.artifacts/<outcome>/` directories for comparison sessions, trial renders and working close-ups. Where an outcome merits a working bundle, keep one with its revision, result, limits, consumers and retention. Routine trials can expire without backup. Move accepted decisions and remaining defects to their owners, and bind the decisive evidence for an active claim or defect to a tracked record or verified archive. Tests exercise maintained behavior and explicitly selected fixtures. A trial’s appearance in a Development index creates no test or backup obligation.
- **Retire** · Check imports, discovery, packaging, links, public URLs and symlink targets. Repair readers and narrow claims that lose evidence. Retire spent output after recording its outcome. Review temporary bundles after 30 days. Extensions need an active use and next review date.

Run `python3.12 tools/verify.py retained PATH [PATH ...]` from the repository root
to trace exact repository-relative paths. The report checks accepted teaching and
comparison evidence, delivery declarations, the known recipe graph, licenses,
open work items and recovery records. The recorded public index is checked when
its commit is in local Git history. External consumers, dynamic lookups and
current archive availability need separate evidence before retirement.

## Contribution and delivery

Use a [campaign record](../records/campaigns/anatomy-gallery-consolidation.md) for a bounded destination that spans multiple sessions. It records the sequence, unknowns and current frontier. The [local backlog](../records/work-items/backlog.md) leads to open work items. A completed item can live in its campaign record once its ID, evidence and limits are preserved and its readers have moved. Keep standalone records referenced by an assessment or a dependency. Link related GitHub issues and PRs from the work item. GitHub owns the state of those external records. Keep settled requirements and evidence with their existing owners.

| Outcome | Evidence |
| --- | --- |
| Bounded scope | Check open PRs before broad changes. Record the problem, impact, evidence, acceptance and scope in the work item or issue. A self-contained small fix may use its handoff or PR. |
| Reviewable change | Use a scoped commit on the current branch for local Mac development. Follow the shared GitHub guide for cloud and remote work. Link open work and record the exact tested revision, checks, results and limits. For large or generated files include source, consumers and retention. |
| Accepted delivery | Meet the applicable gates and obtain any required merge or publication authorization. Verify publication through the affected entry points and apply the transport acceptance for asset uploads. Close issues on accepted outcomes or explicit retirement. |
| Paused or blocked | Recoverable branch/commit, missing input or decision and next action. Preserve unrelated and paused work. |

[Shared GitHub delivery guide](https://github.com/qianyizhang/repo-kit/blob/main/user/practices/github.md)
