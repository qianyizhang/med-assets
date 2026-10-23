# Asset and review layout

This is an additive foundation, not a completed migration. Existing `heart/`,
`body/`, `metadata/`, checksums and Git LFS links remain authoritative and unchanged.
No new model or screenshot payload is included in this change.

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
3. Upload missing LFS payloads through an authorized route and independently read
   them back by hash and size **before** publishing new pointers.
4. Include the model's source notices, review record, evidence and tests together.
5. Add catalog entries only when every referenced dependency exists.

A text-only foundation does not certify any existing asset. Published viewers and
repository synchronization are separate deliveries. No blanket clinical,
anatomical, motion or browser-runtime approval is implied.
