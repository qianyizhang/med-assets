# Keyboard focus during study navigation · #206

Exact v45 guarded patch. Compare now places programmatic focus on the visible named study context; Back returns to the originating Compare action, or visible overview search when the origin is missing, filtered, hidden or duplicated. `tabindex=-1` adds no positive tab stop. Initial render/deep links, native selection and language controls do not force focus. No models, evidence, gates, storage or asset fetching changed.

## Apply to a preserved local copy
`python apply.py /exact/v45/public/review`

All4 input hashes and2 output hashes must match before writes; wrong source, existing helper and reapply are refused. No download or publication. This patch deliberately refuses private #205's different renderer; do not apply one package over the other or overwrite either branch. A separate private composition has tested both features together but is not this standalone payload.

## Evidence and limits
- Independent actual-source Happy DOM reproduction found focus left on hidden Compare/Back links. Real browsers may instead blur to body; no browser/assistive-technology pass is claimed.
- Actual renderer regression: repeated forward/back, hidden/filtered/missing/duplicate origin, initial/deep-link startup, native select, language and hash behavior, and only local data fetch. Use `HAPPY_DOM_MODULE` pointing to an already-installed package and `GALLERY_ROOT` pointing to a local applied Site copy to run `actual-gallery-dom.mjs`. Set `INITIAL_HASH='#candidate-adrenals__source-candidate-01'` for startup case.
- Independent review and full Site/repository checks are recorded separately. No new visual asset or screenshot supplied; this changes focus behavior, not rendered anatomy.
- Existing comparison/preservation and routing/security guards retained. Source records, model and image bytes, download behavior, public access and all clinical/anatomical gates unchanged. Publication/merge are separate decisions.
