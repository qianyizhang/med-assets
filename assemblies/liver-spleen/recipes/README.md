# HRA female liver and spleen replay

- **Outcome** · Exact current liver and spleen exterior GLBs, in the original HRA frame.
- **Inputs** · [Pinned external atlas](../../../sources/datasets/hra/united-female-v1.10/external-source.json), Python with NumPy and a fresh output directory. Supply the atlas locally and run without Python `-O`.
- **Acceptance** · Checks source and final hashes. Optional Blender 4.3.2 `--render` produces material/neutral diagnostic views and exact-coordinate topology audits. Keep those results distinct from legacy BMesh diagnostics.
- **Scope** · Scoped static appearance, with open region patches possible. Anatomy unreviewed and runtime unverified. Retained WebPs are lossy derivatives. Native scene and render history remains deferred.

```sh
python3 assemblies/liver-spleen/recipes/replay.py --source "$hra_atlas_glb" --output "$fresh_output"
```
