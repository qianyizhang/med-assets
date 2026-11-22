# Teaching form at the original task scale

[Thirteen task decisions](decisions.json) · [Exact candidate assessments](campaign-assessments.json) · [TAQ-016](../../../records/work-items/items/TAQ-016-resolve-visible-form.md)

The two local teaching editions address the authored bronchial first fork and the source-preserving pelvic focus. Eleven original exports retain their teaching uses with specific limits. This pass uses the sixteen-point rubric at `9e6e490` and starts from the exact maintained editions at `c179a58`. Thyroid r02 already met the target and retains its earlier acceptance.

| Task | Result |
| --- | --- |
| First bronchial fork | The r15 fairing softens the collar and lower junction without erasing either main arm of the Y. Three neutral close views match r14 at 45 mm. The rejected narrow-support experiment had bright spots. For r15 the wider support and softened normal transition make these recede. [Comparison](plates/bronchial-comparison.webp) · [First-fork teaching plate](plates/bronchial-first-fork-teaching.webp) · [r15 export](../../../models/bronchial_tree/exports/first-fork-fairing-r15/README.md) |
| Cervix and vaginal exterior | The seven exact r02 parts used by the earlier teaching selection become the r03 focus export. The new file removes 16 unrelated context meshes and 61.2% of the download bytes. Its neutral side and opposite views are pixel-identical to the same selection from r02. [Comparison](plates/vagina_hra-comparison.webp) · [r03 export](../../../models/vagina_hra/exports/teaching-context-r03/README.md) |
| Ovaries and tubal ends | Alternate views on both sides expose the fringe and its separation from the adjacent ovary. The neutral, teaching-scale trial lowers reflection through material roughness alone with no change to any contour. The flat lower right end and angular source contours remain visible. The original HRA export receives form 2 for that visible finish, with a scoped exemption for gross localization. [Original teaching plate](plates/ovary-source-teaching.webp) · [Matched matte trial](plates/ovary-matte-trial.webp) · [Exact r01](../../../models/ovaries/exports/hra-ovary-tubal-r01/README.md) |
| Diaphragm, nasal cast and source heart | Both waves of constrained same-scope reductions were checked. The conservative previews exceeded the sampling allowance at an inferior lateral diaphragm rim, a lateral cast surface and the ventricular margin. The tighter retries removed fewer than 4% of triangles. [Diaphragm](plates/diaphragm-comparison.webp) · [Nasal cast](plates/nose_sinuses-comparison.webp) · [Heart](plates/heart-comparison.webp) |
| Native Workshop | The five-lobe reduction in a disposable evaluated snapshot lowers the scene triangle count from 286,402 to 262,878. The worst 640 × 640 alpha mask differs by 22 pixels. The evaluated geometry leaves out the native procedural configurations and controls that the Workshop delivery provides. Keep the editable scene for the original task. [Matched trial](plates/anatomy-workshop-r1-comparison.webp) |
| Other retained forms | Existing matched visibility and source comparisons show the named task remains possible while revealing the limits that prevent a score of 3. The decision for each names the feature, the permitted teaching use and evidence needed to reopen review. [Prior visual and source comparisons](../refinement-form/README.md) · [Current decisions](decisions.json) |

The r15 change is limited to the authored schematic at the first fork. OpenStax illustrates the tracheal split into the right and left main bronchi. For the ovary task, the reference describes the fimbrial shape and gross relationship. It does not register the HRA contours to a specimen section. The original review [documents the specimen source gap](../../ovaries/2026-11-21-form-assessment-r01/README.md). [Respiratory reference](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-1-organs-and-structures-of-the-respiratory-system) · [Ovarian reproductive anatomy](https://openstax.org/books/anatomy-and-physiology-2e/pages/27-2-anatomy-and-physiology-of-the-ovarian-reproductive-system)

## Replay and verify

Use exact hydrated control files, Blender 5.2.3 LTS Release Candidate `fab76e95306d` and Python 3.12. The fairing replay used NumPy 2.5.4. The plates used Pillow 13.0.0. Recover outputs into new paths from the repository root.

```sh
pack=reviews/teaching-assessments/target-form
scratch=.artifacts/taq-016-replay
mkdir "$scratch"
python3.12 models/bronchial_tree/recipes/first-fork-fairing-r15/build.py "$scratch/airway"
python3.12 models/vagina_hra/recipes/teaching-context-r03/build.py "$scratch/vagina.glb"
python3.12 "$pack/ovary-matte-trial.py" "$scratch/ovary-matte.glb"
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$pack/render.py" -- . "$scratch/matched" \
  --bronchial "$scratch/airway/bronchial-first-fork.glb" --ovary "$scratch/ovary-matte.glb" \
  --check-contacts
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$pack/economy.py" -- "$scratch/economy" "$scratch/vagina.glb"
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$pack/economy.py" -- "$scratch/conservative" "$scratch/vagina.glb" \
  --settings "$pack/economy-conservative.json"
python3.12 "$pack/plates.py" "$scratch/matched" "$scratch/economy" "$scratch/conservative" "$scratch/plates"
```

[Fairing and movement receipt](bronchial-build.json) · [Camera, geometry and local contact receipts](render.json) · [Economy bounds and matched frames](economy-trials.json)

The r15 output replays from its pinned r14. Positions and normals outside the local support, all triangle indices and the frame remain exact. The local clean reimport found no new nonadjacent face contacts. The pelvic focus packs each retained source data range unchanged. The ovary trial changes only the two ovarian roughness factors from 0.2074 to 0.58. It is recoverable from exact r01 when the material test needs review.

The finite-precision contact and sample checks cover the reported views and neighborhoods. These checks support gross teaching recognition and occurrence of visual defects. Specialist anatomy, clinical use, browser performance and hosted delivery require their own evidence.
