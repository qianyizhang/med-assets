# Review record contract (foundation v1)

This small contract supports later organ-sized imports. It is not a claim that the
full collection has already been migrated or passed. No catalog is introduced by
this foundation. Existing package records stay unchanged.

## Format selection

`schemaVersion: 1` is local to a record family; it does not declare every JSON
document to be foundation v1. Choose a validator by the package and record's
purpose, not by that number alone.

| Family | Validator and scope |
|---|---|
| Foundation v1 `record.json` in the 2026-10-23 metadata-cleanup and HRA runs | `tests/review_records/validate_record.py`; the 25 existing records are selected explicitly by `FOUNDATION_PATTERNS` in `tools/verify.py`. Offline mode checks shape and text/pointer references; payload-integrity mode checks actual bytes. |
| Bounded migration receipts, including adrenal `bounded-record.json` | Existing package validators, for example `tests/bp3d_glands/verify_bounded_receipt.py`. Identity and migration assertions are package-specific; missing foundation-only fields do not alone invalidate these receipts. The 11 selected package checks are listed in `PAYLOAD_CHECKS`. |
| Scoped decisions, including salivary `decision.json` | Package README, provenance and its own geometry/failure checks. Salivary verification needs Blender and the pinned source scene; it is not covered by foundation validation. |
| Accounting and runtime receipts | Their own checks in `tests/review_accounting/` and `tests/runtime_receipts/`; no new runtime or clinical approval from a metadata pass. |

Other record families are outside the foundation gate. When extending coverage,
add an explicit family selection and its tests; do not rewrite immutable records
or apply foundation fields mechanically. The fixed selector covers those 25
historical paths; new foundation runs need explicit coverage. See [verification
scope](VERIFICATION.md) for what each command actually runs.

## Foundation fields

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
