# Review the dental set, not just individual teeth

**Current result:** 28 existing adult exterior representations can support a whole-mouth review. The 32-adult / 20-primary target is not complete. No condition variant or coherent teaching set has passed anatomy review.

This adds a set-level acceptance contract to the existing component specification. It does not replace the source-specific pilot limitations or approve new geometry.

## What exists now

| Coverage | Current evidence | What remains |
|---|---|---|
| Permanent exteriors | 28 BP3D source-named teeth, in one native atlas frame; 2 shared gingiva surfaces | Target slots 18, 28, 38, 48 unavailable; tooth identity, contacts and overall anatomy still need review |
| Primary exteriors | 20 named specification slots | No created, verified source-backed primary set |
| Internal layers | Prepared LMU specimens 31 and 46, each with 4 source-labelled layers | Not normal baseline replacements; preparation/cropping and inter-tissue limits; no registration to BP3D |
| UFF specimen | Unknown-FDI hard boundary and slice-enclosed space proxy | Does not fill a named slot; not a complete canal or separate enamel/dentin |
| Conditions | 7 families specified | 0 created variants; 0 baseline/condition pairs reviewed |

`set-coverage.json` lists all 52 target teeth, with separate geometry, source, specification and acceptance states. BP3D coverage was checked against the actual r02 GLB source labels, not inferred from a count of 28. Missing coverage is not a claim that a patient lacks those teeth. Earlier spec source-survey statements are historical; this dated coverage record records subsequent pilot work.

## Whole-set acceptance

Review permanent and primary dentitions separately. Neither a strong isolated tooth nor attractive lighting can pass the set.

- **Identity:** each named tooth matches its class, arch and patient side. Inspect incisors, canines, premolars and molars at comparable scale; no duplicated generic crowns or mirrored labels without source evidence. Primary morphology and developmental stage need their own evidence, not scaled adult meshes.
- **Scale and shape:** consistent units and preserved source scale; show a shared ruler. Compare crown dimensions, crown/root proportions, cusp/ridge/fossa detail and silhouette across adjacent teeth. Record measurements against the chosen reference, not invented universal tolerances.
- **Arrangement:** common arch frame, midline, tooth long axes and occlusal orientation. Preserve native placement first. Any registration or repositioning must have a recorded transform and rationale; do not transplant UFF/LMU internals into BP3D.
- **Neighbour relationships:** inspect every adjacent pair, interdental space and gingival transition. Report gaps and penetration measurements relative to mesh resolution. Upper/lower intercuspation and contact require opposing-arch review; a static closed-mouth render does not validate a bite or jaw motion.
- **Cohesive presentation:** shared neutral lighting, exposure and camera scale; consistent material conventions and detail density. Keep source limitations visible. Compare solid, translucent and section views without changing the underlying geometry or disguising incompatible sources.
- **Components:** every promised tissue remains individually selectable. Shared gingiva/bone are not duplicated per tooth. Unresolved layers remain missing; a coloured exterior shell is not enamel thickness or a pulp tissue model.
- **Condition accuracy:** paired baseline and variant use the same tooth/arch, camera and scale. Show changed anatomy and unchanged context. Any non-source-derived change is labelled reference-authored and needs a specific reference plus dentist review.
- **Approval:** record technical QA, visual consistency and professional anatomical review independently. A full-set pass needs all delivered teeth and each condition pair reviewed; representative examples alone cannot approve the remainder.

Minimum review board: whole-mouth frontal and both lateral views; upper/lower occlusal views; isolated class comparison; adjacent-contact close-ups; baseline/variant pairs. Keep missing slots visible in the coverage list, not fabricated placeholder teeth. Add a neutral silhouette option so colour cannot conceal shape errors.

## Next creation batch: a useful whole-set checkpoint

**Batch 1 — expose the existing coherent exterior assembly.** Reuse the 28 BP3D teeth and 2 gingiva objects without rescaling, repair or repositioning. Add the source-label-to-FDI crosswalk, independent selection, common material/light treatment, whole-arch views and a contact/penetration report. First review target: identity, arrangement and visual coherence, not new layers or a complete 32-tooth claim. Source licence/attribution and exact canonical bytes must stay attached.

**Batch 2 — one controlled condition pair in that assembly.** After selecting an adequately resolved and reviewed molar, reference-author one localized cavitated lesion and a separately selectable restoration, preserving the surrounding baseline and neighbours. Keep these illustrative variants separate from measured BP3D anatomy. Do not start by copying the lesion to all teeth. A reference-backed morphology review must precede calling the condition accurate.

**Batch 3 — extend only after those gates.** Add one supported periodontal segment with paired baseline support; then fill the 4 unavailable adult exterior slots and develop a separately sourced primary set. Primary source/access and developmental-stage evidence remain blockers. Do not mirror/scale adult specimens or fabricate third molars to meet the inventory count. Endodontic demonstrations wait for complete, reviewed canal evidence; the UFF proxy cannot supply it.

This ordering creates a meaningful whole-mouth review immediately while keeping the eventual full 32 / 20 set and layer/condition work visible as unfinished.

## Condition pairs must show the right differences

| First examples | Required visible evidence | Reject |
|---|---|---|
| Cavitated caries / restoration | Localized loss of tooth surface with referenced site/extent; separate restorative boundary and preserved surrounding form | A black stain presented as a cavity; guessed deep internal spread; identical lesion stamped onto every class |
| Non-cavitated early change, later | Referenced surface/material change without invented surface collapse | Requiring a hole for every early lesion; diagnosing activity from colour alone |
| Periodontal segment, later | Referenced gingival contour/recession or deposit geometry; pocket/support relationships shown only where supported | Red recolouring alone as periodontitis; unsupported bone loss or automatic disease severity |
| Crack, apical disease, impaction, later | Dedicated condition reference and matching anatomical context | Reading scan artifacts as disease; arbitrary fracture lines; generic red spheres labelled as infection |

Medical context: [NIDCR tooth decay](https://www.nidcr.nih.gov/health-info/tooth-decay) distinguishes early mineral-loss changes from cavitation; [NIDCR gum disease](https://www.nidcr.nih.gov/health-info/gum-disease) describes gingival and supporting-tissue changes. Checked 2026-10-26. These explain the visualization requirements; they do not license copied illustrations, supply patient-specific lesion geometry, or replace professional review. No procedural clinical instructions or operating parameters are supplied.
