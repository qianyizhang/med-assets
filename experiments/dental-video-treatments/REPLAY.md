# Replay and checks

Run from the repository root. Python 3.11+ and Git are sufficient for source checks. Media checks additionally need FFmpeg/ffprobe. Real rendering needs the separately installed, pinned engine dependencies. No render runs during ordinary offline CI.

```sh
P=experiments/dental-video-treatments
git lfs pull --include="$P/**"
python3 "$P/replay.py" check --payloads
python3 "$P/replay.py" check --movies
python3 tools/verify.py offline
```

`--payloads` rejects missing LFS bytes and checks hashes/sizes. `--movies` also fully decodes all retained movies and checks duration, frame count, dimensions and audio format. Neither is listening, clinical approval or browser interaction QA. The whole-repository payload gate is separate and requires all unrelated historical media.

## Prepare isolated builds

The output must not exist. Use another name for a repeat run. This validates source/audio/font identities, copies just one engine and the shared inputs, and generates HyperFrames HTML with an exact original-output hash check.

```sh
python3 "$P/replay.py" prepare hyperframes --output "$P/.work/hyperframes"
python3 "$P/replay.py" prepare remotion --output "$P/.work/remotion"
python3 "$P/replay.py" prepare manimgl --output "$P/.work/manimgl"
```

The working directories contain no dependencies. Install only the engine being evaluated. The collection replay used Node.js 24.22.1 for the browser renderers. DejaVu Sans must be available to the operating system for Remotion and Pango/ManimGL; its exact regular/bold files are included in `fonts/`. HyperFrames loads the included files directly.

### HyperFrames

```sh
cd "$P/.work/hyperframes"
npm ci
HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 npx hyperframes check --json
HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 npx hyperframes render . --fps 30 --quality looks --workers 2 --no-browser-gpu -o output.mp4
```

Uses the managed headless browser with software GPU. The original six-scene file produces maintainability recommendations to split subcompositions; these are not a zero-warning pass. The source is preserved rather than refactored during collection.

### Remotion

```sh
cd "$P/.work/remotion"
npm ci
npx remotion browser ensure
NODE_OPTIONS="--require=$PWD/loopback-only.cjs" npx remotion render src/index.tsx DecayFile output.mp4 --concurrency=2
```

The adapter only bypasses unsupported network-interface enumeration within this renderer process; it does not change OS/network/security settings. Omit it on normal hosts if unnecessary. The exact shared master is copied to `public/final-mix.wav`.

### Original 3b1b ManimGL

Python 3.12, a C/C++ compiler, pkg-config, Cairo/Pango headers, FFmpeg and OpenGL/EGL are required. No LaTeX is used. The Python lock is not a container image or a lock for native libraries.

```sh
cd "$P/.work/manimgl"
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
XDG_CACHE_HOME=$PWD/cache MPLCONFIGDIR=$PWD/cache/matplotlib .venv/bin/python render_egl.py mineral_ledger.py MineralLedger -w -r 1280x720
ffmpeg -y -i videos/MineralLedger.mp4 -i audio/final-mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -movflags +faststart -t 48 output.mp4
```

Leave `LEDGER_START` and `LEDGER_DURATION` unset for a complete 48-second render. The headless adapter selects the supported ModernGL EGL backend without modifying upstream packages. A graphical machine can use native `manimgl` instead. Re-encoding/platform variation may change hashes; do not overwrite the retained final or claim bitwise identity without comparing.

### Synchronized review

```sh
python3 "$P/comparison.py" --output "$P/.work/comparison.mp4"
```

This reads the three retained movies, overlays engine/title labels, scales them to 640×360, and uses one audio track. FFmpeg and the included font payloads are required. Output must not exist.

## Audio regeneration is optional

The frozen master is the canonical replay input. Generating new audio requires the additional Kokoro model/runtime download and can change performance/timing. See `audio/README.md`; do not treat a new voice render as the same comparison without rechecking every film.
