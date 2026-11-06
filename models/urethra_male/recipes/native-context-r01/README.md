# Rebuild and render
Requirements: Blender4.3.2 with bundled glTF import/export, Python3 with Pillow, NotoSansCJK-Regular.ttc at the standard Debian font path. Software/fonts are dependencies, not bundled. Use `--disable-autoexec` for the untrusted atlas file.

Supply the external pinned `Startup.blend` SHA2569f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd; see source provenance for archive URL/hash. Never open the complete atlas scene or enable its scripts.

In a new work directory W, place the original baseline as W/baseline.glb, SHA256368638eb652ab42feb177e5be97708714f8950038199072c94ddbcb2a115cb92. Baseline URL: https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/assets/drafts/pelvis/urethra_male.glb . It is external and not bundled.

```
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python build.py -- --source /path/Startup.blend --out W/r01
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_opaque.py -- --work W
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_translucent.py -- --work W
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python render_baseline.py -- --work W
python compose.py --work W
python annotate.py --work W
```
Build validates the source hash before creating its new output directory. Render/composition outputs must not already exist. No source geometry repair is performed. Source names, native effective transforms and final hashes are written in source-members.json. Render bindings distinguish camera directions from validated anatomical axes. PNG metadata may vary between working paths; compare decoded pixels, not only PNG byte hashes.

Additional checks (new outputs only):
```
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify_native.py -- --source /path/Startup.blend --work W --out W/source-check.json
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify_surface.py -- --work W --out W/surface-check
```
The portable native verifier adapts the independent review algorithm to explicit guarded arguments; its local replay is separate from the original independent review. Vertex-distance matching does not establish anatomical interfaces or every possible topology property.
