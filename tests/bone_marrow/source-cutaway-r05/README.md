# Reproduce the bounded teaching cutaway

Dependencies actually used: Blender4.3.2 (NumPy included), Python3 + Pillow, DejaVu Sans and Noto Sans CJK SC for annotation. Not bundled. No script installs dependencies or fetches files. Fetch the2 exact public inputs in provenance.json and check their hashes/bytes. `SOURCE` is the12.7MB canonical skeleton GLB; `BASELINE` the34KB original marrow GLB. All outputs must be NEW paths.

```sh
T=tests/bone_marrow/source-cutaway-r05
C=models/bone_marrow/exports/authored-source-cutaway-r05/marrow_cutaway.glb
blender -b --python-exit-code 1 --python "$T/build.py" -- --source "$SOURCE" --out new-build
blender -b --python-exit-code 1 --python "$T/verify_geometry.py" -- --source "$SOURCE" --candidate "$C" --out new-check
blender -b --python-exit-code 1 --python "$T/render.py" -- --baseline "$BASELINE" --candidate "$C" --out new-renders
blender -b --python-exit-code 1 --python "$T/render_baseline.py" -- --baseline "$BASELINE" --out new-baseline
python3 "$T/compose.py" --renders new-renders --baseline new-baseline --out new-evidence
```

Build~1min, geometry verifier~1min,4 views~1min on shared CPU. Build replay was byte-exact for final GLB; safety guards tested. Native images were actually rendered from fresh final GLB. No guarantee of byte/pixel identity across Blender versions/platforms. Visual comparison to pre-portable r05 has small pixel differences, explicitly recorded—not called pixel-identical. Source-derived geometry/rights and independently authored components remain distinguished.

Baseline composite guard checks exact1000×1200 RGBA dimensions/pixel SHA, not PNG container bytes: Blender may embed changing metadata while pixels remain identical. The baseline renderer still hash-checks original GLB bytes, and output bindings record each actual PNG byte SHA. This correction was tested with an independently regenerated baseline.
