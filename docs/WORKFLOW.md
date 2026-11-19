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
