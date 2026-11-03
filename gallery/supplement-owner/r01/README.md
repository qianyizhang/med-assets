# Supplement viewer owner routing (#210)

Original blood, diaphragm and tongue entries correctly group logical supplements, but their viewer links use the original asset owner and fail the unchanged strict selection contract. This recipe changes only the unique archive link expression to the candidate's own assetId. It does not loosen selection validation or alter records/gates/media.

Run `python3 apply.py REVIEW_DIRECTORY` against exact deployed v46 review source. All 3 input hashes and the complete output hash are checked before the sole review.js write. Repeated application, wrong/ambiguous input and output mismatch reject. Does not install sibling #205–209 changes: those are required inputs.

Tests: `python -m unittest tests/test_gallery_supplement_owner.py` (also under `python -O`). Actual-source DOM test requires GALLERY_ROOT pointing to the Site checkout and HAPPY_DOM_MODULE pointing to an already installed happy-dom module; no download is required. It verifies 40 archive links in EN/中文/EN, exact source/gates, 3 supplement associations and strict wrong-owner rejection; it is not browser/WebGL or clinical validation.

For Site delivery, retained incremental Site bundle additionally includes the regression and exact historical migration-preservation adapter. The recipe alone changes production source only. No publication or merge authorization is conveyed.
