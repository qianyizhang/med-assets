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
