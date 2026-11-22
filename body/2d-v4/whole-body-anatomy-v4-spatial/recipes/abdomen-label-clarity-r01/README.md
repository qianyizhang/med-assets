# Abdomen stomach label clarity only

Input: canonical commit 0b4e3dbbfd569222ba8715ac8107ab9589dd8f29, body/2d-v4/whole-body-anatomy-v4-spatial/regions/abdomen.svg.
From this directory, run `python3 apply.py --input <EXACT_BASELINE_SVG> --output <NEW_SVG>`. The verified output matches the [current abdomen SVG](../../regions/abdomen.svg). [QA receipt](qa.json) · [Transport record](../../../../../transport/manifests/c95434900062d9c23d8ef46be1272dd2752982a3ea6aaed6b31fa0821e476dc4.json).
Only leader path and label y change. All original organ geometry, metadata and attribution remain byte-preserved. This reduces visual ambiguity; original endpoint tested inside stomach/outside spleen, so not a proven wrong-organ error. No coverage or quality-count promotion.

Actual before/after pixels independently inspected. Reviewer personally inspected before/after and approved only this label-clarity improvement. English locator retained as-is; no retroactive bilingual rewrite.
