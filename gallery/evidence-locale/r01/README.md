# Stable medical evidence across language changes (#208)

Blood-form study previously selected its 3-view contact sheet in English but only intact/cutaway cells in Chinese. The source-label ranking accidentally depended on translated captions. Primary evidence ranking now uses the English source label, Chinese fallback, then empty label; contact → front → first order is retained. All 37 studies retain existing English ordering; language changes only captions, not selected evidence identity.

## Choose one exact guarded delivery
- Frozen #207 Site 3e37658e18bb12a630dc12691eb90fe0d589bcec: python3 apply.py REVIEW_DIR --mode 207. Only review.js changes.
- Fresh v45 c671a87e28332763d1d1d8df07b6291fd21de45d: python3 apply.py REVIEW_DIR --mode v45. Composes #205/#206/#207/#208 with all input/payload/intermediate/final hashes preflighted before any writes.
- Existing comparison-navigation/r01 payloads are referenced, not duplicated. Neither recipe is sequentially applied to another package. Repeats and unknown/tampered source/output fail without mutation.
- Prior frozen Site/repo heads and packages remain unchanged.

Image bytes, evidence metadata/roles, translated captions, lazy loading, disclosure/layout, study selection URLs and Compare/Back focus are unchanged. No asset or anatomical claim changes.

## Tests and limits
dom.mjs tests actual renderer over all 37 studies: primary/rest IDs/files and captions through EN→中文→EN. LABEL_FIXTURE=no-en and LABEL_FIXTURE=empty cover source-label fallback; normal English ordering matches the existing ranking. GALLERY_ROOT and HAPPY_DOM_MODULE point to local source and existing HappyDOM; fetch is stubbed to local review-data.json. Prior #205/#206/#207 DOM regressions are retained. Strict preservation checks assert the new renderer hash and reverse only this exact ranking delta to #207 before prior guard checks.

Evidence is offline DOM simulation, not browser/WebGL/assistive-technology QA. No new media requests, Blob operations, dependencies, publication or clinical promotion.
