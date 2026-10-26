# r04 — scoped gross-component relationship improvement

Candidate SHA256: `c44d35e13be11d2fb35141747d819d4609a45ca0a5527c89e1015618d17cab70`.

## Actual visual review

Personally inspected all5r04views: minus-y, plus-y, side, oblique, inferior-source; original baseline whole; r03minus-y only as rejected diagnostic. Corrected r04 is a meaningful improvement over the baseline's flat-ended cylinder, sphere-like glans and lateral rods. The source form shows a curved corporal body with paired proximal sides, a distinct central/ventral spongiosum with a larger proximal bulb, and a glans at its distal end. These component relationships are coherent enough for a **labeled gross erectile-component teaching study**, not complete organ anatomy.

The cavernosa are one connected source mesh: paired proximal form is visible, but an internal septum or2separately delineated chambers is not. Skin, prepuce, tunica, vessels and nerves are absent. No continuous urethral lumen is modeled/verified. A dark distal spot must not be promoted to a validated meatus or continuous passage. Uniform smooth surface and coarse proximal facets remain visible limitations. No motion/functional/clinical validation.

## Critical transform correction

r03 used stale matrix_world before dependency-graph update and was rejected. Source location/rotation0 and scale1 did not imply an identity world transform: matrix_basis/world include component-specific translations after update. r04 now preserves native placement. Earlier near-origin bounds in source-topology.json are obsolete for relationship review; use source-transform-check.json and r04-source-export.json.

## Independent source/export evidence

Selective loading only3namedsource meshes, with autoexec disabled; default scene objects excluded. Corrected source-world positions map bijectively to all3freshly imported export meshes with maximum difference59.72nm. Oriented triangle topology matches after mapping. This is float32-tolerance preservation, not byte-identical coordinates.

Source cavernosa646V/1288tri and spongiosum282V/560tri each1component, closed edge incidence and Euler2. Glans694V/1391tri retains1boundary edge and2additional incidence3edges (3edges not incidence2 total). No zero-area triangles. Source glans/spongiosum surfaces have139finite-precision triangle contacts; contact is not a watertight union or lumen proof.

## Glans defect is not duplicate cleanup

No duplicate unoriented triangles in the source glans. Unique source triangle924 touches all3problem edges:2have incidence3,1has incidence1. Removing it would delete a unique source surface triangle, not merely deduplicate serialization. Do not fill an opening, remove this triangle, or smooth it under a preservation-only claim. Detailed evidence: glans-edge-detail.json. Preserve the actual defect and limit acceptance to gross component relationships.

## Decision

Accept **scoped visual/gross-component improvement** with explicit missing-lumen and source-edge-defect caveats. Not complete internal anatomy, watertight printable mesh, clinical model, animation/runtime pass, or full original organ approval. Whole original status remains Needs revision; count delta0. References/licensing gates in REFERENCE-GATES.md still apply; no external publication or geometry mutation performed by this review.
