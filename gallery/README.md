# External viewer integration

The [public review gallery](https://anatomy-verification.landy123007.chatgpt.site/review/)
is owned by the separate Site source. This repository contains asset inputs,
source-bound viewer work, and a small offline integration contract; it does not
contain or deploy that complete application.

The current renderer snapshot and three supporting modules are retained for
offline integration checks. Their byte identities, public Site version and check
date are pinned in [the test fixture binding](../tests/gallery/fixtures/source.json).
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
comparison state, plus bilingual directory ownership and snapshot guidance.
No network or media requests occur. These checks exercise
selected actual source functions; they are not a full Site build, browser,
accessibility, rendering, or clinical pass.

Read-only comparison with the same v50 Site source confirms that candidate camera,
lifecycle, context recovery, knee and eye helpers are incorporated byte-for-byte.
The camera, lifecycle/context and knee/eye applicators are retired. Current-source
behavior tests use one bound candidate and per-run private staging through
`tests/viewer/run.py`; `tests/viewer/source.json` owns exact source identities.
The camera CPU suite uses that same candidate. Pharynx modules
are absent from v50 and retain their separate unapplied recipe. See each package
for exact bindings and independent runtime limits.

The refreshed renderer describes asset-owned recipes and directory-based discovery,
without proposing nonexistent global registries. The [repository workflow](../docs/WORKFLOW.md)
owns local layout and discovery; the Site remains separately maintained. Historical
baseline metadata is labelled as a snapshot rather than a repository-wide pending
sync. This guidance update does not replace model/evidence bytes or change review
gates. Refresh the byte-bound fixture from the owning Site source, never independently.
