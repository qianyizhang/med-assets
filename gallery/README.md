# External viewer integration

The [public review gallery](https://anatomy-verification.landy123007.chatgpt.site/review/)
is owned by the separate Site source. This repository contains asset inputs,
source-bound viewer work, and a small offline integration contract; it does not
contain or deploy that complete application.

On 2026-11-05, the public v49 renderer and three supporting modules matched the
retained final patch outputs exactly. Their current byte identities and source URL
are pinned in [the test fixture binding](../tests/gallery/fixtures/source.json).
The superseded v45–v48 applicators, intermediate renderers, standalone recipes,
and migration-reversal tests have been retired. Reapplying those recipes is no
longer a supported maintenance task. Change future gallery behavior in the owning
Site source, then update the current integration fixture after review.

| Scope | Current state | Reference |
|---|---|---|
| Comparison state and keyboard navigation | Incorporated; language changes retain disclosures/layout, Compare/Back restores visible focus | [#205](https://github.com/qianyizhang/med-assets/issues/205), [#206](https://github.com/qianyizhang/med-assets/issues/206) |
| Selected study URL and evidence ordering | Incorporated; valid selections replace the route, source labels keep evidence order stable across locales | [#207](https://github.com/qianyizhang/med-assets/issues/207), [#208](https://github.com/qianyizhang/med-assets/issues/208) |
| Right-elbow legend | Incorporated; exact source-bound caption corrects the historical blue capsule label; [material evidence](elbow-legend-source.json) retained | [#209](https://github.com/qianyizhang/med-assets/issues/209) |
| Supplement ownership and study-only labels | Incorporated; links use the candidate owner; entries without baselines are named explicitly | [#210](https://github.com/qianyizhang/med-assets/issues/210), [#150](https://github.com/qianyizhang/med-assets/issues/150) |

`python3 tools/verify.py offline` includes `tests/test_gallery_renderer.py`: the
exact renderer snapshot and current helper modules run against compact recorded
entries and synthetic interaction fixtures. Coverage includes bilingual labels,
URLs, evidence selection, supplement ownership, the elbow correction, focus and
comparison state. No network or media requests occur. These checks exercise
selected actual source functions; they are not a full Site build, browser,
accessibility, rendering, or clinical pass.

Candidate lifecycle/camera/context, pharynx, knee, and eye packages retain their
own source bindings and prerequisites. Incorporation of the main review renderer
does not by itself establish that those other recipes can be retired.

The snapshot intentionally retains the external renderer's then-current text.
Its proposed `models/catalog.json` and `reviews/index.json` do not exist in this
repository; [the repository workflow](../CONTRIBUTING.md) owns current local
layout and discovery. Correct that external text in the Site source when next
editing it, rather than changing the byte-bound fixture independently.
