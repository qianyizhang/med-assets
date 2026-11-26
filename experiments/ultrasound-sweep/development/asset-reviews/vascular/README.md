# Carotid wall and blood-pool qualification

The baseline at `0d943e4` capped the isolated outer wall across the blood channel. The candidate connects the outer and inner wall at each editorial cut, and gives the flat cut its own normals. Ring spacing follows the largest interpolation error in either the wall or lumen. The case acquisition recipe still owns the center, radius and eccentric plaque profile.

The review compares 61 named part/case bindings. The before and after images use the same orthographic camera, scale, lighting and neutral material for each pair. The end detail is centered on the distal cut. Repeated images share an image file. The original CCA and right jugular examples come from the standalone carotid sweeps. Their independently fitted bounds and different subject are labeled.

Each numeric result is an agent assessment of the named isolation task. Original and revised wall openness was checked by ray intersection. The exported ring traces were compared against independent calls to the sampling recipe on a 0.2 mm station grid. Triangle and geometry-buffer byte counts share the same scope. The angular trial measures the distance from the original odd-indexed vertex to the midpoint of the replacement chord. No clinical-performance claim follows from those checks.

Run `node experiments/ultrasound-sweep/cases/vascular/verify-surfaces.mjs STUDY_DELIVERY` against a full assembled study to repeat the contour checks.
