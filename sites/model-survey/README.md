# Model survey and R2 delivery

[Public survey](https://med-assets-model-survey.landy123007.chatgpt.site/) ·
[Public asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json)

The survey covers 62 families, 31 products and 141 GLB paths at
`e63006dca598031d58bdf66485fed24a24194558`. Its 92 preview rows use 153 image
pairs. Asset directories and review records remain authoritative; storage changes
do not refresh the survey or promote review gates. Fetus remains recipe-only,
the FDI31/46 pilot preview is labelled FDI31, and neutral renders are unreviewed.

## Owners

| Path | Purpose |
|---|---|
| `app/src/content/`, `app/src/theme.css`, `app/tests/` | Survey interface, theme, R2 delivery and tests. |
| `app/.openai/hosting.json` | Existing Site identity and DB/BUCKET bindings. |
| `framework.lock.json` | Pinned external framework and frozen ZIP URL/size/hash. |
| `snapshot-reference.json` | Original snapshot identities and current `livePublication` reference. Immutable seed, API response and source serialization have separate hashes. |
| `tools/` | Survey reproduction, seed restoration, preview preparation and framework assembly. |
| `.local/publication/` | Ignored publishing Git checkout; retain its remote ancestry. |
| `.local/app/` | Ignored complete generated project; edit the overlays in `app/` instead. |
| `.local/preview/` | Original split preview at http://127.0.0.1:62099/. Its Data preview registration resumes at user login until stopped. |

R2 retrieval and migration are documented once in the
[transport guide](../../transport/README.md). Downloads are public HTTPS and need
no Codex/ChatGPT login. Objects are served by this Site's Worker, not direct bucket
URLs. `/assets/index.json` is the listing; `/assets/` is not a directory browser.

## Restore and build locally

Use Node 24, npm, Git and Python 3.11+. No Sites authentication or Data plugin is
needed for local builds from the frozen backup:

1. Download `framework.lock.json.backup.url`; verify its exact byte count and
   SHA-256 before extraction. The ZIP includes its own restore guide.
2. Set `SURVEY_BACKUP` to the extracted `model-survey-backup/` directory.
3. In a fresh checkout, run these commands from the repository root:

```sh
git clone "$SURVEY_BACKUP/framework.bundle" sites/model-survey/.local/publication
python3.12 sites/model-survey/tools/restore_snapshot.py "$SURVEY_BACKUP/app/src/data.json"
python3.12 sites/model-survey/tools/framework.py
npm --prefix sites/model-survey/.local/app ci
npm --prefix sites/model-survey/.local/app run build
```

Existing source checkouts can supply the same pinned Git objects. Seed restore
accepts only the verified original snapshot, immutable R2 seed or frozen source
seed; it refuses conflicting data and the reordered mutable API response.
Framework assembly checks the commit/tree, integrity manifest, Site bindings and
safe paths, excludes old survey content, and refuses existing output. Use a fresh
`--output` directory when rebuilding the generated project.

Serve the built `dist/` with a local HTTP server. Source-built previews use public
R2 images. The ZIP's `offline/model-survey.html` embeds images and opens fully
offline. Node/npm packages are not bundled; `npm ci` needs public npm access or a
suitable cache. The generated project's unchanged `AGENTS.md` and runtime
verifier govern its source/build boundaries.

## Publish

Use the Data and Sites skills with the generated project. Explicit Data builds
and packaging use `--source` to preserve the custom Worker; do not combine that
mode with `--separate-data`. The local npm step builds the client; source packaging compiles the custom Worker.

Preserve the existing Site/artifact IDs, public audience, owner environment,
stored edits and DB/BUCKET bindings. Reconcile newer remote source, copy checked
materialized source and packaged output into `.local/publication/`, then append
through the Sites helper. Never push the whole med-assets repository or rebuild
after final packaging. Verify complete uploaded assets and fresh readback. Close
temporary asset-upload authorization and redeploy the same saved version afterward.
Current deployment/source identities belong in `snapshot-reference.json`.

## Recipes and checks

`build_survey.py` refreshes reviewed rows from indexed repository sources;
`add_previews.py` embeds retained previews; `render_previews.py` uses exact hydrated
GLBs. These change survey content and require review. `prepare_r2_assets.py`
prepares image objects/URLs locally without uploading:

```sh
python3.12 sites/model-survey/tools/prepare_r2_assets.py \
  --app sites/model-survey/app --output NEW_DIRECTORY \
  --site-url https://med-assets-model-survey.landy123007.chatgpt.site
```

Pillow, Blender, Sharp and Playwright/browser are recipe-specific dependencies.
`MED_ASSETS_REPO` selects another checkout; optional host overrides are
`MODEL_SURVEY_NODE`, `MODEL_SURVEY_SHARP_MODULE`,
`MODEL_SURVEY_PLAYWRIGHT_MODULE`, `MODEL_SURVEY_BROWSER` and
`MODEL_SURVEY_PREVIEW_URL`. Browser captures go to ignored `.local/qa/`.

```sh
python3.12 -m unittest discover -s tests -p 'test_model_survey_*.py' -v
node sites/model-survey/.local/app/scripts/verify-protected-runtime.mjs
node --test sites/model-survey/app/tests/r2-assets.test.mjs
python3.12 tools/verify.py offline
```

## Retention

Keep the frozen ZIP and its delivery entry while the pinned framework or survey
depends on it. Keep source/data/license references, publishing history, original
offline exports (`app/.data-app-*`), authoring Git bundle and unique deployment
archives in the existing ignored recovery locations. The ZIP is never added to
Git. Historical source recovery also remains in the original publication manifest
under `.local/recovery/` and publication commit
`f69d31708d87500f761b430de1a0113294ffb1d3`.

Stop preview users before moving their directory. Review scratch renders/captures
by 2026-12-06; no background update or deletion is scheduled. Existing eye,
trabecular-spacing and heart-applicability disagreements remain in the survey
with proposed corrections; no anatomy/clinical/WebGL acceptance is implied.
