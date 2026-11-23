---
description: Give the right elbow and shoulder question-first practice with fixed source landmarks and labeled answer views.
scope: Anatomy Gallery Use Cases and right-arm assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-029
work_status: done
work_kind: build
added: 2026-11-23
depends_on: AG-GAL-028
tags: gallery, lessons
---

# AG-GAL-029 — Right-arm part lessons

**Owner** · Gallery teaching maintainer. Make the two relationships in the [shared right-arm replay](AG-GAL-028-reuse-z-atlas-components.md) available as linked practice stops in Use Cases. The learner can locate a relationship on an unlabeled reference image, switch the tissue layer in the same framing, then reveal a labeled answer. Interactive inspection uses the same native metre coordinates and named subsets as the reference images.

| Stop | Fixed evidence and learner action |
| --- | --- |
| Right elbow | Switch from the joint capsule to the ulnar nerve while retaining the humerus, radius and ulna at the same scale and in the same posteromedial view. Compare the medial epicondyle and olecranon, then identify the nerve beside both. The capsule is partly occluded from that side. The named bone silhouettes stay in place and the two source displays retain their different shading. |
| Right shoulder | Find the glenoid socket and its labral rim, then switch to the cuff muscles while retaining the scapula. The posterolateral view exposes both the glenoid and scapular spine. The separate posterior and anterior answer panels locate supraspinatus above the spine, infraspinatus and teres minor below it, and subscapularis on the anterior face. Both layers hide the humerus to expose the landmarks. |

The [Gallery lesson configuration](../../../lessons/right-arm-parts/arm-lesson-layers.json) pins the four exact assessed GLBs and their node selections. Downloads retain their original task and evidence. Delivery adds two stops to the existing Use Cases and six WebPs totaling 117,752 bytes. The [arm replay review](../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/README.md), [cuff review](../../../reviews/joints/2026-10-30-rotator-cuff-r01/README.md) and [ulnar review](../../../reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/README.md) bind the earlier exact evidence. [Body-donor elbow study](https://link.springer.com/article/10.1007/s00276-024-03327-8) · [OpenStax shoulder orientation](https://openstax.org/books/anatomy-and-physiology-2e/pages/11-5-muscles-of-the-pectoral-girdle-and-upper-limbs)

The static atlas surfaces illustrate gross anatomical relationships. The nerve edition omits much of the soft-tissue tunnel. Cuff surface extents do not establish tendon continuity, attachments or motion. Colors distinguish surfaces. [Z-Anatomy and historical BodyParts3D attribution](../../../sources/datasets/z-anatomy/joint-regional-studies/upstream/ATTRIBUTION.md) applies to the source geometry and to the lesson render derivatives.

## Media replay

Two fresh render sets from the final cameras encoded all six files byte for byte. The [lesson's replay](../../../lessons/right-arm-parts/README.md#rebuild-and-compare) gives the current commands, environment and dimensions.

The campaign lead checked both stops before and after in the ordinary Gallery. Each reference layer and labelled answer decoded, and the live camera returned to the same rotated frame after switching tissues. Missing and same-size corrupt GLBs preserved the reference exercise and supported retry. The six-task browser check also exercised the stills without WebGL. [Shared acceptance check](../../../sites/anatomy-gallery/tools/verification/layer-lessons.mjs)

## Integrated batch acceptance

The lead accepted the right arm, [Head & Neck](AG-GAL-030-salivary-part-lessons.md) and [female pelvis](AG-GAL-031-pelvic-part-lessons.md) at implementation `1d64f071c5d484fff35d2a7f2d20f009a384351d`. The built local Gallery HTML has SHA-256 `95d806dec51ff7f65963ea64c9ead3e65a9ad6dbaf178f66888848151a8fc29b`.

Chrome entered each task through Use Cases or Body Systems and checked both tissue layers, landmark marking, fixed-camera and rotated-camera round trips, immediate answer reveal, reset and retry. Each task worked in a local public-origin rehearsal with WebGL disabled. The wider Gallery checks passed for all eleven Body Systems stops, the 21 other registered use-case checks and the existing 3D Stage presets. The use-case verifier now reports the size of its actual checklist. The previous hard-coded total was stale.

The existing collections and assessed models supply all six tasks. The batch adds 18 compact WebPs totalling 307,372 bytes and their reproducible source recipes. The asset scorecard remains at 77 maintained families and 81 selected teaching files. The repository passed 455 offline tests and verified 1,147 hydrated LFS payloads, 25 foundation records and 13 package checks. The 15 packaged Gallery tests and four preview-server tests passed. The updated route guide, Gallery use-case guide, build guide and work queue describe the new entry links, practice and local replay. These are local acceptance results.
