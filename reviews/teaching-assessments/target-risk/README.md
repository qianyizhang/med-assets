# Target review for nine teaching tasks

The [per-family decisions](decisions.json) bind the preceding assessment, current file, learner action and every below-target axis. The [exact-file assessments](campaign-assessments.json) cover the four focused editions and the existing thyroid companion. The [build and render receipts](measurements.json) capture source identities, replay comparisons and trial limits.

| Task | Matched evidence and disposition |
| --- | --- |
| Parathyroid localization | Use the same-source thyroid companion. The posterior view exposes both upper and lower pairs. Views from the patient's two sides confirm depth beside each lobe. Gland vertices agree exactly with the target-only component. The atlas uses mirrored markers and the thyroid projection has no assigned identity. [Posterior and sides](views/parathyroid.webp) |
| Eye anterior order | Use the three-structure derivative. The front oblique exposes the aperture and lens. The superior close-up confirms the retained angular rim and exact material roles. The separate source profile gives the depth order. [Comparison](views/eye.webp) · [Profile and controls](../refinement-risk/views/eye-anterior-order.jpg) |
| Cardiac wall motion | The focus edition keeps the LV wall and aorta plus the exact authored wall track. Both phase poses match the selected meshes in the full atlas. All 20 integer-frame evaluations agree, with 5.047 mm maximum sampled wall motion and a fixed aorta. The full atlas supplies orientation. [Matched phase sample](views/heart.webp) |
| Breathing dome descent | The editable focus edition keeps the five lobes, dome and liver. All retained world vertices match at all 121 integer frames. At frame 49 the dome crest is 20.90 mm lower, the left lower-lobe base is 17.60 mm lower and the lowest liver point is 7.98 mm lower than at frame 1. [Phase comparison](views/breath.webp) |
| Bladder base and entries | The focused file retains six bladder patches and two ureters exactly in the female atlas frame. Both small orifices received separate world-vertex comparison. The rear focus reveals both and the opposite view exposes the source base ridge. [Pelvic and focus views](views/bladder.webp) |
| Gallbladder exterior and section | Keep the exact file. The neutral broad highlight and two views show the source bulb and narrowing independently of the section. The isolated section exposes the authored cut rim and separate duct cue. The all-parts panel is a diagnostic view of the apparent seams. [Form review](views/gallbladder.webp) |
| Stomach exterior and rugae | Keep the exact file and established exclusive modes. The source profile and authored backing are separate. Six fold reductions kept sampled deviations under 0.8 px, saving 1,708 triangles and 37,216 bytes. Higher reductions on folds 3, 8 and 10 exceeded 1 px. The trial retains the texture cost and 58,748 triangles. [Neutral and oblique checks](views/stomach.webp) · [Matched mesh trial](views/stomach-trial.webp) |
| Lymph-node tissues | Keep the tissue-only edition. The capsule and three regions are visible with the original apertures and rough medullary relief. An initial simplification could not represent 37 coincident face pairs. Protecting their neighborhoods let the trial run. The 40,678, 55,698 and 65,416-triangle medullas exceeded the 0.8 px budget. The shorter trial removed under 4% at its smallest tested step. [Capsule and neutral medulla](views/lymph.webp) |
| UFF extraction failure | Keep the material evidence in the exact export and source overlays. Slices 966, 969 and 972 show the terminal selection changing from 140 to 128 to zero voxels as the channel opens. A cap edit would obscure the method failure the exercise asks the learner to find. [Terminal comparison](../refinement-risk/views/uff-proxy-terminal-evidence.jpg) |

The matched plates use a standard neutral studio light or declared illustrative object colors. The digestive all-visible views are diagnostic. The established Gallery presets already use exclusive selections. The UFF comparison retains its existing scan and mesh witnesses. The receipts cover local asset measurements. Browser playback, deployment, clinical anatomy and flow have separate scopes.

## Replay

Run from the repository root with Blender 5.2.3 build fab76e95306d, Python 3.12, and Pillow. Use fresh scratch directories. The native Blender identity is the reviewed saved file. Replays compare exact retained geometry and frame measurements because Blender save metadata can vary.

```sh
review=reviews/teaching-assessments/target-risk
scratch=.artifacts/taq-017-replay
mkdir "$scratch"
python3.12 "$review/select_glb.py" heart "$scratch/heart"
python3.12 "$review/select_glb.py" bladder "$scratch/bladder"
eye=models/eye_anterior_segment/recipes/teaching
baseline=models/eye_anterior_segment/exports/hra-v1.3-r01/anterior_segment.glb
candidate=models/eye_anterior_segment/exports/eye-order-r01/eye-order-study.glb
python3.12 "$eye/build.py" --source "$baseline" --output "$scratch/eye"
cmp "$candidate" "$scratch/eye/eye-order-study.glb"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$eye/review_blender.py" -- --baseline "$baseline" --candidate "$candidate" --output "$scratch/eye-qa"
for family in heart breath bladder stomach gallbladder; do
  blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
    --python "$review/review_blender.py" -- "$family" "$scratch/$family-qa"
done
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$review/review_blender.py" -- parathyroid "$scratch/parathyroid-verified"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$review/review_blender.py" -- lymph "$scratch/lymph-bounded"
blender --background --factory-startup --disable-autoexec --threads 3 --python-exit-code 1 \
  --python "$review/review_blender.py" -- lymph "$scratch/lymph-fine" --fine
python3.12 "$review/plates.py" "$scratch" "$scratch/views"
```

The two GLB selections are exact repacks with embedded resources. Their readback checks compare every retained buffer view, and their fresh imports compare transforms and evaluated positions. Use the retained provenance and licenses with each export. The parathyroid companion keeps its independently reviewed original identity.

The [shared female HRA pelvis assembly](../../../assemblies/hra-female-pelvis/README.md) owns the bladder selection and the active rebuild for both pelvic outputs. This review retains its original task measurements and figure bindings. The bladder commands above use the assembly's selection to reproduce the reviewed bladder export.
