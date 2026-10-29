# Asset and review layout

This layout began as an additive foundation, not a completed migration. That
foundation left the existing `heart/`, `body/`, `metadata/`, import checksums and
Git LFS links unchanged and added no model or screenshot payload. Subsequent
reviewed batches can change current assets. Historical `SHA256SUMS` remains the
2026-10-22 import snapshot; use the [current verification commands](VERIFICATION.md)
to check today's checkout and its documented import-file updates.

## Target homes for subsequent reviewed batches

| Path | Responsibility |
|---|---|
| `models/<organ>/source/<revision>/` | Editable scenes and recipes; reference shared inputs rather than duplicate them. |
| `models/<organ>/exports/<revision>/` | Exact exported variants, each with its own hash and scope. |
| `assemblies/<assembly>/<revision>/` | Explicit same-frame composition; never assume registration across atlases. |
| `sources/datasets/<provider>/<version>/` | One immutable home for raw public source bytes, metadata and license. |
| `reviews/<organ>/<run>/` | Immutable review record, exact-export screenshots, failures and retests. |
| `tests/` | Reusable check code, not generated screenshots or model files. |
| `gallery/` | Presentation generated from canonical metadata; not another hand-maintained model registry. |

Add real folders only with their dependency-complete content. Preserve original
packages until a reviewed path/hash mapping makes relocation safe. Historical
failures remain historical; a newer pass never rewrites earlier evidence.

## Small-batch merge rule

1. Confirm source/license and exact byte hashes.
2. Review actual exported views against appropriate references; record limitations.
3. Follow the [bounded transport flow](../transport/README.md#normal-flow) for
   manifest-only publication, authorized upload and independent hash/size readback
   **before** publishing new LFS pointers.
4. Include the model's source notices, review record, evidence and tests together.
5. Add the study's README entry only when every referenced dependency exists (see
   [study discovery](#study-discovery)).

A text-only foundation does not certify any existing asset. Published viewers and
repository synchronization are separate deliveries. No blanket clinical,
anatomical, motion or browser-runtime approval is implied.

## Study discovery

Browse [reviews](../reviews/), [models](../models/), [diagrams](../diagrams/) and
[assemblies](../assemblies/) using GitHub's directory listing or a local checkout.
These existing directories are the discovery surface; no generator or second
metadata registry is needed.

For each new batch, add or reuse a README in its own review run or export revision
(for example, `reviews/<study>/<run>/README.md` or
`models/<study>/exports/<revision>/README.md`). Give the study a readable title,
state its scoped status and limits, and link the exact artifact, review record,
evidence, source/licence notices and replay instructions. Reuse the existing
[review contract](REVIEW_CONTRACT.md) and package metadata; link to them rather
than copying records into another registry. A new revision retains prior evidence.

Independent study additions need no new row in `docs/SCOPED-STUDIES.md`, the root
README, a parent directory README or a generated aggregate. The scoped overview
retains its historical entries and 36-study migration count; new studies do not
change that bounded count. Correcting an existing claim still needs review.

Separate study/run paths let asset PRs compose independently. Shared source
changes, review contracts and transport policy still require coordinated review.

Check retained navigation and a two-branch addition with:

```sh
python3 -m unittest discover -s tests -p test_study_navigation.py
```

This checks documentation and Git composition, not media bytes or quality gates.
