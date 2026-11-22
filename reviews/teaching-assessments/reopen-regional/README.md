# Three interpreted regional teaching editions

Use the adrenal pair to orient the glands on their own atlas kidneys, the pancreatic exterior to trace head to tail, and the collecting-route diagram to locate both limits of the depicted line. The [decisions](decisions.json) bind each edition and its original learner task to the matched views. The source files remain available for detailed surface or component inspection.

| Edition | Change, comparison and limit |
| --- | --- |
| [BP3D adrenal profiles](../../../models/adrenals/exports/atlas-locator-r02/README.md) | Fairing reduces the rough reverse relief. Each gland retains its own XYZ extrema; maximum vertex movements are 1.18 mm and 1.36 mm. The first trial anchored isolated extreme vertices and produced pointed corners. Refitting each smoothed gland to its original extent gives a continuous contour in the [selected reverse views](views/adrenals-after.webp). Both original atlas kidneys are included in source coordinates. Their reference positions establish the gross relationship. The fairing represents teaching form and supplies no evidence of fine specimen morphology. |
| [HRA pancreatic locator](../../../models/pancreas/exports/gross-locator-r05/README.md) | Relaxing the original regions separately exposed seams in the enlarged head. A coarse voxel surface showed ripples. The accepted envelope joins the five gross source regions, remeshes at 1.25 mm, smooths a control cage and reduces the subdivided exterior to 11,088 triangles. One closed connected envelope remains. The eleven duodenal and splenic context meshes retain their unique positions and triangle counts. The [matched head and reverse views](views/pancreas-after.webp) support gross localization. The approximately 2.7 mm worst sampled difference from the source head bounds this interpretation. r04 retains the boundaries, ampulla and ducts. |
| [Collecting-route diagram](../../../models/lymph-collecting-routes/source-trace-r02/README.md) | Seven interpolated curves run through the original ring centers. Two colored markers identify the central trace’s actual sampled endpoints. The imported marker centers differ from the source by less than 0.0001 mm. The [enlarged straight and oblique views](views/lymph-after.webp) separate the trace from its six muted guides. Intermediate curvature, stroke size and endpoint symbols are graphical choices. The upper end establishes no venous contact. |

The primary anatomical references describe the adrenal relationship to the kidneys, the region between duodenum and spleen, and the wider lymphatic return. The exact exported models and source positions establish the relationships represented here. [OpenStax adrenal glands](https://openstax.org/books/anatomy-and-physiology-2e/pages/17-6-the-adrenal-glands) · [Digestive accessory organs](https://openstax.org/books/anatomy-and-physiology-2e/pages/23-6-accessory-organs-in-digestion-the-liver-pancreas-and-gallbladder) · [Lymphatic anatomy](https://openstax.org/books/anatomy-and-physiology-2e/pages/21-1-anatomy-of-the-lymphatic-and-immune-systems)

## Replay

Use Blender 5.2.3 build `fab76e95306d`, the exact hydrated starting files and the [pinned BP3D archive](../../../sources/datasets/bp3d-4.0-glands/external-source-members.json). The adrenal recipe checks the archive and the two kidney members before import. Run from the repository root. Set `bp3d` to the existing archive and choose a fresh output directory.

```sh
out=.artifacts/regional-replay
recipe=reviews/teaching-assessments/reopen-regional
blender -b --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 --python "$recipe/trials.py" -- "$out" lymph adrenals pancreas --bp3d "$bp3d"
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python "$recipe/check.py" -- "$out"
python "$recipe/plates.py" "$out" "$out/plates"
```

The plates use Pillow 11.3.0 and the macOS Helvetica font. Compare the resulting GLB SHA-256 values and clean imports to the [measurements](measurements.json) and [independent checks](clean-import-check.json). The measurements include source-to-envelope and envelope-to-source distances sampled at vertices. They do not estimate surface error between all samples. The matched cameras preserve scale within each pair. The enlarged details use separate framing.

The adrenal derivative credits BodyParts3D, © Database Center for Life Science, under CC BY 4.0 with historical OBJ notices retained upstream. The pancreatic derivative credits Kristen Browne and Heidi Schlehlein, HRA Female v1.10, under CC BY 4.0. The commissioned lymph source carries the permissions of its original package. This local review grants no additional distribution rights.
