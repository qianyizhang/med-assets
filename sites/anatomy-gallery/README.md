# Anatomy Gallery

[Public Site](https://med-assets-model-survey.landy123007.chatgpt.site/) ·
[Public asset index](https://med-assets-model-survey.landy123007.chatgpt.site/assets/index.json)

- **Model Survey archive** · The dated catalogue records 62 asset families, 31 products and 141 GLB paths at `e63006dca598031d58bdf66485fed24a24194558`. 92 preview rows use 153 image pairs. Asset directories and review records own current status. Fetus is recipe-only, the FDI31/46 pilot preview is FDI31, and neutral renders remain unreviewed.

Use the [Gallery authoring guide](../../docs/gallery/README.md#author-a-gallery-entry) to add a Library record, lesson, comparison or Stage view.

## Gallery entry points

The ordinary report entry opens Asset Library in list view. Tree and cards share its metadata, filters and rating-aware sort. Body Systems opens an eleven-system teaching collection under Use Cases. The s1233 adrenal study runs through Use Cases, Compare and 3D Stage. The separate BodyParts3D review opens in Compare and returns to the selected family. Head & Neck uses retained salivary views in Use Cases and Compare and links the two exact r02 exports in Library. Airway Review opens the nasal, tracheal and bronchial studies. Its local first-fork teaching stop opens r15 and links the original r13 comparison. Old family bookmarks and the planning survey remain available. See the [canonical routes and API](../../docs/gallery/routes-and-api.md). The [public release record](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#public-release-and-readback) identifies the live Gallery and its rollback point.

Use Cases also opens the bilingual oral-spaces cutaways and four regional locators. The local preview serves their owner-held WebPs and retained PNG fallback through the asset index. Each regional stop links the exact source GLB, and the oral lesson links the original vectors. See the [teaching routes](../../docs/gallery/use-cases.md#oral-spaces-and-regional-locators).

The Gallery also opens the three bilingual pathway diagrams and the interactive dental arch. Experiments & Archive contains the left kidney outline trial and both dental film collections. The [collection ledger](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#collection-ledger) records the collection destinations and the public Head & Neck and Airway handoffs.

### Files in the imported atlas packages

The Static Cardiac Atlas entry attaches the ten RAS-mm STL exports and editable Blender file to its [static ED delivery](../../docs/gallery/routes-and-api.md#page-links). The original **All indexed files** disclosure is available on the family overview. For the original texture study, use the [retained UV layout and texture maps](../../heart/Cardiac_Atlas/textures/), [normal-map measurements](../../heart/Cardiac_Atlas/textures/Normal_QA.json) and [diagnostic render recipe](../../heart/Cardiac_Atlas/render_normal_diagnostic.py). The imported guide’s render paths refer to its original distribution.

The Breathing delivery groups its editable assembly with the eleven animated GLBs. The GLBs sit beside the [animation manifest](../../body/breathing/animation-manifest.json). Their [static inputs](../../body/anatomy-workshop-r1/meshes/) and [attribution](../../body/breathing/NOTICE.md) are in the checkout. The [portable replay](../../body/breathing/README.md#replay-and-verify) rebuilds the clips from those meshes.

### Static opaque heart exterior

Search for **Cardiac opaque exteriors** in the loopback Gallery to open static r02. **Inspect in 3D** opens the exact model with individual structure selection. **Exact exports** offers the pinned GLB download. The static r01 and repository-source animation are in the same revision history. The [r02 package](../../heart/exterior-presentation-r02/README.md) owns replay and recovery. The recommended revision and its shareable 3D preset are available on the local preview. Public release is tracked separately in [AG-GAL-020](../../records/work-items/items/AG-GAL-020-adopt-static-heart-repack.md#public-release).

### First bronchial fork

From **Use Cases → Airway Review → Trace the first bronchial fork**, select **Inspect in 3D** to load the locally faired r15 at the central Y. The [r15 package](../../models/bronchial_tree/exports/first-fork-fairing-r15/README.md) owns replay. Revision history retains the r14 distal simplification and r13 source comparison, including their exact downloads and saved Stage presets.

## Owners

| Path | Purpose |
|---|---|
| `app/src/content/`, `app/src/theme.css`, `app/tests/` | Gallery interface, theme, R2 delivery and tests. |
| `app/.openai/hosting.json` | Existing Site identity and DB/BUCKET bindings. |
| `framework.lock.json` | Pinned external framework and frozen ZIP URL/size/hash. |
| `viewer.lock.json` | Official Three.js r180 module and MIT license URLs, sizes and SHA-256 values. |
| `snapshot-reference.json` | `surveySeedPublication` pins the frozen Survey inputs and v7 recovery. `livePublication` binds the current Gallery release, HTML, snapshot and API response. |
| `tools/` | Survey reproduction, local preview and framework assembly. |
| [Transport tools](../../transport/tools/) | Seed and legacy media restore, delivery manifest preparation, fetch and upload. |
| `.local/publication/` | Ignored publishing Git checkout; retain its remote ancestry. |
| `.local/app/` | Ignored complete generated project; edit the overlays in `app/` instead. |
| `.local/preview/` | Retained split preview and original snapshot. The old preview was stopped during the package move. Use the loopback command below for the current Gallery. |

- **Asset bytes** · [Public downloads and R2 migration](../../transport/README.md).
- **Delivery index** · [The source index](app/src/content/assets/delivery-index.json) declares the public asset routes. Assembly writes a byte-identical `r2-trial.json` in the generated project for the protected Worker imported from the pinned framework.

## FDI31 prepared specimen

The [FDI31 entry](https://med-assets-model-survey.landy123007.chatgpt.site/?view=1#swirendo_fdi31)
opens the Library specimen with its preview, review, limitations and Balanced GLB.
The download checks the published manifest and verifies the file size and
SHA-256 before saving. The card also links to the GitHub export.

The [legacy focus review](https://dental-fdi31-focus-review-oct28.landy123007.chatgpt.site/fdi31/)
serves the [bilingual notice](retirements/fdi31/index.html) with links to
the survey and canonical R2 bytes. On 2026-11-19 the survey and legacy
notice reached public version 7. The survey revision is recorded in
[`snapshot-reference.json`](snapshot-reference.json). The legacy Site
source is `75c28214f68cec33cf7a83abcab7bcdcee2d543a` and its deployment
is `appgdep_6afea201fdb4819185df77820acaa74a`.

At the November 19 release, Chrome readback matched the 1,001-route index, Balanced GLB, and
the pinned framework backup ZIP against their checked-in identities.

## Restore and build locally

- **Outcome** · Reproducible local build from the pinned framework and immutable seed.
- **Inputs** · Node 24, npm, Git and Python 3.11+. Verify the frozen ZIP against `framework.lock.json.backup` before extraction. Set `SURVEY_BACKUP` to its `model-survey-backup/` directory. The ZIP contains its restore guide.
- **3D runtime** · Run the Site's viewer command once with network access to fetch the exact upstream modules and MIT license in [the lock](viewer.lock.json). Framework assembly uses those files offline and checks every size and digest before promoting the output. If an input is missing or differs, restore to a fresh directory with `gallery_runtime.py --output DIRECTORY` and pass it to `framework.py --viewer-inputs DIRECTORY`.
- **Build** · From the repository root with fresh output paths.

```sh
git clone "$SURVEY_BACKUP/framework.bundle" sites/anatomy-gallery/.local/publication
python3.12 transport/tools/restore_snapshot.py "$SURVEY_BACKUP/app/src/data.json"
python3.12 sites/anatomy-gallery/tools/gallery_runtime.py
uv run --python 3.12 --with 'Pillow==12.2.0' python -c 'from PIL import features; assert features.version("webp") == "1.6.0"'
uv run --python 3.12 --with 'Pillow==11.3.0' sites/anatomy-gallery/tools/framework.py
npm --prefix sites/anatomy-gallery/.local/app ci
npm --prefix sites/anatomy-gallery/.local/app run build
```

| Check | Acceptance |
| --- | --- |
| Seed | Verified snapshot, immutable R2 seed or frozen source seed. Conflicts and the reordered mutable API response fail. The generated app uses the Anatomy Gallery title while the restored Model Survey seed retains its recorded bytes. |
| Framework | Pinned commit/tree, integrity manifest, Site bindings and safe paths. Use a fresh `--output`. The generated project's instructions and runtime verifier apply. |
| Generated WebPs | [Source and display bindings](display-images.json) select Pillow 11.3.0 with libwebp 1.5.0 or Pillow 12.2.0 with libwebp 1.6.0. Both use RGBA, lossless, exact alpha and method 6. Assembly uses the older encoder in the current process and runs the newer encoder through the offline uv cache when needed. It verifies each source and the delivery size and digest before caching the WebP at its ignored package path. Hydrate the PNGs and rerun assembly to fill a pointer-only checkout. Use `uv run --offline` for assembly after caching both wheels. |
| Preview | Run `node sites/anatomy-gallery/tools/preview_gallery.mjs sites/anatomy-gallery/.local/app 8858` for a read-only loopback preview of the built Site, rubric, study API and verified local delivery. Hydrate the study GLBs and WebPs for full local viewing. Open the frozen `offline/model-survey.html` directly for embedded images. `npm ci` needs npm access or a populated cache. |

For legacy catalogue thumbnails and portraits, the loopback preview can also read
the exact original snapshot from `.local/preview/dist/snapshot.<sourceSnapshotSha256>.json`.
The retained original snapshot and the standalone offline HTML have their own
recovery paths. Neither supplies the Site's Three.js modules.

### Archive media

A hydrated checkout supplies the dental video treatments and the retained kidney contact WebP through the usual Gallery preview. The six Image 2.6 films use the existing [teaching backup](../body-systems-survey/README.md#restore-the-media). To restore only this study, from the repository root:

```sh
zip=.artifacts/teaching-backup/med-assets-teaching-c803735.zip
printf '%s  %s\n' ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014 "$zip" |
  shasum -a 256 -c &&
  unzip -n "$zip" 'experiments/dental-image26/results/*' &&
  rg '  experiments/dental-image26/results/' sites/body-systems-survey/backup-sha256.txt |
  shasum -a 256 -c
```

After restoring a film, select **Retry video** in the running preview. The preview serves those six MP4s only when local content matches the member digests. The Gallery uses its existing public delivery index for other media. Image 2.6 playback has a separate public delivery decision.

### Legacy Dental Review media

The local dental reviews include the exact original studio PNGs and GLBs for
cotton tweezers and mouth mirror, plus the historical prepared-incisor PNG.
Restore those ten payloads from the repository root with Python 3.12 and curl.

```sh
python3.12 transport/tools/restore_legacy_dental.py
```

The [lock](app/src/content/assets/legacy-dental-assets.json) pins the public
source URL, byte count and SHA-256 for each original. The command writes the
verified bytes to the ignored `.local/legacy-dental/` cache. The read-only
preview checks the cache at request time, so a restored file becomes available
on reload. The tracked WebPs preserve the reviewed pixels. Public cutover of
these exact routes needs a separate delivery decision.

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
python3.12 transport/tools/prepare_r2_assets.py \
  --app sites/anatomy-gallery/app --output NEW_DIRECTORY \
  --site-url https://med-assets-model-survey.landy123007.chatgpt.site
```

Pillow, Blender, Sharp and Playwright/browser are recipe-specific dependencies.
`MED_ASSETS_REPO` selects another checkout; optional host overrides are
`MODEL_SURVEY_NODE`, `MODEL_SURVEY_SHARP_MODULE`,
`MODEL_SURVEY_PLAYWRIGHT_MODULE`, `MODEL_SURVEY_BROWSER` and
`MODEL_SURVEY_PREVIEW_URL`. The ordinary Gallery browser check writes to
`.artifacts/gallery-library-systems/` by default. Give the Library verifier a dedicated
`MODEL_SURVEY_CAPTURE_DIR`. Set `MODEL_SURVEY_APP_DIR` to the preview's generated app
directory when it differs from `.local/app`. The verifier walks the ordinary Library
against the pinned AG-GAL-018 Git baseline and checks exact downloads and teaching evidence.
The build assembles the dated pilot, owner-held `reviews/<asset>/<review>/teaching-assessment.json` files and the [maintained-file campaign](../../records/campaigns/teaching-asset-review.md). Campaign batches live under `reviews/teaching-assessments/<batch>/campaign-assessments.json`. Bind each review to the export's path, size and SHA-256. Use a local source path or an HTTPS reference, and supply a digest and size for every reviewed image. An optional `teachingView` selects one of those images for the learner. The read-only loopback preview serves these local reviews and checks evidence bytes before delivery. The [coverage report](../../records/campaigns/teaching-asset-review/current-coverage.md) includes native assemblies and missing scores. Both the report and Gallery read accepted refinement decisions through the [shared loader](../../tools/teaching_assessments.py). A decision binds to the previous task and assessment as well as to the exact export. The [first target review](../../records/campaigns/teaching-asset-target.md) links the 45 follow-up decisions, retained exemptions and collection checks. The [reopened exemptions](../../records/campaigns/teaching-exemption-recheck.md) cover every remaining low score and retain owned follow-ups. The [previous refinement review](../../records/campaigns/teaching-asset-refinement.md) retains the 46 original comparisons. A maintained local export can declare its exact `library/<family>/<revision>` route in that assessment. The build verifies its bytes and groups files that share a route. Each file keeps its own task, views and scores. When a refinement candidate matches a maintained export in SHA-256 and size, the download uses that export's filename and verified bytes.

The focused authoring run uses the same loopback runner as the full Gallery check. It exercises the real s1233 study through all four surfaces, including an unavailable comparison witness, the exact Library download, and a Stage shared view and its WebP.
The packaged bookmark replay uses the exact public and a test origin in a disposable browser. Pass the packaged project directory to `verify_survey_bookmarks.mjs`.

```sh
python3.12 -m unittest discover -s tests -p 'test_model_survey_*.py' -v
node sites/anatomy-gallery/.local/app/scripts/verify-protected-runtime.mjs
node --test sites/anatomy-gallery/app/tests/r2-assets.test.mjs
node --test sites/anatomy-gallery/app/tests/fdi31-download.test.mjs
node --test sites/anatomy-gallery/tools/preview_gallery.test.mjs
node sites/anatomy-gallery/tools/verify_gallery.mjs --authoring
node sites/anatomy-gallery/tools/verify_gallery.mjs
MODEL_SURVEY_CAPTURE_DIR=.artifacts/library-verification node sites/anatomy-gallery/tools/verify_library.mjs
MODEL_SURVEY_CAPTURE_DIR=.artifacts/teaching-target-verification node sites/anatomy-gallery/tools/verify_teaching_target.mjs
MODEL_SURVEY_CAPTURE_DIR=.artifacts/heart-exterior-verification node sites/anatomy-gallery/tools/verify_heart_exterior.mjs
MODEL_SURVEY_CAPTURE_DIR=.artifacts/bronchial-exterior-verification node sites/anatomy-gallery/tools/verify_bronchial_exterior.mjs
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

Exercise the two bilingual ovary entries and image recovery with `node sites/anatomy-gallery/tools/verify_gallery.mjs --ovary` using the browser settings above. The [shared Cardiac Atlas](../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/) is exercised by `verify_refinement_scenes.mjs` through both ordinary Library lessons.

Run `node sites/anatomy-gallery/tools/verify_part_lessons.mjs` with the browser settings above to exercise the six right-arm, salivary and pelvic tasks. It checks landmark marking, camera retention, exact-byte rejection, retry and usable answers with WebGL unavailable. Hydrate the small WebP inputs under `app/src/content/gallery/part-images/` when assembling the Gallery.
