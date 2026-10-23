# Portable, dependency-explicit handoff

Reviewer-inspected acceptance: LIMITED STATIC calf → Achilles → heel teaching readability, 2026-10-23. Contextual supplement to the existing musculoskeletal source study only: no new model count, tendon/ligament replacement, duplicate knee count, anatomy or runtime promotion. Final eight-part export includes source Talus.r. Distal tendon scalloping and unvalidated attachment remain explicit.

## Reproduction
External source is NOT included. Obtain the correct `Startup.blend` from the Z-Anatomy source archive, verify SHA256 below, and supply its path explicitly. Never execute the downloaded add-on or bundled scripts.

```sh
blender -b --disable-autoexec -t 2 -P build_proposal.py -- --source /path/to/Startup.blend --output /path/to/output
blender -b --disable-autoexec -t 1 -P check_export_geometry.py -- --source /path/to/Startup.blend --output /path/to/output
python finalize_manifest.py --source /path/to/Startup.blend --output /path/to/output
```

`--skip-renders` on the build command is an optional small export-only replay. Source hash is enforced before loading. This is dependency-explicit reproduction, NOT a self-contained source archive. A fresh-path `FRESH_OUTPUT` test with explicit paths regenerated the GLB byte-for-byte: SHA256 `e38e33c1d0ceb791e4a2ad676dedd7923f53b5ad8d7dc8b195202565609354ea`. Rendering replay uses the same script, exact-export import and recorded camera setup; GPU/platform-dependent pixel identity is not promised.

Exact external dependency:
- Archive URL: https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/master/Z-Anatomy.zip
- Retained archive SHA256: `e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736`
- Retained archive Git blob SHA from original acquisition attribution: `f43cabc6f366b2a6058dd2ed4a2b3c7b9b2492cb`
- Archive member: `Z-Anatomy/Startup.blend`
- Required extracted file SHA256: `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`
- Fresh GitHub metadata confirms matching Git blob `f43cabc6f366b2a6058dd2ed4a2b3c7b9b2492cb`, 86,734,957 bytes. Last archive-change commit: `bb293be456f6d2245191f37752d14ec76894740d` (2024-06-07).
- Pinned public URL: https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/bb293be456f6d2245191f37752d14ec76894740d/Z-Anatomy.zip ; fresh HEAD returned 200 and Content-Length 86734957. Metadata/HEAD checked only; large archive deliberately not redownloaded. Verify retained archive/extracted SHA256 after retrieving. Full check receipt in `source-url-verification.json`.

## Evidence custody
`immutable-evidence-bindings.json` freezes the accepted GLB and six talus-inclusive export PNG hashes plus reviewer acceptance scope. Do not overwrite those image files while retaining their review claim. Generate future revisions in a different output directory. Initial three seven-part PNGs are historical diagnostics only.

The package retains source/license credits and changes under CC BY-SA 4.0; derived GLB AND renders remain share-alike, with no additional restrictions. External AAOS/Cleveland Clinic references are links only; no reference illustrations copied. See ATTRIBUTION.md and SOURCE-LICENSE.txt.

## Concise failure lesson
Floating repeated rods represented routes without tissue shape or attachment context. Replace that claim with a bounded, named same-source spatial relationship; do not use object count as coverage. The improved context still has a scalloped source seam, not a validated enthesis. Exact export audit must compare triangles, not only bounds/counts.
