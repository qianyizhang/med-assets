# FDI31 staged-source check

`existing public Site → bounded download → SHA-256/header checks → CI receipt`

- Scope: #96 retained unapproved FDI31 candidate + 4 matched images. No canonical or clinical approval.
- Attribution: Benz, Leander; Heck, Katrin; Walter, Elias (2024), Data: Visualization of Pulpal Structures by SWIR in Endodontic Access Preparation. https://data.ub.uni-muenchen.de/477/ ; CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/ . Derivative: protected interfaces with exterior-only simplification; original specimen frame and mm-to-m scale retained.
- Identity: unchanged manifest bytes from PR109, SHA-256 `ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118`.
- Run: `python3 ci/verify_fdi31_source.py --output /tmp/fdi31-NEW-review`; affected PRs run the same check.
- Cost/size: 8,723,574 download bytes → 27,593,900 raw bytes; public-repo standard Linux runner, 5-minute ceiling. No LFS, cache/artifact uploads, credentials or publication.
- Failure: stop on first source/size/hash/header error; no automatic retry.
- Evidence: job log + summary; explicit fresh directory contains 5 verified payloads + this notice. Existing output is refused; failure removes only newly created output.
- Consumer: existing GLB reader parses JSON/BIN and accessor ranges; checks 4 named layers and 1,328,980 triangles. PNGs are hash/header checked, not visually reviewed.
- Not proved: repository LFS hydration, clean-checkout media availability, anatomy, clinical validity or runtime. PR109 remains separate and unmerged.
