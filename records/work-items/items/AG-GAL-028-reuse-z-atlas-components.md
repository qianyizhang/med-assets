---
description: Reuse source-native Z-Anatomy bone and parotid geometry across current scoped editions.
scope: Anatomy Gallery Z-Anatomy regional assets
status: stable
last_update: 2026-11-23
document_class: work_record
work_id: AG-GAL-028
work_status: done
work_kind: build
added: 2026-11-23
depends_on: AG-GAL-027
tags: gallery, assets
---

# AG-GAL-028 — Reuse Z-Anatomy atlas components

**Owner** · Z-Anatomy regional asset maintainer. Give repeated atlas geometry one selection and replay owner. Preserve each lesson’s action, native placement and source credits. Apply the [beta retention policy](../../../docs/WORKFLOW.md#retention) when replacing deliveries.

Start from the pinned [Z-Anatomy source member and license](../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json). Confirm the actual source revision used by each candidate and derive only the components supported by that evidence.

| Component | Evidence and first action |
| --- | --- |
| Right humerus, radius and ulna | The elbow and shoulder studies share the exact 2,143 evaluated humerus positions and 4,280 indexed triangles. Rotator cuff and ulnar elbow share another exact encoding of those streams. Across encoding pairs, the maximum per-axis position discrepancy is about 0.00015 mm and index order matches. The radius also matches indexed topology. Ulna position correspondence is within 0.00011 mm, with another index sequence. Start by replaying the single right humerus, then compare oriented triangles and shading at the elbow landmarks before adopting the radius or ulna. |
| Right scapula | Shoulder and rotator cuff have 12,665 corresponding positions within 0.00012 mm and differ by two triangles. Determine the affected polygons and render the glenoid and spine at each lesson’s camera. Retain the current variants if the source or normals used for those cues differ materially. |
| Parotid pair | The outer-envelope pair and the Head & Neck salivary study have 854 corresponding positions and 1,704 triangles per gland. The maximum world-coordinate component difference is approximately 0.00018 mm. The right index stream matches, while the left index stream differs. Verify the source extraction and reverse or duplicate faces before selecting a common geometry owner. Preserve the envelope-only view and make the native ducts, other glands and jaw context explicit selections. Keep the submandibular crossing excluded. |

The elbow capsule and collateral ligaments explain joint relationships. The ulnar model locates the nerve against the medial epicondyle and olecranon. Rotator cuff identifies muscle courses across each scapular face. Shared bones serve as anchors to those distinct tasks. A larger default containing all tissue would obscure the targets. Likewise the standalone parotid pair serves an exterior locator, while the full study traces a duct course and uses the jaw and other glands for orientation. A coincident envelope provides no validation of its duct attachments.

## Acceptance

- [x] Produce task-specific selections from an identified common native geometry owner. Demonstrate one disposable source edit reaching each affected export while independently checking its reference landmarks, selection, normals/materials and source frame. Track separate anatomy or rendering where it supports the lesson.
- [x] Inspect matched exact-export views in the ordinary Gallery and check exact downloads and unavailable responses. Verify the current selections and migrate their readers. Retain credits and any old delivery with a named consumer or active evidence dependency. Record decoded tolerances, bytes and any constraint that prevents replacing a current selection.

## Accepted local iteration

The starting revision was `3db3f60`. Both recipes verify the same SHA-256 for the native Z-Anatomy Blender member before evaluating named surfaces. Each publishes a complete set of lesson files from a fresh build. The [arm recipe](../../../models/joints/recipes/z-right-arm/README.md) supplies four different tissue selections. The [salivary recipe](../../../models/salivary_glands/recipes/native-region/build.py) supplies the exterior pair, the glands and ducts, and the jaw context. Sharing these components preserves the independent learner tasks.

| Lesson | Before/after decision |
| --- | --- |
| Elbow | In the anterior view, locate the capsule between the humerus, radius and ulna. In the deep oblique view, locate the annular ligament beside the radial head. The rebuilt edition preserves the landmarks and oriented triangles. |
| Shoulder | The capsule, labrum and glenoid remain legible. The new shoulder has two zero-area triangles in a 1.14 mm scapular patch. The nearest changed vertex is 52.5 mm from the labrum anchor and 71.3 mm from the spine anchor. The common source-frame triangulation trial changed shading at more corners. Keep the reviewed world-coordinate bake for this lesson. |
| Rotator cuff | The two faces of the scapula still distinguish the posterior cuff muscles from subscapularis. A clean rebuild reproduced the original GLB byte for byte. |
| Ulnar elbow | The nerve retains its course beside the medial epicondyle and olecranon. Whole, medial and posteromedial views matched at the inspected teaching scale. |
| Parotid exterior | Both lobulated gland outlines remain readable in the native frame. The left exterior now uses the same triangle diagonals as both salivary selections. The maximum sampled triangle-interior difference was 0.373 mm. Retain the gross exterior scope. |
| Head & Neck, duct course | The isolated file preserves both visible parotid ducts. Its teaching plate uses a separate jaw-context view to show the duct crossing the surface of the masseter. The dated negative evidence explains the excluded submandibular ducts. |
| Head & Neck, gland locations | Lateral and superior views place the gland pairs against the mandible and oral floor. This existing context export now has its own exact four-axis assessment and Library link. |

[Arm measurements and teaching plates](../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/README.md) · [Salivary measurements and matched views](../../../reviews/teaching-assessments/2026-11-23-salivary-shared-source/README.md) · [Scorecard](../../campaigns/teaching-asset-review/current-coverage.md)

The lead replayed the source edit through all seven exports, inspected the matched camera views, and opened the individual downloads through their ordinary Library links and the 3D Stage. A 0.1 mm humeral edit reached all four arm selections. A 1 mm right-parotid edit reached all three salivary selections. Restoring the original input reproduced the reviewed deliveries. The six new files and the byte-identical cuff all meet the teaching target. Across the Gallery, 75 of 81 selected export–task pairs meet target across all four axes; six existing form exemptions remain. The [Teaching register](../../../docs/gallery/maintained-models.md) recorded 77 IDs at this checkpoint.

## Beta cleanup

The shared extractor and package recipes replace the separate cuff, ulnar and salivary generators. The active delivery index drops the retired 186,792-byte ulnar v1 replay GLB. The seven selected downloads together fall from 2,678,244 to 2,546,512 bytes. Current r01/r02 controls still underpin matched assessments, the published Library or the negative duct review. The six new files obtain their local delivery routes from their exact assessment and the maintained register. Each multi-file lesson can select its own task and download without another hand-maintained asset manifest.

The former export READMEs, old recipe directions and October reviews pointed at superseded entry points. The package documents now identify the active builders and the role of the retained controls. The two existing package-integrity records were updated for four changed documentation files. Their model, review-image and license identities still bind the original controls. The Gallery guide and use-case documents identify the current teaching files and the two Head & Neck stops. AG-GAL-018 records the ulnar v1 input as part of its dated baseline. The root README, AGENTS.md, workflow, Library and migration guides now apply the [beta retention policy](../../../docs/WORKFLOW.md#retention).

## Verification

The tested implementation is `40e2e1f48b7ea1d96d45e7bd46f8b7a8366902cd`. The built Gallery HTML SHA-256 is `9a125062a0f976398afc08a980391a9932e397ac8520457473c5428a840d83f9`. These results cover local delivery. The published Gallery has its prior release.

- Fresh Blender replays reproduced all seven selected GLBs. Independent clean imports verified the disposable source edits. Injecting a failure partway through either build left the destination available for retry. Replaying the current arm plate sources reproduced the three bilingual teaching images byte for byte.
- Chrome checked all seven exact downloads before and after, refused incorrect file hashes, and opened each in Stage for whole-model and isolated-landmark inspection. Both Head & Neck stops selected the intended download and returned to the originating lesson. When a current image failed, the source views remained available. Reload restored the current view.
- The Library walked 97 entries, 151 revision or parent routes and 130 campaign assessments, with 101 sampled exact download responses. The full Gallery journey covered all eleven systems. The 15 packaged app tests and four preview-server tests passed. The offline gate passed 454 tests and the payload gate verified 1,129 hydrated LFS files, 25 foundation records and 13 package checks.
- The scoped change removed fourteen obsolete Python files, the superseded salivary replay README and the ulnar v1 beta input. Tracked LFS content increased by about 2 MB with the six current editions and their evidence. No new delivery manifest was added. After review, the temporary archive extraction, portable Blender copy and superseded builds were removed.
