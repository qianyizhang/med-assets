# Female HRA liver: scoped exterior study

Capsule, bare area and six named source ligaments; exterior representation only.

Illustrative materials on the selected exterior source components; no position/index/normal change.

Static visual scope passed; anatomy unreviewed and runtime unverified. Source region patches can remain open. Native HRA frame, not s1233 or body registration.

## Explicit external source dependency

The exact **374,505,632-byte united-female v1.10 atlas is not included** in this small PR. Its official immutable URL, SHA-256, metadata and license are in `sources/datasets/hra/united-female-v1.10/external-source.json`. Obtain it separately if rebuilding; there is no automatic download or hidden bulk Git LFS migration.

```sh
python tests/liver_spleen/replay.py --source /path/to/3d-vh-f-united.glb --output /tmp/liver-spleen-replay
```

Python 3 + NumPy required. Optional `--render` requires Blender 4.3.2 and produces offline candidate-material/neutral diagnostic views. Fresh output only; exact final hashes and source identity are enforced. Generic exact-coordinate topology audit runs separately from legacy BMesh diagnostic fields; neither certifies anatomy. The 2 WebPs are lossy display derivatives, not original lossless PNGs. Native scene/render history is deferred.
