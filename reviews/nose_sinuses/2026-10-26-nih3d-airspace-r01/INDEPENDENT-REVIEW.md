# Independent review — NIH3D source-preserved airspace specimen display

2026-10-26 03:42UTC. **Accept only as a separate source-preserved specimen-display supplement.** Do not replace the failed nasal/conchae study or promote it to full anatomy approval.

## Source and actual pixels
- NIH3D3DPX-002305, uploadernevitdilmen: https://3d.nih.gov/entries/3DPX-002305
- Primarydescription states MDCT-derived upper-airwaycast including sinuses/nasalcavity/hypopharynx and a rightmaxillary retention-cyst indentation. This is source-reported pathology, not independentdiagnosis or a normalreference.
- PrimaryHTML `source-page.html` independently inspected: explicit https://creativecommons.org/licenses/by/4.0/ href and CC-BY icon. License not inferred from governmenthosting.
- Personally viewed native-axis`source-review/{minusY,plusY,plusX,oblique}.png` and independently rendered exactGLB`independent-review/fresh-export-oblique.png`.
- Complex source-derived airspace morphology is useful relative to toy primitives, but solidcast depicts airspace, **not mucosa, conchae or bone**. No inferred ostia labels, clinical dimensions, anatomicalaxisregistration or patientregistration.

## Independent geometry evidence
SourceSTLSHA`9c9d980edd1bb2d576376c0c486a3e45db65188c6ede72f3b2e1a56a1f7f9ba7`.
-98996exact-coordinatevertices,198408triangles,1component,0boundary/nonmanifoldedgecounts,0degenerate; Euler−208. Closedness is not anatomical correctness.
-4non-shared-vertex selfintersections detected by BVH candidate screen then noncoplanarsegment-triangle tests with interior hits. `source-check.json` and `candidate-intersections.json` record trianglepairs/points. Source automated13count uses different methodology and is not contradicted/replaced by4detectedpairs.
- ExportSHA`3d8c4d56e09d72ae369c697d2bb9435cc3792f9dbe225e7d456ff58174a577be` independently reimported into clean Blender scene. Inverseuniformfit gives unique98996vertexbijection and identicalorientedtriangles; maximumerror1.09569e−5 nativeunits (9.38644e−8 longestextent). Unknownnativeunits: no mmclaim.
- All4known sourceintersections persist in fresh GLB,2segment-trianglehits each. Not repaired; not print/simulation/surgicalready. Tests are finiteprecision and not exhaustive shared-vertex/coplanarselfintersectionproof.

## Reproduction
`export_verify.py --source <source.stl> --candidate <nasal_airspace.glb> --record <record.json> --out <new-directory>` via Blender `--python-exit-code 1`; hashguards and newoutputonly. Passingrun receipts in`portable-check/`.

Package must preserve publicsourceattribution/license, pathology/airspace/axis/units caveats, retainedselfintersectionwarnings and original Needsrevision status/count0. Staticrenderinspection is not browserWebGL/runtimeapproval.
