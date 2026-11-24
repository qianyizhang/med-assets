# Renal and splenic acquired references

The [reference manifest](renal-splenic.json) pins the six display images and carries their attribution. Each is an acquired comparison from a separate case relative to s1233. The cited captions establish the planes and renal laterality. Visual inspection confirmed the elongated and rounded renal sections and the longitudinal and transverse splenic views. The transverse spleen source is a tight view around the hilum with limited surrounding anatomy. The source does not establish that its two spleen panels came from the same participant.

The kidney panels are from [Yadav et al., Diagnostics, 2025, Figures 4–6](https://www.mdpi.com/2075-4418/15/24/3208). The spleen figures are from [Demissie et al., BMC Medical Imaging, 2021, Figures 1–2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8642847/). Both sources use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Their selected figure captions carry no separate credit exceptions. The cropped renal panels retain the source calipers, probe orientation icons and scale. The spleen images retain the published markings. No patient identifiers are visible in the retained images.

For replay, verify each download hash, convert to RGB, apply the crop as left, top, right, bottom edges with Pillow, fit within 960 × 680 pixels using Lanczos without enlarging, then encode WebP at quality 94. Save without source metadata. Compare output hashes against the manifest.

| Output | Original image | Original SHA-256 | Crop |
| --- | --- | --- | --- |
| `kidney-right-12.webp` | [Figure 4b](https://mdpi-res.com/diagnostics/diagnostics-15-03208/article_deploy/html/images/diagnostics-15-03208-g004b.png) | `46a9263936d441b27a2855f2dd0903442293136cdcfd76caf765f63f77242625` | `23, 31, 2368, 1352` |
| `kidney-right-48.webp` | [Figure 5b](https://mdpi-res.com/diagnostics/diagnostics-15-03208/article_deploy/html/images/diagnostics-15-03208-g005.png) | `a2848432e65b3d541e341c75e3d6b28db5177d1f8007a01ea436713d8fa5d5b9` | `27, 2014, 2285, 3284` |
| `kidney-left-12.webp` | [Figure 6b](https://mdpi-res.com/diagnostics/diagnostics-15-03208/article_deploy/html/images/diagnostics-15-03208-g006a.png) | `37a64850bd22b38d917c0d20941d25030c5a266f93eebe9511e5215c79000caa` | `24, 2060, 2295, 3337` |
| `kidney-left-48.webp` | [Figure 6d](https://mdpi-res.com/diagnostics/diagnostics-15-03208/article_deploy/html/images/diagnostics-15-03208-g006b.png) | `175d849a95f2b29dcdbe9c6e88cd87c7689220f2456c5c359beb06830e151bbe` | `24, 2040, 2293, 3316` |
| `spleen-12.webp` | [Figure 1](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e472/8642847/e61196479865/12880_2021_719_Fig1_HTML.jpg) | `01f8956e20067863fed1341c087c677b906f91f6621f30277bde7c9ed97bbd72` | Full published figure |
| `spleen-48.webp` | [Figure 2](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/e472/8642847/cd48538f7690/12880_2021_719_Fig2_HTML.jpg) | `f196276b8ffdcc092c36033eabf89e9b29b4ad4e6c67bf3c20b23621865bd83a` | Full published figure |
