# One Breath airway review

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

| Stage or isolated region | Isometric | Straight |
| --- | --- | --- |
| Complete route, nose to alveoli | [Whole route](route-iso.png) | [Whole route](route-ortho.png) |
| Upper airway, above V7 proximal port | [Upper region](upper-iso.png) | [Sagittal](upper-ortho.png) |
| Tracheal bifurcation to left upper lobe | [Branch](branch-iso.png) | [Branch](branch-ortho.png) |
| Enlarged terminal airways and alveolar cups, at distal tip of left branch | [Terminal](terminal-iso.png) | [Terminal](terminal-ortho.png) |

The [route export](../../../lessons/one-breath/airway-r01/README.md) supplies all eight matched Blender screenshots. [Camera and visibility receipt](renders.json). The [previous lesson storyboard](../../../lessons/one-breath/review/offline-storyboard.png) shows the original V7 main bronchial ports and separate exchange stage.

| Independent gate | Result |
| --- | --- |
| Technical | Two fresh builds yielded the same GLB bytes. A separate clean import recovered 46 meshes, intersecting surfaces at all 14 checked junctions and four wall-ray hits around the alveolar endpoint. The earlier V7-only candidate correctly failed the expanded landmark check. Its actual lumen supports the prior central route; the new peripheral routes are schematic. |
| Visual | All four clean-import pairs inspected. A sagittal view separates the nasal shelves and pharyngeal bend. The main-to-lobar bridge connects the retained left port to the Workshop branch. The front view exposes the alveolar cups. A terminal isolate avoids overlap with the lung exterior and trachea. |
| Anatomy | Reference-screened for the upper-airway sequence and conducting-to-respiratory transition. Source larynx and trachea are staged with authored passages. Finer bronchial generations are compressed and alveoli enlarged. No measured physiology or specialist review. |
| Consumer and motion | The check sampled 41,312 vertices from five loaded lung morphs at phases 0 → 0.5 → 0, with per-lobe maximum displacements of 10.70–20.03 mm and exact return to the original positions. The 27 visible extension meshes and static route held their placement at peak inspiration. The separate staged V7 shell was visible in whole/branch views. All 37 targeted Node tests passed, including expanded route continuity and focus selection at both phases. |
| Browser | A local Chrome WebGL run at 1360 × 900 paused on the inspiratory side at 42.22% of a breath. Switching stages and regions preserved that progress. The nasal, tracheal and terminal labels fit the whole viewport. The terminal view linked to the original exchange stage; CO₂ selection, Chinese reset and 390 px reflow were exercised. [Recorded UI state](browser/result.json). This run covers the tested local browser. |
| Preparation failure | A real vendor-network failure originally left a partial staging directory. Preparation now verifies every vendor input before creating its destination. An injected failure at the final dependency left the destination absent, same-path retry succeeded with all five pinned vendor files and a third run refused the existing directory. |

**Browser captures** · [Mechanics at rest](browser/mechanics-rest.png) · [Paused inspiration](browser/mechanics-inspiration.png) · [Whole airway](browser/airway-whole.png) · [Upper airway](browser/airway-upper.png) · [Bronchial junction](browser/airway-branch.png) · [Terminal focus](browser/airway-terminal.png) · [Exchange](browser/exchange.png).

[Exact artifact, source and screenshot bindings](record.json)
