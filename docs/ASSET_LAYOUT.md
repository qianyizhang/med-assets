# Asset and review layout

Each maintained asset has one source owner and one retained export per purposeful
variant. Keep source, current deliverables and review decisions easy to find;
put intermediate work under ignored `.artifacts/`.

## Canonical homes

| Path | Responsibility |
|---|---|
| `models/<organ>/source/<revision>/` | Editable scenes and organ-specific build/render recipes. Reference shared inputs and tools. |
| `models/<organ>/exports/<revision>/` | Current exports and their purpose, identity, limits and source links. Keep another revision only for a named consumer or distinct use. |
| `assemblies/<assembly>/<revision>/` | Same-frame composition and its registration assumptions. |
| `sources/datasets/<provider>/<version>/` | One home for raw public inputs, source identities, attribution and licenses. |
| `reviews/<organ>/<run>/` | Outcome README plus evidence and bindings needed by current claims. Keep decisions and unresolved defects; omit routine check dumps. |
| `tests/` | Reusable behavior checks and the smallest useful fixtures. Call owning build/verification code rather than keep another implementation. |
| `tools/` | Shared execution, format handling, integrity, transport and replay helpers. |
| `ci/` | Workflow/runtime fixtures and execution glue. Reuse shared tools for common behavior. |
| `gallery/` | Version-bound viewer patches and their replay inputs. The deployed gallery is a separate delivery. |
| `transport/` | Reviewed publication manifests and transport instructions. Policy remains in its executable owner. |
| `metadata/`, `SHA256SUMS` | Original import provenance and explicit updates to retained import files. |
| `.artifacts/<outcome>/` | Disposable renders, logs, audit output, staging and trial builds. Never an additional maintained source home. |

The existing `heart/` and `body/` bundles remain source owners until their inputs,
texture paths and consumers have a verified mapping. Some organ recipes still
live under `tools/<organ>/` or `tests/<organ>/`. Use that existing owner during
migration; do not create a second copy to fit the table. Historical `SHA256SUMS`
describes the 2026-10-22 import, not the current checkout. See
[current verification](VERIFICATION.md) and the
[retention policy](../CONTRIBUTING.md#generated-artifacts-and-retention).

## Consolidation rules

- Move source and its callers together. Check imports, CLI commands, dynamic
  discovery, package manifests, hashes, documentation and workflow paths.
- Put reusable behavior in the existing owning module. Keep organ-specific
  parameters and recipes with the asset; avoid a new framework or registry.
- Verify the retained path and important failure cases, then remove copied
  scaffolding, compatibility wrappers and spent output that no consumer needs.
- Keep failure decisions distinct from later passes. When evidence is retired,
  remove its links and narrow any claim that depended on it.

## Study discovery

Browse [reviews](../reviews/), [models](../models/), [diagrams](../diagrams/) and
[assemblies](../assemblies/) directly. A study's owning README links its current
export, source/licensing, replay instructions, review decision and necessary
evidence. Reuse existing metadata and the [review contract](REVIEW_CONTRACT.md);
do not add a second catalog, index or copied package inventory.

Independent additions need no global row in `docs/SCOPED-STUDIES.md` or the root
README. The scoped overview retains its historical 36-study migration snapshot;
new studies do not change that count. Shared source and policy changes still
need coordinated review.

Check navigation links with:

```sh
python3 -m unittest discover -s tests -p test_study_navigation.py
```

## Delivery boundaries

Before publishing new LFS pointers, follow the
[bounded transport flow](../transport/README.md#normal-flow) for source/license
checks, reviewed manifests, authorized upload and independent size/hash readback.
Include the source notices, current review decision and necessary evidence with
the delivered asset. Technical checks, visual review, anatomy/clinical approval,
browser runtime and publication remain separate gates; none follows from a file
being present or a navigation check passing.
