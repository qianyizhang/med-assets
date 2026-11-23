# FDI31 staged-source check

`existing public Site → bounded download → SHA-256/header checks → CI receipt`

- Scope: #96 retained unapproved FDI31 candidate + 4 matched images. No canonical or clinical approval.
- Attribution: Benz, Leander; Heck, Katrin; Walter, Elias (2024), Data: Visualization of Pulpal Structures by SWIR in Endodontic Access Preparation. https://data.ub.uni-muenchen.de/477/ ; CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ . Derivative: protected interfaces with exterior-only simplification; original specimen frame and mm-to-m scale retained.
- Identity: the canonical content-addressed record is
  `transport/manifests/ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118.json`;
  unchanged manifest bytes from PR109, SHA-256 `ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118`.
- For a fresh remote readback, manually dispatch `fdi31-source-verification.yml` on the revision to examine, or run `python3 tests/source_checks/verify_fdi31_source.py --output /tmp/fdi31-NEW-review`. The ordinary PR gate runs the offline failure-path suite.
- Cost/size: 8,723,574 download bytes → 27,593,900 raw bytes; public-repo standard Linux runner, 5-minute ceiling. No LFS, cache/artifact uploads, credentials or publication.
- Failure: stop on first source/size/hash/header error; no automatic retry.
- Evidence: job log + summary; explicit fresh directory contains 5 verified payloads + this notice. Existing output is refused; failure removes only newly created output.
- Consumer: the shared GLB reader checks the embedded buffer and the range of each referenced buffer view; checks 4 named layers and 1,328,980 triangles. PNGs are hash/header checked, not visually reviewed.
- Not proved: repository LFS hydration, clean-checkout media availability, anatomy, clinical validity or runtime. [PR109](https://github.com/qianyizhang/med-assets/pull/109) merged on 2026-10-29.
