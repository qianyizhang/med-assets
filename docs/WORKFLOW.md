# Architecture and workflow

## Ownership

| Owner | Scope |
| --- | --- |
| [models](../models/) | Individual 3D assets with editable inputs, purposeful exports and asset-owned recipes. |
| [assemblies](../assemblies/) | Multi-asset compositions and registration. |
| [body](../body/), [heart](../heart/) | Imported atlas products, coordinate frames and stable public export paths. |
| [diagrams](../diagrams/), [lessons](../lessons/) | 2D aids and runnable teaching products, with their sources and checks. |
| [reviews](../reviews/) | Current decisions, unresolved defects and exact supporting evidence. |
| [sources](../sources/) | Shared inputs, licenses, acquisition identities and unique recovery material. |
| [metadata](../metadata/) | Original imports and explicit current-file exceptions. |
| [tools](../tools/), [tests](../tests/) | Shared operations and regression suites. Asset parameters and replay commands stay with the asset. |
| [gallery](../gallery/), [ci](../ci/), [transport](../transport/) | External-viewer integration, guarded runtime and content-addressed delivery. |
| [sites](../sites/) | Derived reports and Site authoring. Publishing checkouts and inline media payloads stay ignored. |

- **Discovery** · Start at the asset directory, export README and linked review. Use directory discovery as the inventory.
- **Variants** · Keep exports with a named use, replay dependency or unique evidence. Preserve snapshot layout where replay depends on it.

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
- **Authorization** · Deletion, publication and merge require their own authority.

## Verification

**Runtime** · Python 3.11+, Git and Node.js 18+. Run without Python `-O`.

| When | Gate | Acceptance |
| --- | --- | --- |
| Every change | `python3.12 tools/verify.py offline` | Offline regressions, import references, LFS identities, transport manifests and selected foundation records. Selected suites may inspect local media. |
| Broad changes with hydrated LFS | `python3.12 tools/verify.py payload-integrity` | Offline gate plus all indexed LFS bytes, foundation evidence bindings and selected package checks. Unresolved pointers fail. |
| UFF dental changes | `python3.12 tools/verify.py dental` | Separate suite including the actual pinned GLB hash. Use an isolated environment with [UFF requirements](../models/dental_specimens/uff_tomo1b/recipes/requirements-uff.txt). Missing dependencies leave coverage unavailable. |
| Changed recipes, consumers or recovery | Owning recipe and stable entry points | Representative source → export → clean reimport, consumer behavior and changed failure paths. Major refactors and releases need full applicable checks. |

- **Index** · Stage deliberate retirements before checks. [Verifier](../tools/verify.py) owns suite discovery, selection and failure rules.
- **Evidence** · Bind checks to exact inputs and outputs. Reuse evidence for unchanged inputs. Record unavailable checks. A replay exit records process completion. Verify output identities and inspect pixels separately.
- **Scope** · Offline coverage is selective. Payload coverage proves local byte identity and selected consistency. Geometry, pixels, anatomy, runtime and availability require their own evidence.

## Import and source integrity

| Record | Contract |
| --- | --- |
| [Original checksums](../SHA256SUMS), [import manifest](../metadata/asset-manifest.json) | Immutable 2026-10-22 import, 591 extracted members. Earlier records retain original archive identities. |
| [Current overrides](../metadata/current-import-overrides.json) | Changed indexed import paths record original/current hashes, reason and actual change commit. LFS also records `currentBytes`. Missing indexed paths fail. Retired paths remain in historical provenance. Commit fields are provenance declarations. |

- **Asset identity** · Preserve coordinates, transforms, materials, textures, source → export bindings, attribution and full source-specific licenses. See [source records](../sources/).
- **Public tree** · Use public-source or authorized evidence. Keep credentials, private/signed URLs, conversations and personal/internal paths outside Git.

## Review records

- **Owner** · Use the package record and its validator. [Foundation v1 validator](../tests/review_records/validate_record.py) owns schema, status values, containment and identity checks.
- **Evidence** · Use immutable review identity and exact artifact/evidence bindings. Bind each comparison image to its actual artifact. Record gate scope, missing structures, limits and remaining checks.
- **Metadata-only exports** · [Shared replay, patches and exact reviews](../reviews/accounting/2026-10-23/README.md).
- **Failures** · Record observed failure, cause or labeled hypothesis, fix, retest and lesson.
- **Claims** · Technical, visual, anatomical/clinical, runtime and publication status are independent. Reference screening has its own scope. Motion claims need sampled transform, rig or deformation evidence for the claimed behavior.

## Visual comparisons

### Body-system gallery rubric

Score the **specific export, part selection and teaching task**. Name the
target structures, the relationship a learner should see and the closest
intended view. A whole-body locator, a sectional diagram and a registered
scan surface can each earn full marks. Each makes a different promise.

| Axis | What to inspect | Evidence for 3 / 4 |
| --- | --- | --- |
| Fidelity to evidence | Identify the source, laterality, frame, scale and protected landmarks or junctions. Mark inferred walls, routes, offsets and magnification where the learner sees them. | **3** · Clean import preserves the named landmarks and intended relationship. **4** · A source comparison also bounds the largest relevant change, including the most vulnerable small part. For a schematic, check the claimed spatial order, contacts and openings against its reference and against the exported geometry. |
| Form and surface | Inspect the silhouette, varying cross-section, transitions, cut faces and grazing highlights. Look for repeated stock shapes, flat facets on curved anatomy, slice terraces and collapsed thin walls. A planar section face can be intentional. | **3** · The target reads as the intended structure in both views at display size. **4** · It also holds up at the declared close-up. A reviewer can point to the distinguishing shape or interface and find no distracting artifact there. |
| Teaching readability | Try the named action before reading the legend. Identify, trace or isolate each target in the default view, then check its relation to its neighbors in a second view. Inspect a grayscale copy and use shape, order, labels or a section where colors converge. | **3** · The view pair supports the task and the named parts can be isolated. **4** · The primary teaching view makes the critical relation visible, another angle confirms it, and the task survives removal of hue. Record the targets found or the route followed. |
| Mesh economy | Count triangles, GLB primitives and connected pieces **per named part**. Report bytes at comparable export scope. Inspect a thin, highly curved or shared boundary on the clean import. | **3** · The distribution is explained by visible features, selection, or motion, with no obvious wasted or starved region. **4** · A measured comparison, such as a lighter candidate or an explicit sampling-error test, shows the benefit and bounds the loss. Extra triangles can earn full marks when they resolve a named defect. |

Use integer scores. **0** means a missing or contradicted requirement, **1**
a defect that dominates the teaching view, and **2** a usable result with a
specific visible or evidentiary limitation. Mark missing evidence **unrated**
and omit the total. Report all four scores with one observation each. A
review target is **at least 3 on every axis**. Use the total out of 16 to
compare iterations on the same task. A wrong side, lost landmark, falsely
continuous route, corrupt export or untraceable source blocks acceptance at
any total. Clinical and runtime verification retain their own status.

For the gallery palette, give the teaching target the clearest value or
silhouette contrast. Subdue context while keeping its orientation landmarks
legible. Differentiate a cut face from the intact exterior. Add gloss,
roughness variation or surface relief when it helps identify a tissue or
boundary in the named view. Test highlights on pale structures and check
the grayscale image for targets that merge with their neighbors.

**Soft geometry guidance.** Start with one selectable part per teaching
role. One material primitive often suffices for a homogeneous surface.
Multiple pieces can be correct for a source label, and extra primitives
can distinguish a wall from its section face. Record those reasons.
For a static teaching part, a few hundred triangles can describe a simple
sheet or short tube. A few thousand can describe a curved organ, a fold
or a cut rim. Above roughly 10,000 triangles on one context organ, try a
lighter copy and compare the closest intended view. These are prompts to
inspect the mesh. Branch networks, preserved scan detail and deforming
surfaces can justify substantially different budgets.

Choose edge length by local curvature and viewing distance. On a smooth
outline, aim for about one display pixel or less of chord-to-curve error
at the intended close-up. Wide planar faces can use long edges. Spend
samples where the outline turns or two surfaces meet. For a scan derivative,
report voxel spacing, component changes, a typical and a worst-case surface
deviation in physical units. Inspect the worst small structure separately.
Distinguish image aliasing from geometry by inspecting a full-resolution
render at 1:1 and a second orientation. Rerendering at higher resolution
can fix a jagged image edge. Terraces that follow the model across views
call for a source-bounded geometry change.

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
| Offline PR CI | [Workflow](../.github/workflows/offline-verification.yml). Read-only checkout and offline gate. |
| Viewer offline integration | [Gallery](../gallery/). Actual candidate modules with API doubles. For camera changes, run the [CPU test](../tests/candidate_camera/run_cpu.py) against pinned vendor inputs. WebGL and BFCache require runtime evidence. |
| Main-only browser runtime | [Guarded workflow](../.github/workflows/firefox-glb-runtime.yml) and [fixture](../ci/glb-runtime-fixture.json). Use only the guarded entry point. Preserve pinned expectations, source/animation/track checks and separate receipts for failed, limited and passing runs. |
| Missing live viewer access | Mark runtime `unverified`. Medical/dental delivery and authorized merge may proceed when other required checks, reviews, guards and known defects are satisfied. |
| Media transport | [Transport acceptance](../transport/README.md#upload-acceptance) covers routine local uploads and guarded delivery. |

## Retention

- **Keep** · Canonical editable inputs and current exports, licenses, source identities, replay, current decisions and exact evidence for active claims or defects. Keep unique recovery material independently of Git history.
- **Scratch** · Fresh ignored `.artifacts/<outcome>/` directories. Keep one durable bundle per meaningful outcome with revision, result, limits, consumers and retention. Move accepted decisions and remaining defects to their owners.
- **Retire** · Check imports, discovery, packaging, links, public URLs and symlink targets. Repair readers and narrow claims that lose evidence. Retire spent output after recording its outcome. Review temporary bundles after 30 days. Extensions need an active use and next review date.

## Contribution and delivery

| Outcome | Evidence |
| --- | --- |
| Bounded scope | Check open PRs before broad changes. Record the problem, impact, evidence, acceptance and scope in the issue. A self-contained small fix may use its handoff or PR. |
| Reviewable change | Use a scoped commit on the current branch for local Mac development. Follow the shared GitHub guide for cloud and remote work. Link open work and record the exact tested revision, checks, results and limits. For large or generated files include source, consumers and retention. |
| Accepted delivery | Meet the applicable gates and obtain any required merge or publication authorization. Verify publication through the affected entry points and apply the transport acceptance for asset uploads. Close issues on accepted outcomes or explicit retirement. |
| Paused or blocked | Recoverable branch/commit, missing input or decision and next action. Preserve unrelated and paused work. |

[Shared GitHub delivery guide](https://github.com/qianyizhang/repo-kit/blob/main/user/practices/github.md)
