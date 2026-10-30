# Source-defined opaque heart exterior

These separate derivatives restore the native model's opaque-exterior visibility rule. They keep 124 exterior mesh nodes and exclude the 123 source endocardium/valve/support nodes from the displayed scene. The static derivative also excludes its 142 source-tagged cutaway duplicates. Originals, cutaways and native sources remain unchanged.

This is a presentation correction for the shared seam concern in #150. It is not a correction of the RV inlet, valve, papillary or chordal geometry. The visible gaps, separate vessel joins and schematic surface remain. Do not teach complete anatomical containment, lumen continuity or physiology from these derivatives.

## Source evidence

`heart/Cardiac_Atlas/build_heart.py:509–514` hides collections 02 and 03 when `cut < .5 and mode < 1.5`. Independent inspection of both native `.blend` sources confirmed all 123 nodes are hidden in tissue and clinical opaque exterior states, and available in cutaway/transparent states. The static and animated portable export recipes remove visibility drivers and select these internal collections for their full exports. That export-to-native difference explains the unwanted cord/leaflet presentation.

`visibility-spec.json` records the exact native member names and native source hashes. The builder accepts only the two exact existing repository exports. The canonical fitted animated asset `17b26d1459c0fbbbc71d051452c4074d1237683ffe02c1a8021d7ac83583857a` is a different, 8,180,452-byte artifact and was not available here. The animated derivative below is explicitly from the repository's original authored source, not a replacement certified for that fitted canonical artifact. All 912 retained canonical morph samples agree with the repository source; [identity, provenance and the remaining exact-byte gap](../../reviews/heart_exterior/2026-10-30-native-visibility-r01/provenance-and-applicability.md) explain the limited claim.

| Derivative | Source SHA256 | Result SHA256 |
|---|---|---|
| `exports/static-opaque-exterior.glb` | `83dd48731d0cc67e8aa61abbd7b03163fb01bcba78f501e9d2c939927aaecf6e` | `595380d0aff153db4494fc5f9e8ffba062d0732c2bf0886242ebe1a188d3806f` |
| `exports/animated-source-opaque-exterior.glb` | `6912d439271c3525230a90fe403d586000e6a66ab37f82bf0419604181e52263` | `aec9c13d3b9a0fa919bdc362ed17c582f895f77fc44f5e29cd184cea57599e0f` |

The operation filters node participation, remaps scene/child indices and removes animation channels for excluded nodes. All retained node transforms, mesh/material/accessor definitions and the entire original BIN chunk remain byte-identical. Unused original payload data remains in the file; this is not a size or runtime optimization. The animated derivative retains 109 exterior channels, all 25 authored samples and the original 0.8-second loop.

## Reproduce and check

Use Python 3.11+ and actual hydrated source GLBs and native `.blend` files (the package checker verifies their provenance). From the repository root:

```sh
python3 heart/exterior-presentation-r01/build.py --repo . --kind static --output /tmp/heart-static-new
python3 heart/exterior-presentation-r01/build.py --repo . --kind animated-source --output /tmp/heart-animated-new
python3 tests/heart_exterior/verify_pair.py --source body/anatomy-workshop-r1/meshes/heart_detailed.glb --candidate /tmp/heart-static-new/static-opaque-exterior.glb --spec heart/exterior-presentation-r01/visibility-spec.json --output /tmp/heart-static-check-new.json
python3 tests/heart_exterior/verify_pair.py --source heart/Cardiac_Atlas_Animated/Heart_Clinical_Animated.glb --candidate /tmp/heart-animated-new/animated-source-opaque-exterior.glb --spec heart/exterior-presentation-r01/visibility-spec.json --output /tmp/heart-animated-check-new.json
python3 tests/heart_exterior/verify_package.py --source-repo .
python3 tools/verify.py offline
```

All builder outputs and verification receipt paths must be new. `regression.py` takes a directory containing `static/` and `animated-source/` outputs and checks deterministic replay, no overwrite, source identity and candidate corruption rejection. It is a scoped actual-media check, not part of ordinary offline CI.

Blender 4.3.2 is required for `tests/heart_exterior/reimport_motion.py` and `render.py`. The former compares all 124 retained objects after clean import at every authored sample; use `--animated` for the 25-frame clip. The latter takes a source/candidate GLB, a new output directory and `--match` with a retained original binding record. Logical `view` names preserve cameras after evidence file relocation. Render whole/front detail/neutral as needed; label outputs `Original` or `Updated`. Source static state hides explicit cutaway duplicates. These are offline renders, not browser screenshots.

[Actual images, independent review and receipts](../../reviews/heart_exterior/2026-10-30-native-visibility-r01/README.md) document scope and remaining gates.

## Attribution and limits

Project-authored analytic Cardiac Atlas, not patient-derived anatomy. Source recipes, package manifests and the owner's prior distribution identify authored geometry; no unresolved third-party geometry provenance was found. The package declares no separate public reuse license, and this derivative grants none. That absence is distinct from authorization to deliver the owner's project work. Preserve the native/source documentation and original identities.

Independent source/pixel review supports only the restored opaque-exterior presentation. Internal spatial relationships remain unresolved; a coherent RV inlet/apparatus redesign is a separate design choice, not a mesh weld determined by the current source. Clinical/anatomy approval, live viewer runtime and canonical fitted-animation integration remain unverified. Authorized draft publication does not promote those gates. #150 is not closed by this package.
