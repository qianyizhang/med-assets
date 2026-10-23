# Blood-cell form study — AUTHORED, not microscopy or patient data

This separately named teaching candidate replaces no canonical file. `draft_blood.glb` remains unchanged at SHA-256 `8efaa236d4f4102ce755e7c5a6252347c2212caba32c9b8ddf8cc6e5e7b9433c`.

## What the study depicts

- Two orientations of a closed, biconcave erythrocyte. No hole and no nucleus.
- One simplified intact neutrophil, and a second display of **the same authored cell** with front cytoplasm removed to expose its internal segmented nucleus. The nucleus is one connected volume with three differently elongated, smoothly bent lobes, entirely within the original cell boundary. The cutaway is not a physiological opening or a section through the nucleus.
- Three small, oblate platelet illustrations. No activation sequence or clot formation is claimed.
- Text meshes are display annotations, not cellular structures.

The display arrangement is not a blood smear, cell count, population proportion, concentration, density, motion or in-vivo arrangement. No membrane ultrastructure, organelle completeness, nuclear chromatin texture or measured granule density is depicted. An opaque sphere is a simplified outer-cell boundary, not a verified intact-cell surface reconstruction. The cut plane is a graphic device; it must not be described as a cell wall (human cells have no cell wall).

## Authored geometry and scale

Arbitrary display units only: RBC diameter 2.0, neutrophil diameter 2.9, platelet diameter 0.68. These provide illustrative relative sizes, not biological measurements or individual specimen estimates. The image references were not segmented, traced, fitted or reconstructed into these meshes.

RBC generating surface: `r = sin(a)`, `z = cos(a) * (0.15 + 0.62*r^2 - 0.28*r^4)`, `x = r*cos(theta)`, `y = r*sin(theta)`, for `a in [0, pi]`, `theta in [0, 2*pi)`. Upper/lower centers are closed with unique vertices. The coefficients are authored choices, not an attributed fit or named biophysical model. The exported central profile records the actual coordinates separately.

Nuclear lobes: three unequal ellipsoids with low-order quadratic bends and two narrow curved connectors, union-remeshed at 0.024 authored units and lightly smoothed. This is deliberate schematic irregularity, not random bumps or measured nuclear morphology. The intact cytoplasm excludes the exact nuclear volume. The cutaway duplicates those meshes and removes cytoplasm on the viewer-facing side of `y = 0.02` in the authored Blender frame; the whole nucleus remains in its original location. Selected granules are stylized and not exhaustive. Colors are an authored teaching palette, not measured cell colors or a promise of microscopy appearance.

Blender frame: Z up, front view toward +Y from negative Y; GLB exports Y-up. This study has no body origin, patient axes, laterality or whole-body registration.

## Primary references and rights

1. OpenStax, *Anatomy and Physiology 2e*, §18.3, https://openstax.org/books/anatomy-and-physiology-2e/pages/18-3-erythrocytes . Textual and local visual reference for biconcavity. Current page inspected 2026-10-23 states CC BY-NC-SA, not unrestricted CC BY. Its source image is retained **only in local-only-not-for-redistribution**, excluded from the handoff. No OpenStax pixels, vectors or text excerpts are embedded in the model or redistributable comparison plates.
2. OpenStax §18.4, https://openstax.org/books/anatomy-and-physiology-2e/pages/18-4-leukocytes-and-platelets . Qualitative reference for an intracellular lobed neutrophil nucleus and smaller platelets. Same image restriction/exclusion. No physiology rates or blood-count claims carried into the study.
3. **CDC / Dr. F. Gilbert, 1972, PHIL #18906**, https://wwwn.cdc.gov/phil/Details.aspx?pid=18906 . Public-domain blood-smear micrograph, locally inspected. The lower segmented cell is the neutrophil; the arrowhead identifies a lymphocyte, which is not modeled. The lobed nuclear material lies within a surrounding cell area. The image is a 2D microscopy reference, not volumetric ground truth and not the source of this authored mesh. Free source: CDC PHIL. The comparison plate credits CDC and Dr. Gilbert; no CDC endorsement is implied.
4. **NIAID Visual & Medical Arts / Ryan Kissinger, Red Blood Cell, BIOART-000444**, https://bioart.niaid.nih.gov/bioart/444 . Record inspected as public domain; downloaded original illustration via the linked NIAID API. Courtesy of NIAID. Qualitative biconcave-form illustration, not a measurement or microscopy reconstruction.
5. Nachmias, V. T. (1980), *Cytoskeleton of human platelets at rest and after spreading*, Journal of Cell Biology 86:795–802, https://pmc.ncbi.nlm.nih.gov/articles/PMC2110692/ . Primary experimental text supports the restrained discoid platelet depiction. No paper images are packaged; no activation process is simulated.

## Gates and limits

Technical checks, exact-export pixel review, qualitative reference comparison and runtime are separate. This is an educational authored form study, not clinical validation or a patient model. Runtime is unverified: no browser/consumer interaction test has been performed. Static Blender images are not runtime evidence. Do not promote on successful file import alone. Root review of final pixels/reference contrast is required before any limited visual/reference approval.
