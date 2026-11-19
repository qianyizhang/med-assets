# Endocrine glands, head to pelvis

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Open the [portable locator](endocrine-locator.glb) or [editable Blender scene](endocrine-locator.blend). Follow the anterior outline from the hypothalamus and pituitary down to the thyroid, adrenals, pancreas and ovaries. Rotate the neck to find the four parathyroid landmarks on the back of the thyroid. The upper detached circle enlarges an islet of the pancreas. The lower circle shows paired testes as an alternative male gonad inset. The outline is an editorial aid to relative height and laterality.

The gold **TRH** arrow runs from the hypothalamic region to the pituitary region, representing release into the hypophyseal portal circulation and stimulation of anterior pituitary thyrotrophs. The teal **TSH** arrow runs from the pituitary to the thyroid, representing hormone transport by the systemic circulation. Both arrows are separate selectable meshes. The source envelope has one joined stalk and no separate anterior pituitary lobe. Its colored zones provide gross teaching landmarks for the two signals. The inset shows alpha cells in ochre, beta cells in green and a capillary in rust. The cell arrangement, counts, vessel paths and distances are illustrative. [Endotext thyroid-axis physiology](https://www.ncbi.nlm.nih.gov/books/NBK278958/) · [OpenStax endocrine pancreas](https://openstax.org/books/anatomy-and-physiology/pages/17-9-the-endocrine-pancreas).

## Admission and placements

The survey already had useful regional studies. The pituitary assembly resolves its local stalk, the thyroid study supplies posterior parathyroid context, and the HRA pancreas provides exterior regional surfaces. A head-to-pelvis orientation, signal route and visible islet require a common display. This assembly selects and translates existing regional groups, adding only the outline, inset, signals and frames. Source registrations and earlier consumers remain available. The assembly maintains the recipe, one edit-ready scene and one portable export. The [review](../../../reviews/endocrine-locator/r01/README.md) owns the paired images for the survey.

[Inputs](inputs.json) bind the six exact source GLBs. [Placements](placement.json) record translations in Blender metres, applied after baking each source node's effective world transform. The head and adrenals retain the source coordinates. The thyroid, pancreas, ovaries and inset testes are positioned as whole groups. No group was rescaled. Internal group relationships are retained. +X is subject left, +Y posterior, +Z superior in Blender. The GLB maps (x,y,z) to (x,z,−y). Source-named left adrenals, ovaries and testes are at greater X than their right counterparts. The inset is independently centered. Native atlas frames, body sizes and sexes differ. The outline and relative placement have no patient registration.

## Credits

- The hypothalamus–pituitary union and both adrenal exteriors derive from BodyParts3D, © The Database Center for Life Science, CC BY 4.0. Original historical CC BY-SA 2.1 Japan headers remain with the upstream material. [Head assembly and derivative credits](../../hypothalamus-pituitary/teaching-stalk-r01/ATTRIBUTION.md) · [adrenal provenance](../../../models/adrenals/README.md).
- The thyroid/parathyroids and testicular forms derive from Z-Anatomy, including Kousaku Okubo, Gauthier Kervyn and Marcin Zielinski, with historical BodyParts3D/DBCLS attribution. These selected assets and their derived renders retain CC BY-SA 4.0. Carry the linked source notices and license with reuse. [Neck credits](../../../models/parathyroids/exports/z-localization-r01/ATTRIBUTION.md) · [testis credits](../../../sources/datasets/z-anatomy/testicular-region/ATTRIBUTION.md).
- Pancreas and ovary forms derive from Kristen Browne and Heidi Schlehlein, HuBMAP Human Reference Atlas, CC BY 4.0. Pancreas uses the five regional elements of the HRA United Female v1.10 study. Ovary uses the two exterior elements of the ovary/tubal study. [Pancreas reference set](../../../sources/datasets/hra/united-female-v1.10/external-source.json) · [ovary source records](../../../sources/datasets/hra/ovary-tubal-context/README.md).

Changes include subset selection, world-transform baking, translations, matte materials and independent schematic annotations. Preserve these credits and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) for this mixed derivative and its renders.

## Replay

Use the repository root, Blender 5.2.3 and the hydrated input GLBs. Both output directories must be new.

```sh
blender -b -t 1 --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/endocrine-locator/r01/build.py -- --output .artifacts/endocrine-new
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/endocrine-locator/r01/check.py -- .artifacts/endocrine-new/endocrine-locator.glb .artifacts/endocrine-new/placement.json
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/endocrine-new/endocrine-locator.glb --views assemblies/endocrine-locator/r01/views.json --output .artifacts/endocrine-images-new
```
