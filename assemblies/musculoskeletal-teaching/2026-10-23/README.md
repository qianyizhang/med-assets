# Right calf–Achilles–heel contextual study

Limited reviewer-inspected **static teaching supplement**, not a complete tendon/ligament model. Eight same-source right-sided meshes include the talus. No new accepted-model count; original tendon/ligament draft remains Needs revision. No anatomy, attachment, clinical or browser-runtime pass.

- Exact GLB: `e38e33c1d0ceb791e4a2ad676dedd7923f53b5ad8d7dc8b195202565609354ea` (517,676 bytes).
- Six original final PNGs and exact source/export checks retained under `reviews/draft_muscle/2026-10-23-achilles-context/`.
- **Geometry AND renders: CC BY-SA 4.0.** Preserve attribution/change notices and upstream credits in `ATTRIBUTION.md` and `SOURCE-LICENSE.txt`.
- Native Z-Anatomy frame; no cross-atlas registration or whole-body substitution.
- Distal scalloped seam is not a validated enthesis. Two duplicate source triangles and loose vertices are omitted by surface transport; unique surface coordinates remain. Triangle-multiset checks do not certify winding, manifoldness or clinical accuracy.

## Explicit external source, not included
Pinned archive: https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/bb293be456f6d2245191f37752d14ec76894740d/Z-Anatomy.zip — 86,734,957 bytes. Archive SHA `e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736`; member `Z-Anatomy/Startup.blend`, SHA `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`. Obtain explicitly; scripts never download the archive. No bundled add-on execution.

## Recheck
Run integrity verification from this repository:
```
python tests/achilles_context/verify_receipt.py
```
For reconstruction, use Blender 4.3.2 and a **new empty output location**:
```
blender -b --disable-autoexec -t 2 -P tests/achilles_context/build_proposal.py -- --source /path/to/Startup.blend --output /new/output --skip-renders
```
Fresh export-only replay reproduced exact reviewed GLB bytes. Native rendering is separate and pixel identity across platforms is not promised. This is dependency-explicit, not self-contained source delivery.

**Lesson:** floating rods describe routes, not tissue relationships; a useful bounded spatial study still does not establish attachment anatomy.
