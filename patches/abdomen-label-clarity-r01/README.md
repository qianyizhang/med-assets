# Abdomen stomach label clarity only

Input: canonical commit 0b4e3dbbfd569222ba8715ac8107ab9589dd8f29, body/2d-v4/whole-body-anatomy-v4-spatial/regions/abdomen.svg.
Run python apply.py --input <EXACT_BASELINE_SVG> --output <NEW_SVG>.
Only leader path and label y change. All original organ geometry, metadata and attribution remain byte-preserved. This reduces visual ambiguity; original endpoint tested inside stomach/outside spleen, so not a proven wrong-organ error. No coverage or quality-count promotion.

Actual before/after pixels independently inspected. Reviewer personally inspected before/after and approved only this label-clarity improvement. English locator retained as-is; no retroactive bilingual rewrite.
