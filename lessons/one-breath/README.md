# One breath / 一次呼吸

A bounded local teaching prototype: **mechanics → airway route → gas exchange**.
The first two stages assemble the existing s1233 lung morphs and reviewed V7
trachea. The third is an explicitly separate, original alveolar/capillary schematic.
No anatomy masters, gallery, Sites or protected runtime probes are changed.

## Open locally

Requires Git LFS, Python 3.11+ and a browser supporting WebGL2. Both lung models
and both reviewed V7 trachea variants are tracked in this repository. Hydrate
the four pinned model inputs before preparation; no private trachea bundle is
required. A text/LFS-pointer checkout alone cannot display the models.

```sh
git lfs install --local
git lfs pull --include="models/lung_*/exports/metadata-cleanup-r01/*.glb,models/trachea/exports/open-airway-r06/trachea-*.glb" --exclude=""
python3 lessons/one-breath/prepare.py
python3 lessons/one-breath/serve.py --port 8766
```

Open `http://127.0.0.1:8766`. The server binds only to loopback. Preparation resolves
every model from this script's repository, regardless of the working directory;
`--asset-root` optionally selects another hydrated checkout. It checks all four
input sizes/hashes before staging output or downloading the five official Three.js 0.180.0 files
already pinned in `ci/glb-runtime-fixture.json`. A new `.local/` output is required;
existing files are not overwritten. The model loader rejects missing, altered or
externally dependent assets. Asset failures show a retry action. A no-WebGL view
disables breath motion and labels any optional offline composition as static;
the authored exchange schematic remains available. Missing previews are disclosed.

## Learner controls

- **Mechanics:** take/pause one illustrative breath. Lung morphs, diaphragm/rib
  guides, airflow and labels share one breath state; the six-second playback is
  a pacing choice, not a physiological rate.
- **Airway:** trace the same breath through the trachea and the left/right main
  bronchial ports. Stage changes preserve progress. Smaller branches are omitted.
- **Exchange:** select O₂ or CO₂. Air and blood remain visibly separated. Gas
  directions do not reverse during exhalation; exchange has its own continuing
  clock within the shared lesson state.

Reset returns to mechanics/rest while retaining language. EN/中文 covers labels,
actions, loading/error/preview states and short explanations. Reduced-motion
preference makes camera transitions immediate. Port labels use existing V7
terminal opening centers in the retained display frame. The guide route follows
inner-surface slice centers and is editorial, not computed flow.

## Evidence boundaries

The initial isolated Chromium attempt failed before page launch because its SUID
sandbox helper was misconfigured. Later supported-cloud non-WebGL desktop and
500 px browser checks are recorded in [#140](https://github.com/qianyizhang/med-assets/issues/140).
The [availability-status revision](review/availability-status.md) has focused
state/event checks but still needs current browser screenshots and interaction
review. **Live WebGL, animation and camera acceptance remain unverified.** The
existing protected CI-only Firefox probes were not run or altered.

The offline images are actual Blender renders of geometry/morph snapshots emitted
by the same Three.js loader and scene/state functions used by the app. The
bilingual storyboard is an offline composition, not a screenshot of this HTML UI.
The exchange SVG uses the same function as the app. Independent review resolved
out-of-lumen markers, pause drift, midpoint naming and fallback-state defects.
See [review receipts](review/README.md).

```sh
node --test lessons/one-breath/tests/state.test.mjs lessons/one-breath/tests/consumer.test.mjs lessons/one-breath/tests/ui.test.mjs
python3 tools/verify.py offline
```

The 26 targeted Node checks exercise shared state, reset/stage/language data,
actual pinned GLTFLoader/morph consumption, ports, pause behavior and missing/
corrupt-asset rejection/retry. The UI event tests run the actual app body with
DOM, loader and renderer doubles, including detached preview callbacks. They do
not click browser controls, decode preview images or prove layout or WebGL.
The initial source checkpoint's repository offline gate separately passed 183
tests and metadata/pointer checks. See the [repository setup receipt](review/repository-setup.json)
for the fresh checkout's preparation, exact asset/vendor identities and scoped checks.

Optional offline evidence, using Blender 4.3.2 and Inkscape:

```sh
node lessons/one-breath/tests/capture.mjs /tmp/one-breath-NEW
blender --background --factory-startup --python-exit-code 1 \
  --python lessons/one-breath/tests/render_offline.py -- --input /tmp/one-breath-NEW
node lessons/one-breath/tests/board.mjs /tmp/one-breath-NEW
```

For optional static fallback images, copy the resulting `mechanics-rest.png`,
`mechanics-in.png` and `airway.png` into `.local/previews/`. These are labelled
static in the app. No rerender is needed when retained matching evidence exists.

## Sources and limitations

[Attribution and licenses](licenses/ATTRIBUTION.md) and [exact asset identities](assets.json)
travel with the prototype. Source-derived display surfaces are not a healthy atlas.
The retained lung morphs and the diaphragm/rib guides are illustrative. Tracheal
thickness, interior and cuts are authored, not measured specimen wall. Neutral
teaching materials replace source texture display in memory; source GLBs are intact.
No quantitative physiology, biomechanics, CFD, histology or clinical validation.

[OpenStax 22.3](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-3-the-process-of-breathing)
supports diaphragm/chest expansion drawing air in and passive recoil during quiet
expiration. [OpenStax 22.4](https://openstax.org/books/anatomy-and-physiology-2e/pages/22-4-gas-exchange)
supports opposite O₂/CO₂ movement across the alveolar–capillary barrier. The
schematic omits tissue layers and measurements; no reference artwork was copied.
The Techartist page was architectural prompt guidance only; its web page could
not be opened through the available browsing tool. No code or media from it was used.
