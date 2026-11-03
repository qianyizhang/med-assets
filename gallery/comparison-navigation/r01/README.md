# Combined gallery comparison-state and keyboard navigation repair (#205 / #206)

Apply once to exact v45 review directory using `python3 apply.py REVIEW_DIR`. Four input hashes and all 3 output hashes are checked before any write. Reapply and unknown sources fail without mutation. This new combined identity replaces sequential application of the incompatible standalone recipes; standalone packages remain preserved.

- Language changes preserve comparison disclosures and layouts (#205).
- Explicit Compare focuses the visible named study heading; Back restores a unique visible origin, otherwise overview search (#206).
- Initial/deep-link load, native select, language, filters, hashes, scroll, lazy loading and source/approval records remain unchanged.
- Technical tests: actual-source Happy DOM simulation for both features, full nested Site build/checks and repository offline checks. No actual browser, assistive-technology or WebGL pass; no deployment or clinical promotion.

Run Site tests with HAPPY_DOM_MODULE pointing to the existing installed module: `node tests/comparison-state-dom.mjs`, `node tests/navigation-focus/dom.mjs`; INITIAL_HASH covers startup. No new dependencies or media downloads.
