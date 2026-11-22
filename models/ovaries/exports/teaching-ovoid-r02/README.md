# Interpreted ovary exterior with native fimbriae

[Open the teaching GLB](ovary-tubal-teaching.glb) to locate each fimbrial fringe and the gap beside its source-labeled ovary. Only the two ovarian exteriors are interpreted. The eight HRA tube components retain their original coordinates, contours and materials. [Matched teaching views](../../../../reviews/teaching-assessments/reopen-source/ovary-teaching.webp) · [original HRA edition](../hra-ovary-tubal-r01/README.md)

The NCI describes the gross ovary as ovoid and places the fimbriae beside it. Each interpreted exterior follows the principal axes and spans of its own HRA ovary. One subdivision rounds the source triangles. A gradual transition preserves the source-derived contour near the fringe. The interpretation describes gross shape for localization. It supplies no individual specimen contours, cut sections, ligaments or follicular detail. The source's L/R labels and native frame apply. [NCI gross ovary](https://training.seer.cancer.gov/anatomy/reproductive/female/ovaries.html) · [NCI salpingo-ovarian anatomy](https://training.seer.cancer.gov/ovarian/anatomy/)

After clean import, the nearest fimbrial vertices lie 2.34 mm and 2.53 mm from their corresponding ovary, within 0.07 mm of the original values. The two ovarian meshes have 1,696 and 1,640 triangles. All eight tube objects match their original world positions and triangle indices. No ovary–tube intersections or nonadjacent ovarian self-contacts were observed. The worst sampled bidirectional deviation of an ovarian exterior is 1.94 mm. [Neutral comparison](../../../../reviews/teaching-assessments/reopen-source/ovary-comparison.webp) · [measurements and frames](../../../../reviews/teaching-assessments/reopen-source/context-trials.json)

Replay with Python, NumPy and SciPy from the repository root. Choose a new output path.

```sh
python models/ovaries/recipes/teaching-ovoid-r02/build.py /tmp/ovary-tubal-teaching.glb
```

Source geometry by Kristen Browne and Heidi Schlehlein, HuBMAP Human Reference Atlas, CC BY 4.0. The changes to the two ovary exteriors are documented above. Retain the source-specific credits and license with the derivative. [Source manifest, attribution and full terms](../../../../sources/datasets/hra/ovary-tubal-context/README.md)
