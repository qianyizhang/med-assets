# Source-native ovary and tubal-end context

[ovary-tubal-context.glb](ovary-tubal-context.glb) is a separate static candidate
for comparing both coarse ovary exteriors with their acquired native tubal/fimbrial
context. The historical `draft_ovaries` schematic and its animation remain separate.

The GLB contains all 10 acquired meshes, 12 source nodes and 4 source materials:
18,728 vertices and 36,885 triangles. It is 681,552 bytes, SHA-256
`465a44b18df91ece95a236372a8cbe3e1a0de0207525955290e6b0fa519195d1`.
All names, source extras, transforms, geometry, materials, gaps and cut ends are
preserved. Only container indices/offsets and scene/asset metadata change.

Use the [bilingual teaching sheet](../../../../lessons/ovary-tubal-context/README.md)
for a source-labelled overview and full acquired side views. L/R follow source
names. The presentation does not establish patient orientation. Coarse exterior
relationships are the intended use; follicles, uterus, ligaments, attachment,
continuous lumen, motion and clinical use are outside scope.

Sources: Kristen Browne and Heidi Schlehlein, HuBMAP / HRA; ovary v1.3 and fallopian
tube v1.2, CC BY 4.0. [Exact originals, manifest and credits](../../../../sources/datasets/hra/ovary-tubal-context/README.md).

From the repository root, with exact source LFS payloads available:

```sh
python3 tools/ovary_tubal/build.py --root . --output /tmp/ovary-tubal-replay/ovary-tubal-context.glb
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python tools/ovary_tubal/render.py -- --root . --candidate /tmp/ovary-tubal-replay/ovary-tubal-context.glb --output /tmp/ovary-tubal-renders
```

Use new output paths. Build replay is byte-identical. Blender 4.3.2 clean-import
checks compare all world-space triangle data, corner normals, parent/name inventory,
matrices and material values against four separate source imports. Three camera,
scale and lighting matched source/export views have identical RGB pixels.
Native static checks do not certify browser runtime or anatomy. See the
[bounded review](../../../../reviews/ovaries/2026-10-30-hra-ovary-tubal-r01/README.md).
