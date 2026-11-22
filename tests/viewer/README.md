# External viewer integration

- **Published owner** · [Review gallery](https://anatomy-verification.landy123007.chatgpt.site/review/), maintained in the separate Site source.
- **Relationship to Model Survey and Body Systems** · [Gallery design and handoff](../../docs/gallery/design.md).
- **Local goal** · Test incorporated viewer behavior against pinned source without a Site build or network requests.
- **Update scope** · Change the owning Site source. After review, refresh the bound fixture from that source. Historical applicators for incorporated features are retired.

| Coverage | Source and checks |
| --- | --- |
| Gallery renderer | [Fixture binding](../gallery/fixtures/source.json) and [offline tests](../test_gallery_renderer.py). Bilingual labels and directory guidance, selection URLs/evidence order, supplement ownership, focus and comparison state. |
| Right-elbow legend | [Exact material evidence](../gallery/fixtures/elbow-legend-source.json) and [correction](https://github.com/qianyizhang/med-assets/issues/209). |
| Candidate camera, lifecycle and context recovery, knee and eye | Incorporated byte-for-byte in v50. [Candidate source binding](source.json) and [test runner](run.py) own exact identities and private staging. Camera CPU uses that same source. |
| Pharynx visibility | [Unapplied recipe](../pharynx_visibility/visibility-r01/README.md), absent from v50. |
| Live behavior | Browser/rendering, BFCache, accessibility and clinical status need separate evidence. [Repository gates](../../docs/WORKFLOW.md#runtime-and-delivery-boundaries). |

- **Decision references** · [Comparison state](https://github.com/qianyizhang/med-assets/issues/205), [focus](https://github.com/qianyizhang/med-assets/issues/206), [selection URLs](https://github.com/qianyizhang/med-assets/issues/207), [evidence order](https://github.com/qianyizhang/med-assets/issues/208), [supplements](https://github.com/qianyizhang/med-assets/issues/210), [study-only labels](https://github.com/qianyizhang/med-assets/issues/150).
