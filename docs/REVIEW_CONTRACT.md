# Review record contract (foundation v1)

This small contract supports later organ-sized imports. It is not a claim that the
full collection has already been migrated or passed. No catalog is introduced by
this foundation. Existing package records stay unchanged.

Each new record contains:

- `schemaVersion: 1`, immutable `id`, `assetId`, `variantId`, and ISO8601 `reviewedAt`.
- `artifact: {file, sha256}`: repository-relative exact export path and SHA-256.
- `gates`: independent `technical`, `visual`, `anatomy`, `runtime` objects, each
  with `status` and a concise `scope` describing what was actually checked.
- `evidence`: `{file, sha256, artifactSha256, kind}` entries bound to that exact
  artifact. Use separate records for different revisions; do not mislabel a
  before/after montage as a single-artifact image.
- `failureSummary`: concise `failure`, `cause`, `fix`, `retest`, `lesson` strings.
  Label uncertain causes as hypotheses; retain unresolved defects.
- `limitations`: explicit remaining risks, missing structures and unrun checks.

Status vocabulary: `unreviewed`, `unverified`, `passed`,
`pass-with-limitations`, `reference-screened`, `failed`, `needs-review`,
`needs-revision`, `not-applicable`. A technical pass does not promote visual or
anatomy gates. Reference screening is not specialist or clinical validation.
Runtime requires actual supported viewer evidence, not screenshots from Blender.
Motion needs sampled deformation/transform/rig checks and explicit scope;
translation of a whole organ is not evidence of physiological deformation.

`tests/review_records/validate_record.py` checks basic contract shape, path
containment and local hashes only. It rejects unresolved LFS pointer files in
place of payloads. It **does not** assess pixels, anatomy, provenance rights,
remote LFS availability or runtime correctness. A human/reviewer must inspect
those claims independently. Local files must be available before running it.

```sh
python -m unittest discover -s tests/review_records -p 'test_*.py'
python tests/review_records/validate_record.py --root . reviews/ORGAN/RUN/record.json
```

The second command is a path template, not an existing record or passing example.
Only public-source research and authorized asset evidence belong in public
records. Exclude credentials, signed/private endpoints, conversation links and
personal or internal absolute paths. Keep source licensing per package; no
repository-wide license is inferred.

## Comparing asset variants

When a change needs visual review:

- Bind the source, baseline, candidate exports and evidence images to their
  hashes. To claim unchanged geometry, hash the relevant mesh data and compare
  geometry metadata and transforms; if reordering or compression changes the
  bytes, record a reproducible decoded comparison and its tolerances. A whole
  GLB hash alone cannot establish geometry identity after a material edit.
- Compare clean reimports of the actual exports using matching camera position,
  projection and scale, lighting, exposure and background. Record intentional
  differences and inspect the views needed to reveal the changed area.
- Check that material names, colors and legends agree across views. Inspect a
  grayscale view as one readability check; it does not certify accessibility or
  anatomy. Label illustrative colors and retain source limitations.
- Run the documented export/reimport and replay when inputs are available;
  record missing prerequisites and compare relevant hashes, geometry or decoded
  pixels. A proposed geometry change needs a suitable source/reference and
  scale. Technical checks do not promote the separate visual, anatomy, clinical
  or runtime gates.

These practices paraphrase [lookdev](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/lookdev/SKILL.md)
and [qa-review](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/.claude/skills/qa-review/SKILL.md)
from blender-skills contributors, © 2026; [MIT license](https://github.com/arjun988/blender-skills/blob/8f778d2405a214b508d4c7d80742be8e43acdd52/LICENSE).
