# Bilingual evidence-reading state (#205)

A guarded patch for the canonical v45 medical review gallery. EN/中文 switching
previously discarded expanded source bindings and full-width comparisons.
This patch keeps each reader's current disclosure and comparison layout during
the language change; it adds no persistent storage and changes no assets or gates.

- Source context + evidence identity + occurrence distinguish repeated evidence.
- Open **and closed** states survive; siblings stay independent.
- Selected study, filters and the existing scroll restoration stay unchanged.
- Candidate root visibility remains owned by the study selector.
- Model/image payloads, attribution, evidence records and lazy-media code unchanged.

## Apply and verify

`python gallery/comparison-state/r01/apply.py /path/to/fresh-v45/public/review`

The exact input and output SHA256 values are in `binding.json`. All hashes and the
absence of the new module are checked before writing. Unknown source revisions,
modified dependencies, repeat application and modified packaged outputs fail closed.
No network access or dependency installation occurs.

With an existing Happy DOM installation and the patched Site checkout:

```
SITE_SOURCE_ROOT=/path/to/site HAPPY_DOM_MODULE=/absolute/path/to/happy-dom/lib/index.js \
  node gallery/comparison-state/r01/actual-gallery-dom.mjs
```

This imports the actual gallery renderer with local recorded data and no remote
model/image requests. It tests both language directions, 422 existing disclosures,
103 comparisons, duplicate contexts, same-context repeated evidence, new/removed
items, open/closed states, selection, filters, scroll, and storage absence.
These are simulated DOM tests, **not a rendered-browser or WebGL pass**. The isolated
browser fixture could not be served in the available browser environment; its data
URL was denied by browser protocol policy, and that route was stopped.

Independent source review found no blocker. The existing Site test suite and
production build also passed. Publication and deployment remain separate actions.
