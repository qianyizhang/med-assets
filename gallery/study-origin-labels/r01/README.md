# Distinguish study-only entries from originals (#150)

The asset selector contains 69 entries, including seven with `hasBaseline:false`.
Calling all of them originals implies a baseline that those seven do not have.
This exact-source recipe changes only two bilingual presentation expressions:

| Original | Updated |
|---|---|
| Original assets / 原始素材 | Asset entries / 素材条目 |
| Original / 原版 on all asset rows | Study-only entry (no baseline) / 仅研究条目（无原始基线） on the seven study-only rows |

The other 62 rows retain Original / 原版. All 69 assets, 38 current studies,
107 combined entries, internal `baseline` selector value, downloads, filters,
navigation, source identities, gates, geometry and review data remain unchanged.

## Apply and verify

`python3 gallery/study-origin-labels/r01/apply.py REVIEW_DIRECTORY` requires
the exact v48 renderer and review-data hashes before the sole renderer write.
Both original expressions must be unique; the complete reviewed output hash
is checked before writing. Unknown inputs, repeat application and modified
output identities are refused. It does not fetch, build, publish or merge.

Run `python3 -m unittest discover -s tests -p test_gallery_study_origin_labels.py`
(also under `python3 -O`). Four required Python cases include three Node checks
of the actual renderer functions using compact recorded entry data and element
doubles. Original source reproduces the bad labels; updated source preserves
the seven/62 split, EN/中文, study labels, search/counts and download targets.
The unchanged reviewed `preservation.mjs` reverses only the two approved labels
and verifies the exact historical renderer hash; arbitrary edits and baseline
passthrough are rejected. Existing repository historical guards are untouched.

The retained `dom.mjs` runs the complete actual-source Happy DOM regression
against an authorized gallery checkout with an already installed dependency:
`GALLERY_ROOT=CHECKOUT HAPPY_DOM_MODULE=INSTALLED_MODULE node gallery/study-origin-labels/r01/dom.mjs`.
It fetches only its local review-data double and rejects media requests.
It is not included in the media-free repository runner. The original Site
review separately passed 35 Node tests and seven simulated-DOM scripts; those
results do not count as new repository passes.

Runtime/browser, visual layout and assistive-technology checks are user-deferred,
not passed. This text-only correction needs no image or model. No anatomical,
clinical or other review gate is promoted.

Retention: one exact baseline renderer supports replay and regression; updated
source is generated rather than duplicated. Compact fixtures contain only
the entries needed for classification and destination checks. The canonical
review data, Site source repository, media and operational receipts are excluded.
