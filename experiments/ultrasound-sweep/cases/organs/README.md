# Worked organ ultrasound cases

The [case data](cases.json) follows fictional abdomen, thyroid, breast and axillary referrals from the initial acquisition to the recorded impression. The visits include normal, abnormal and technically limited outcomes. For each visit, the plates show representative acquisition checkpoints, and the captions describe actions between them.

| Family | Modeled visits |
| --- | --- |
| Abdomen | Comprehensive survey, mobile gallstone, right hydronephrosis with a postvoid recheck, and pancreatic obscuration on repeat imaging. |
| Thyroid | Normal lobe and isthmus survey, right mid-lobe TR5 nodule with orthogonal measurement and cervical node assessment, and a hidden left inferior pole. |
| Breast and axilla | Bilateral supplemental coverage, a targeted retroareolar cyst, an asymmetric axillary node, and an incomplete retroareolar assessment. |

The [builder](build.py) owns the case records and section geometry. It projects caliper endpoints into the same coordinate system as each plate and converts their separation to millimetres. Tissue boundaries, acoustic appearances and Doppler traces are authored teaching illustrations. The flow examples convey qualitative patterns. Clinical comparisons are linked by study and figure or clip in the case records. They describe separate acquired exams and retain the original source attribution. The existing [sweep research record](../../research/README.md) owns the acquired orientation references supplied to the case library.

From the repository root, run:

```sh
python3.12 experiments/ultrasound-sweep/cases/organs/build.py
python3.12 experiments/ultrasound-sweep/cases/organs/build.py --check
```

The replay check compares the delivered case JSON and SVGs byte-for-byte against their authored source and rejects extra SVGs. The shared case library validates the case IDs, route coverage and image paths during assembly. Source baseline for this local iteration is `62286a1697e5d9464d2a92311b01083222d80875`. Clinical fidelity and protocol completeness remain open for sonographer review.

## Playable acquisition

The [acquisition module](playable.js) exposes ordered chapters and tissue sections in patient coordinates. The [3D adapter](playable-scene.js) fits an exterior using the standalone sweeps and renders internal shapes from the case volumes. In [the abdominal cases](playable-abdomen.js), most organ boundaries come from authored centers and radii. The standalone abdominal sweeps sample the s1233 CT masks. The fitted exterior and agreement between the modeled section and its calipers establish placement and internal consistency for this teaching model. The abdominal organ shapes still need matched landmark and contour review for claims about anatomical fidelity. B-mode appearance, motion, beam attenuation and Doppler are illustrative.

- **Abdomen** includes subcostal and splenic windows, orthogonal sections, vessel and pancreatic windows, biliary repositioning, and a focused bilateral renal and bladder sequence through postvoid recheck.
- **Thyroid** includes bilateral and isthmus dimensions, nodule orthogonal sections, cervical nodes, and a repeat limited by clavicular shadow.
- **Breast and axilla** includes a cranial-to-caudal overview, six overlapping bilateral passes, radial and antiradial cyst views, and orthogonal axillary and contralateral node scans. The retroareolar reattempt uses a different trajectory through the same nipple region.

Run `node experiments/ultrasound-sweep/cases/organs/test-playable.mjs` to check changing section and locator geometry, exact evidence-frame measurements, replay links and representative repeat outcomes. Every record view resolves to a playable chapter. The local Chrome spot check decoded seven representative canvas pairs and compared scan and locator pixels across frames.

The breast gland and tail use footprints and anterior/posterior depth samples from the original gland mesh. The B-mode section and the 3D surface share the calibrated depth envelope. The retromammary fat sits immediately anterior to the pectoral fascia. See the [matched breast assessments](../../development/asset-reviews/organs/reviews.json).

The bilateral supplemental screening traverses use 1 mm steps across each band. The geometry check covers the modeled gland, fat and axillary tail down to their posterior extents. This is a check of the authored case geometry.

The anatomy overlay follows the same tissue contours, field boundaries, layer order and acoustic shadow as the B-mode image. Its legend lists tissue sampled within the visible field. The shared 3D scene shows both analytic and profiled surfaces.
