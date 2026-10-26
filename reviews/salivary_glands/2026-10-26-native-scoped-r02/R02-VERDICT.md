# r02 final bounded acceptance

ACCEPT for source-preserved gross gland-envelope localization and gross parotid surface course only. This is not acceptance of complete salivary anatomy, full duct routing, outlets, patency, lumens, dental reconstruction, or clinical accuracy.

## Independent subset check
`r02-subset-check.json` compares r01 and r02 GLB payloads by source object: node/extras/transforms, all primitive attribute buffers and accessor descriptions, index buffers, and materials. context.glb has 15 objects; glands-ducts.glb has 8. Only Submandibular duct.l and Submandibular duct.r were removed. No objects added, no retained payload changed. Source hash and retained manifest entries unchanged; both r02 GLB hashes match manifest. Earlier independent Blender source-world verification therefore continues to apply to retained objects.

## Actual pixels reviewed
r02 annotated-context.png, review-comparison.png; failure-diagnostic/rejection-closeup.png; r02 native superior, inferior and gland-oblique renders. Annotated panel leader endpoints identify correct gland families. English/Chinese text explicitly states both submandibular ducts excluded, limited source context, no validated outlet/lumen, and original still needs revision. Opaque/translucent diagnostic visibly corroborates original left duct crossing modeled mylohyoid; it is labeled excluded and not repaired.

Both ducts may be withheld without claiming both were independently shown faulty: left crossing confirmed; right course unaccepted. No additional crossing investigation required for this bounded exclusion decision.

No remaining blocker within this narrowed scope. Keep WSU reference images outside redistributable package and retain attribution/license/provenance obligations recorded in REVIEW.md. Source-view context occlusion remains a display limitation addressed by the complementary views; do not replace those with a single opaque oblique view.
