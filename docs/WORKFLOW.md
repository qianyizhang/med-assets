# Architecture and workflow

## Ownership

Start with the asset ID and its owning directory. Read the export README and
linked review before changing an asset; presence in the tree is not approval.

| Owner | What belongs here |
|---|---|
| `models/<asset>/` | Individual 3D assets: editable `source/`, purposeful `exports/`, and asset-owned `recipes/` for building, rendering and checking. |
| `assemblies/<name>/` | Same-frame compositions and recipes that intentionally operate on several assets. Preserve registration assumptions. |
| `body/`, `heart/` | Imported atlas products with their own coordinate, texture and publication contracts. Keep public export paths stable. |
| `diagrams/<name>/`, `lessons/<name>/` | Editable 2D aids and runnable teaching experiences. Their sources and checks belong with the product. |
| `sites/<name>/` | Derived reports and Site authoring. Asset records remain authoritative; keep publishing checkouts and inline media payloads ignored. |
| `sources/` | Shared external inputs, licenses, acquisition identities and unique recovery material. |
| `reviews/<asset>/` | Current decisions, unresolved defects and the exact evidence those claims need. The owning record defines scope. |
| `tools/` | Shared format, integrity, transport and verification operations. Asset parameters stay with the asset. |
| `tests/` | Shared behavior/security regression suites and minimum fixtures. Asset replay/check commands live beside their recipes. |
| `gallery/`, `ci/`, `transport/` | External-viewer integration, guarded runtime execution, and content-addressed delivery manifests. The deployed viewer is a separate source owner. |
| `metadata/`, `SHA256SUMS` | Immutable original import identities and explicit current-file exceptions. |

Browse directories rather than maintaining a parallel global asset registry.
Keep one export per purposeful variant; another revision needs a named consumer,
replay dependency or unique evidence. Internal recipe snapshots may retain their
original relative layout when exact reconstruction uses it. Build into a fresh
output directory; never use a delivered export folder as scratch space.

## Asset admission

Reuse or improve existing assets before adding a maintained variant. An addition
needs evidence that existing assets cannot meet its purpose and quality, or that
adaptation would break another named use which cannot coexist through parameters,
materials, overlays or composition. A demonstrably better replacement is welcome. Avoid destructive or lower-quality
adaptation merely to avoid an addition.

Before committing to expansion, record in the existing issue or owning asset:

- Intended use, required quality, concrete improvement and compared asset IDs.
- Inspected matched output or relevant measurements supporting reuse, selective
  integration, adaptation or the exception. Availability and novelty are insufficient.
- Source/export/storage and review cost, maintenance owner, and consumers migrated
  by a replacement; preserve other uses and required source/recovery material.

Link this decision in the PR. Missing or unsupported admission evidence blocks
ready/merge. This gate does not authorize deletion, publication or merge and does
not reopen settled work. A source is evidence, not anatomical ground truth.

## Verification

Use **Python 3.11+**, Git and Node.js 18+. Ordinary offline checks require no
third-party Python packages, network, rendering or media download:

```sh
python3.12 tools/verify.py offline
```

The command discovers indexed and added `tests/test_*.py` and
`tests/review_records/test_*.py`. Missing indexed suites, empty suites, missing
imports, skips, expected failures, fixture errors and partial execution fail.
Stage deliberate file retirements before running index-based checks. There is no
historical test-count or filename retention gate. Plain unittest discovery is not
the complete command.

Offline mode validates current text, LFS pointer syntax/OID/known sizes,
content-addressed transport manifests and explicitly selected foundation records.
`FOUNDATION_PATTERNS` and `PAYLOAD_CHECKS` in `tools/verify.py` own selection.
It does **not** perform exhaustive payload-byte verification or establish geometry,
pixels, runtime or remote availability. Selected suites may hash local hydrated
media. A generic `schemaVersion: 1` does not select a record family.

After actual LFS bytes are available:

```sh
python3.12 tools/verify.py payload-integrity
```

This includes offline mode, hashes and sizes every indexed LFS payload, verifies
foundation evidence bindings and runs the selected package validators. Unresolved
pointers fail. Python `-O` is refused because retained package checks use assertions.
This is byte identity and selected package consistency, not a clinical/visual pass.

Changing the UFF dental tool also requires its separate full suite, including the
pinned actual GLB hash. Use an isolated environment with
`models/dental_specimens/uff_tomo1b/recipes/requirements-uff.txt`, then run `tools/verify.py dental`. Missing
native dependencies are unavailable coverage, never a skipped pass. Dental tests
are not included in offline or payload-integrity totals.

Choose additional tests by changed behavior. Major refactors/releases require
full applicable checks. Run representative source→export→clean reimport and
consumer/failure recovery journeys when those paths change. Record unavailable
inputs and exact artifacts; use existing valid evidence when inputs are unchanged.
No mass font, dependency or historical-recipe normalization is required.

Recipes document their prerequisites. For example,
`models/esophagus_wall/recipes/replay.py --output NEW_DIRECTORY` needs Blender
4.3.2, Pillow and its recorded Linux fonts. Read `replay-result.json` and inspect
pixels separately; process exit alone does not establish the expected GLB hash.
UFF reconstruction additionally needs its pinned public ZIP.

## Import and source integrity

`SHA256SUMS` and `metadata/asset-manifest.json` bind the 2026-10-22 import:
591 extracted files, originally 370,698,859 bytes. Earlier collection records
retain archive checksums and original source identities. Preserve these bytes;
do not regenerate history to conceal current edits.

Current checks apply to imported paths still indexed. Removed paths remain in
historical provenance. A missing indexed file fails. Changes to retained imported
files need `metadata/current-import-overrides.json`: original/current SHA-256,
reason and actual change commit; an LFS change also needs `currentBytes`.
`shasum -a 256 -c SHA256SUMS` checks the original snapshot, not today's tree.
Change-commit fields record provenance; the verifier does not establish ancestry.

Preserve coordinate frames, transforms, material/texture dependencies and
source→export identities. Keep source-specific attribution and full licenses;
there is no repository-wide asset license. Public-source research and authorized
evidence may be committed; credentials, private/signed URLs, conversations and
personal/internal absolute paths may not.

## Review records

Use the existing package's record and validator. Do not add a second registry.
Foundation v1 records are validated by `tests/review_records/validate_record.py`:

- Immutable `id`, `assetId`, `variantId`, ISO8601 `reviewedAt`, `schemaVersion: 1`.
- `artifact: {file, sha256}` and evidence `{file, sha256, artifactSha256, kind}`
  bound to the exact export. Comparisons can bind different artifacts explicitly.
- Independent `technical`, `visual`, `anatomy`, `runtime` gate status/scope.
- `failureSummary` with failure, cause, fix, retest and lesson; label hypotheses.
- Specific limitations, missing structures and remaining validation.

Statuses are `unreviewed`, `unverified`, `passed`, `pass-with-limitations`,
`reference-screened`, `failed`, `needs-review`, `needs-revision`, `not-applicable`.
Reference screening is not specialist approval. Translation of a whole organ is
not physiological deformation; motion needs sampled transform/rig/deformation
checks with explicit coverage.

Bounded migration receipts, scoped decisions, accounting and runtime records
retain their own validators. Foundation validation checks shape, containment and
identities; it does not assess anatomy, pixels, rights or remote availability.
Salivary geometry/failure checks need Blender and their pinned source scene.

## Visual comparisons

Prioritize anatomical/geometric validity, technical correctness and usefulness,
then appearance and measured runtime performance. Document source deviations and
inferred reconstruction. Derive tolerances from source resolution/intended use;
triangle identity or exact source pixels are not universal anatomy gates. Desktop
is the primary target; efficiency limits are soft unless a concrete use requires
them. Before simplifying geometry, demonstrate the benefit and assess quality cost.

Review clean reimports of actual exports at matched camera, scale, projection,
lighting, exposure and background. Bind artifact/evidence hashes. Geometry
identity after material edits requires mesh/transform comparison; a file hash
alone is insufficient if bytes changed. Record tolerances for decoded comparisons.

Show labelled **Original / Updated** whole context and relevant detail, with a
short what/why caption. Every close-up needs an overview crop locator, matched crop bounds and zoom.
Keep labels and anchors legible at the intended issue/PR display size. Anchor
labels to visible evidence and use complementary views for hidden structures.
Distinguish source annotations, inferred views, illustrative colors and fresh
rerenders from validated anatomy or historical images. Check legends/materials
across views and inspect grayscale readability; that is not accessibility approval.
Measure bytes, triangles and build cost separately from actual runtime performance.

Asset and visible-feature PRs embed representative authorized matched views;
docs/code-only refactors state screenshots are not applicable. Reuse valid evidence
instead of recapturing it. Image publication still needs authorization.

## Runtime and delivery boundaries

The main-only browser workflow remains separately guarded. Offline Node VM tests
exercise actual candidate modules with API doubles; they do not test WebGL or
BFCache. Candidate camera CPU tests need the exact vendored inputs pinned in
`tests/candidate_camera/vendor-binding.json`; run `run_cpu.py --vendor-dir PATH`
when the current camera source changes. It executes the incorporated viewer Fit
body; `--baseline` retains the historical failure witness. Neither run downloads anything.

`ci/glb_runtime_fixture.py` loads the hash-pinned heart expectations referenced by
`ci/glb-runtime-fixture.json`; sparse checkout must include those inputs. Preserve
source, animation and track-count checks and the independent snapshot checks.
Keep failed/limited runtime receipts distinct from later passes.

The ordinary PR workflow has read-only contents access, pinned checkout,
`persist-credentials: false`, no secrets/uploads and no media hydration. Bounded
LFS transport retains source-host allowlists, size/hash limits and fresh readback.
Follow [transport instructions](../transport/README.md) before authorized upload.
Native download success does not authorize uploads or remove transport controls.

Unavailable live viewer testing alone does not block medical/dental PR delivery
or an otherwise authorized merge. Required CI, offline render review, technical
checks, execution/security guards and known defects still apply. Record runtime
as `unverified` until tested. Never spoof CI flags or bypass a runtime guard.
Technical, visual, anatomical/clinical, runtime and publication gates are separate.

## Retention

Retain canonical editable inputs/current exports, licenses, source identities,
replay recipes, meaningful decisions and exact evidence for current claims or
unresolved defects. Keep unique recovery material independently of Git history.

Use ignored `.artifacts/<outcome>/` for scratch renders, routine receipts, logs and
audit dumps. One durable bundle per meaningful outcome, with its README explaining
revision, results, limits, consumers and retention. Do not duplicate inventories,
source/media or per-step receipts. Keep hashes where executable integrity uses them.

At closeout, move decisions and defects to their owners, then delete spent output.
A rejected approach needs its reason and remaining risk, not every failed image.
Trace imports, dynamic discovery, links, packaging, public URLs and symlinks before
removal; repair readers and narrow claims whose evidence is retired. Review temporary
bundles after 30 days; an extension needs an active use and next review date. No
automatic janitor or deletion ledger is required.

## Contribution and delivery

Use one bounded issue for nontrivial work: problem, impact, evidence, acceptance
and scope. A tiny self-contained fix may use its PR instead, with the reason.
Track local/unpushed work, validation pending and delivery blocked separately,
with recoverable branch/commit and next action. Preserve paused and cancelled work.

Open a draft PR after concrete progress. Link issues without auto-closing partial
acceptance. Record changed scope, commands/rationale, exact tested revision,
results and limits; for generated/large artifacts include source, consumers and
retention reason. Follow the [shared GitHub delivery guide](https://github.com/qianyizhang/repo-kit/blob/main/user/practices/github.md).

Iterate on supported defects; stop when acceptance is met. Mark ready only with
scoped evidence and applicable checks. Merge/publication need applicable authority.
Close issues only after acceptance, or explicitly as not planned; neither status
alone authorizes deletion. After authorized merge, update each relevant issue with
delivered scope, checks and remaining work. Split oversized outcomes by independently
closable acceptance, not mechanical commits; do not invent backlog work.

Comparison guidance adapts [lookdev](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/lookdev/SKILL.md)
and [qa-review](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/qa-review/SKILL.md),
blender-skills contributors © 2026, [MIT](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/LICENSE).
