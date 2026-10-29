# FDI31 staged-source check

`existing public Site → bounded download → SHA-256/header checks → CI receipt`

- Scope: #96 retained unapproved FDI31 candidate + 4 matched images, CC BY-SA 4.0.
- Identity: unchanged manifest bytes from PR109, SHA-256 `ab97d341e9490f418a06d4d9943c0ab2743f22713c174446d8d3f3c0b7ee1118`.
- Run: `python3 ci/verify_fdi31_source.py`; affected PRs run the same check.
- Cost/size: 8,723,574 download bytes → 27,593,900 raw bytes; public-repo standard Linux runner, 5-minute ceiling. No LFS, cache/artifact uploads, credentials or publication.
- Failure: stop on first source/size/hash/header error; no automatic retry.
- Evidence: job log + summary; payloads remain transient in memory.
- Not proved: repository LFS hydration, clean-checkout media availability, anatomy, clinical validity or runtime. PR109 remains separate and unmerged.
