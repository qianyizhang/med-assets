# Bounded validation receipt

Linux cloud executor, Blender 4.3.2, Python 3.12, Git LFS 3.6.1;
**2026-10-30**. Exact source and candidate identities are in the linked receipts.

| Check | Observed result |
|---|---|
| Retained archive and native member | Both exact pinned hashes matched; no source download, source script or add-on execution |
| Fresh source extraction replay | Produced exact **834,404-byte** GLB `6094265d2263f3b501f4e487ff7f859b83205bde99bca9312d48c26f29680c50` again |
| [Native source / reimport](v1/source-reimport-check.json) | All **33** vertex clouds, **38,414** surface triangles and effective matrices passed; maximum bidirectional vertex difference `1.22028140481234e-7`, below `1e-6` numerical tolerance |
| `test_package.py` | All **6 scoped tests passed**, including actual deterministic composition, exact GLB/capture reuse and negative source/output guards |
| [Displayed leader targets](v2/locator-check.json) | **6/6** exact vertex and first-visible-object checks passed; prior two occluded scaphoid failures retained |
| [Independent actual images](independent-review.md) | Final color/grayscale V2 accepted with limitations at **07:10:21 UTC** |
| `python3 tools/verify.py offline` | **205 tests**, 26 transport manifests, 25 historical foundation records, 591 import references (3 documented updates), **781 LFS pointer identities** passed |
| Changed-file whitespace | Passed for the complete scoped staged diff |

V2 changes only teaching composition and scaphoid label binding. V1 and final GLB
bytes are identical; all reused raw capture bytes, cameras, lights and scale are
unchanged. No further render was needed to correct a label target.

The ordinary offline suite does not include the six package tests, source replay,
Blender checks, image review or remote payload readback. The source comparison is
an exhaustive surface-preservation check, not anatomical correctness. The failed
soft-tissue screening and earlier layout/landmark failures remain visible in the
review directory; no result is silently promoted.

Anatomy is reference-screened only for the stated skeletal-localization question.
Clinical, live-runtime, motion, physical-scale, complete nerve territory and tunnel
claims remain unverified or excluded. Grayscale contrast is weaker than color.
Remote byte availability and draft publication are recorded separately.
