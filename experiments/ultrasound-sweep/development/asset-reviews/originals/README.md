# Original sweep reference surfaces

Seven full-organ or gland meshes from the s1233 and s1127 sweeps were inspected at matched physical scale. The starting files were the delivered binary mesh and the SHA-256-pinned, 1.5 mm isotropic source segmentation for that subject. The reference surface uses a half-label isosurface. The lighter trial uses the same mask, a Gaussian filter with sigma 0.85 voxel, and a marching-cubes step of four voxels. Each version stays in the original RAS coordinate system.

Distances in measurements.json are nearest sampled-surface distances in millimetres. Each sample set contains vertices, face centroids and edge midpoints. Pole errors compare extrema on the superior–inferior axis. These measurements do not establish clinical morphology or a subvoxel worst-case error bound. The original native meshes remain the reference selection.

For the thyroid, five sagittal planes centered on the smallest label area between the two lateral lobe area maxima were also compared in-plane. [Bridge measurements](thyroid-bridge.json) record pole-to-pole depth and bidirectional contour discrepancies for each plane.

Label source: TotalSegmentator v2.0.1, Jakob Wasserthal, contributors and University Hospital Basel, CC BY 4.0. The compact mesh and its matching case/mask hash are recorded in measurements.json. [Dataset and terms](https://zenodo.org/records/10047263)
