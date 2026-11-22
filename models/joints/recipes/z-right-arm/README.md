# Shared Z-Anatomy right arm

Build the elbow and shoulder ligament studies, right rotator-cuff localization, and
ulnar-nerve elbow study from one selection of the pinned Z-Anatomy source. The recipe
evaluates each of the 22 named members once. All four use the same right humerus.
The elbow and ulnar study also reuse the radius and ulna. The shoulder and cuff
reuse the scapula. The four GLBs keep only the surfaces used by each task.

Use Blender **4.3.2** for replay of the retained files. Obtain and hash the archive
and extract only `Z-Anatomy/Startup.blend` according to the
[pinned provenance](../../../../sources/datasets/z-anatomy/ulnar-elbow/provenance.json).

```sh
blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python models/joints/recipes/z-right-arm/build.py -- \
  --source /path/to/Startup.blend --out /tmp/z-right-arm-new

blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python models/joints/recipes/z-right-arm/verify.py -- --source /path/to/Startup.blend
```

Use a fresh output path. The build checks the member hash before appending the
selected objects. The output directory appears after all four exports finish.
The verification command checks retained bytes, imports both normal and
disposably edited exports, and exercises wrong-source, existing-output and
partial-export failure paths.

The joint editions retain their baked world-coordinate mesh encoding and original
embedded `regional_elbow_r01` and `regional_shoulder_r01` source selection
identities. The Gallery identifies the newly assessed files by their r02 paths.
The cuff and nerve editions retain their translation-bearing native meshes.
glTF uses the single native swizzle `(x, y, z) → (x, z, −y)`. All selections use
the source right side and illustrative materials for the surfaces and capsule.

| Selection | Exact file |
| --- | --- |
| Elbow capsule, four ligaments and three bones | [Elbow r02](../../exports/z-elbow-r02/README.md) |
| Glenohumeral capsule, labrum, five ligaments and three bones | [Shoulder r02](../../exports/z-shoulder-r02/README.md) |
| Four cuff muscles and two bones | [Rotator cuff r01](../../exports/z-rotator-cuff-r01/README.md) |
| Ulnar nerve and three elbow bones | [Ulnar elbow r02](../../../peripheral_nerves/exports/ulnar-elbow-r02/README.md) |

The source-aware replay preserves the selected model topology, surface detail
and scopes as assessed in the [matched review](../../../../reviews/teaching-assessments/2026-11-23-z-right-arm-replay/README.md).
Selection, display finishes and coordinate conventions follow the original
export packages. Z-Anatomy geometry and derived images use
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Retain historical
BodyParts3D / The Database Center for Life Science CC BY-SA 2.1 Japan credit and
the [provider notice and license](../../../../sources/datasets/z-anatomy/ulnar-elbow/License.txt).
