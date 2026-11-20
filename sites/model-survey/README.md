# Model survey and R2 delivery

[Public survey](https://med-assets-model-survey.landy123007.chatgpt.site/) ·
[Public asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json)

- **Outcome** · Browse 62 asset families, 31 products and 141 GLB paths at `e63006dca598031d58bdf66485fed24a24194558`. 92 preview rows use 153 image pairs.
- **Scope** · Dated survey. Asset directories and review records own current status. Fetus is recipe-only, the FDI31/46 pilot preview is FDI31, and neutral renders remain unreviewed.

The [gallery design guide](../../guideline/design.md) maps catalogue entries to verification candidates and related system views.

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

- **Asset bytes** · [Public downloads and R2 migration](../../transport/README.md).

## FDI31 prepared specimen

The [FDI31 entry](https://med-assets-model-survey.landy123007.chatgpt.site/?view=1#swirendo_fdi31)
opens the specimen card with its preview, review, limitations and Balanced GLB.
The download checks the published manifest and verifies the file size and
SHA-256 before saving. The card also links to the GitHub export.

The [legacy focus review](https://dental-fdi31-focus-review-oct28.landy123007.chatgpt.site/fdi31/)
serves the [bilingual notice](retirements/fdi31/index.html) with links to
the survey and canonical R2 bytes. On 2026-11-19 the survey and legacy
notice reached public version 7. The survey revision is recorded in
[`snapshot-reference.json`](snapshot-reference.json). The legacy Site
source is `75c28214f68cec33cf7a83abcab7bcdcee2d543a` and its deployment
is `appgdep_6afea201fdb4819185df77820acaa74a`.

Chrome readback matched the public 1,001-route index, Balanced GLB, and
the pinned framework backup ZIP against their checked-in identities.

## Restore and build locally

- **Outcome** · Reproducible local build from the pinned framework and immutable seed.
- **Inputs** · Node 24, npm, Git and Python 3.11+. Verify the frozen ZIP against `framework.lock.json.backup` before extraction. Set `SURVEY_BACKUP` to its `model-survey-backup/` directory. The ZIP contains its restore guide.
- **Build** · From the repository root with fresh output paths.

```sh
git clone "$SURVEY_BACKUP/framework.bundle" sites/model-survey/.local/publication
python3.12 sites/model-survey/tools/restore_snapshot.py "$SURVEY_BACKUP/app/src/data.json"
python3.12 sites/model-survey/tools/framework.py
npm --prefix sites/model-survey/.local/app ci
npm --prefix sites/model-survey/.local/app run build
```

| Check | Acceptance |
| --- | --- |
| Seed | Verified snapshot, immutable R2 seed or frozen source seed. Conflicts and the reordered mutable API response fail. |
| Framework | Pinned commit/tree, integrity manifest, Site bindings and safe paths. Use a fresh `--output`. The generated project's instructions and runtime verifier apply. |
| Preview | Serve `dist/` locally for a source-built preview with public R2 images. Open the frozen `offline/model-survey.html` directly for embedded images. `npm ci` needs npm access or a populated cache. |

## Publish

| Goal | Acceptance |
| --- | --- |
| Package custom Worker | Authorized Data/Sites publication from the generated project. Use `--source` without `--separate-data`. npm builds the client. Source packaging compiles the Worker. |
| Preserve live identity | Reconcile newer remote source. Retain Site/artifact IDs, public audience, owner environment, stored edits, DB/BUCKET and publishing ancestry. Append checked source and exact packaged output through the Sites helper. |
| Verify publication | Check the deployed revision and affected live flow. Apply [transport upload acceptance](../../transport/README.md#upload-acceptance) to uploaded assets. Update `snapshot-reference.json` with deployed identities. [Temporary upload closeout](../../transport/README.md#add-or-reverify-r2-copies). |

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
node --test sites/model-survey/app/tests/fdi31-download.test.mjs
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
