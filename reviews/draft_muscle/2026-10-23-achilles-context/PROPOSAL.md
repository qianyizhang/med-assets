# Right Achilles contextual study — accepted limited static contextual supplement

**Supersedes the initial seven-part read-only diagnostic.** Final export adds the retained exact source-named `Talus.r` because its omission made the distal tibia/fibula arrangement visually misleading. The eight selected source meshes remain in native evaluated world space, without authored shape changes or inferred attachment bridges.

- Export: `achilles-right-context-proposal.glb` (~0.5 MB), source/dependency hashes in `dependency-manifest.json`.
- Exact-export evidence: `export-posterior.png`, `export-lateral.png`, `neutral-oblique.png`, `heel-close-lateral.png`, `heel-close-posterior.png`, `heel-close-neutral-oblique.png` (all final GLB reimports; no hidden parts). Camera/image binding in `export-render-binding.json`.
- Initial `posterior.png`, `lateral.png`, `oblique.png` are retained as earlier seven-part diagnostics, NOT evidence of the final talus-inclusive export.
- Reference check: `REFERENCE-CHECK.md`; license/credit: `ATTRIBUTION.md` and retained `SOURCE-LICENSE.txt`.
- Reproducibility: `build_proposal.py`, `check_export_geometry.py`, `finalize_manifest.py`; source `.blend` deliberately referenced, not duplicated.

## Failure / lesson, concise
Baseline: floating repeated rods/fans, no tissue-specific shape or attachment context. Lesson: teach a named same-source relationship, not a route marker or model count.
Proposal limitation: inherited sculpted calf ridges, thin lateral tendon profile and scalloped distal edge. Preserve these visibly; do not mistake a visual contact seam for validated enthesis. No attachment continuity, histology, biomechanics, complete ankle joint, proximal muscle origins, clinical use or full tendon/ligament coverage claim.

## Transport outcome
Native source loop triangles are used to avoid silently changing source quad diagonals in GLB conversion. Final unique surface triangles compared to retained source at 1e-7 native-unit coordinate rounding; all named mesh bounds exact. Two coincident duplicate triangles on medial gastrocnemius lose multiplicity; one loose tendon vertex and nineteen loose fibula vertices are omitted by surface-only export. These are explicit transport differences, not source repairs. Winding/watertightness/attachments not certified. See detailed `source-vs-export-geometry.json` and `transport-verdict.json`, not just object count.

## Remaining decision
Reviewer inspected the FINAL talus-inclusive exact-export pixels and accepted limited static teaching readability only. Publication, canonical registry/asset replacement, runtime and anatomy gates remain untouched/unverified. Existing knee ligament study is linked in manifest only, not copied or counted again. Patellar/hand/biceps gaps remain open.
