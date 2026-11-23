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

Search for **Cardiac opaque exteriors** in the candidate Gallery to open static r02. **Inspect in 3D** opens the exact model with individual structure selection. **Exact exports** offers the pinned GLB download. The static r01 and repository-source animation are in the same revision history. The [r02 package](../../heart/exterior-presentation-r02/README.md) owns replay and recovery. The recommended revision and its shareable 3D preset belong to the candidate build. Public release is tracked separately in [AG-GAL-020](../../records/work-items/items/AG-GAL-020-adopt-static-heart-repack.md#public-release).

### First bronchial fork

From **Use Cases → Airway Review → Trace the first bronchial fork**, select **Inspect in 3D** in the candidate build to load the faired r15 at the central Y. The [r15 package](../../models/bronchial_tree/exports/first-fork-fairing-r15/README.md) owns replay. Revision history retains the r14 distal simplification and r13 source comparison, including their exact downloads and saved Stage presets.

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

Run the [bootstrap](tools/bootstrap.py) from the repository root with Python 3.12, uv, Git, Node 24 and npm. Start with the Gallery's tracked media and reviewed PNG masters hydrated. Supply the frozen ZIP from the [framework lock](framework.lock.json) if the pinned framework checkout or Survey seed is missing.

```sh
python3.12 sites/anatomy-gallery/tools/bootstrap.py --selection candidate \
  --backup "$SURVEY_BACKUP_ZIP" --output sites/anatomy-gallery/.local/gallery-candidate
node sites/anatomy-gallery/tools/preview_gallery.mjs sites/anatomy-gallery/.local/gallery-candidate 8858
```

Use `--offline` for subsequent fresh outputs with the pinned viewer files, npm packages and uv wheels already available. Bootstrap verifies the local framework commit, tree, runtime manifest, Site bindings and seed identity on each run. The first run can fetch the pinned Three.js files and MIT license, install the lockfile's npm packages, and fetch the exact Pillow versions. A build appears at `--output` after protected runtime verification and client compilation.

- **Framework and seed** · Bootstrap can use the existing `.local/publication` checkout and `app/src/data.json`, or recover missing inputs from the verified ZIP into `.local/bootstrap`. Supply another pinned checkout with `--source` and an exact seed or immutable snapshot with `--seed`. The restored Model Survey seed keeps its recorded bytes. The assembled app uses the Anatomy Gallery title.
- **Viewer inputs** · Bootstrap verifies the sizes and hashes in [the viewer lock](viewer.lock.json). Use `--viewer-inputs` to point at another copy. To recover from a corrupt cache, restore into a fresh path with [the viewer command](tools/gallery_runtime.py) and use that directory.
- **Generated WebPs** · [Display bindings](../../sources/display-derivatives.json) select Pillow 11.3.0 with libwebp 1.5.0 or Pillow 12.2.0 with libwebp 1.6.0. Bootstrap verifies the hydrated PNGs and any cached WebPs, and fills missing display bytes before validating campaign evidence. The lossless WebP settings preserve exact RGBA.
- **Published rehearsal** · Use `--selection published --source /path/to/site-checkout` and a fresh `--output`. The selected checkout must contain the exact commit in [the live publication record](snapshot-reference.json). Bootstrap verifies the seed-derived snapshot before building the rehearsal.

Assembly writes the Library and study API read models and the release’s resource
manifest into the built project. Preview uses the selected project’s read handler
and verifies exact local payload bytes. The generated candidate Worker uses the
same read rules with R2. The public asset index owns upload admission. See
[Library selections](../../docs/gallery/asset-library.md#making-a-release-selection)
and the [route and API contract](../../docs/gallery/routes-and-api.md).

The v10 rehearsal uses the frozen publication source and a catalog adapter so its
selection is independent of preview hostname. Retain the adapter while v10
requires source reconstruction. Once a compatible immutable release bundle
replays the UI, API and resource routes, retire the source patch for that release.

For legacy catalogue thumbnails and portraits, the loopback preview can also read
the exact original snapshot from `.local/preview/dist/snapshot.<sourceSnapshotSha256>.json`.
The retained original snapshot and the standalone offline HTML have their own
recovery paths. Neither supplies the Site's Three.js modules.

### Archive media

A hydrated checkout supplies the dental video treatments and the retained kidney contact WebP through the usual Gallery preview. The six Image 2.6 films use the existing [teaching backup](../body-systems-survey/README.md#restore-the-media). To restore only this study, from the repository root:

```sh
python3.12 transport/tools/restore_collection.py teaching-media --subset dental-image26 \
  --from-zip .artifacts/teaching-backup/med-assets-teaching-c803735.zip
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
`MODEL_SURVEY_PREVIEW_URL`. The Gallery browser runner writes one receipt and capture directory per case under
`.artifacts/gallery-verification/` by default. Set `MODEL_SURVEY_CAPTURE_DIR` for a dedicated run. Set `MODEL_SURVEY_APP_DIR` to the preview's generated app
directory when it differs from `.local/app`. The verifier walks the ordinary Library
against the pinned AG-GAL-018 Git baseline and checks exact downloads and teaching evidence.
The build assembles the dated pilot, owner-held `reviews/<asset>/<review>/teaching-assessment.json` files and the [current teaching assessments](../../reviews/teaching-assessments/current-assessments.json). Each current record pins its base assessment and carries accepted changes and reviewer attribution. The [maintained selections](../../docs/gallery/maintained-selections.json) bind each export and stable learner task ID to that accepted record. The [shared resolver](../../lib/med_assets/teaching.py) supplies those records to the Gallery and [scorecard](../../records/campaigns/teaching-asset-review/current-coverage.md). Run `python3.12 tools/maintained_teaching.py` from the repository root to print the generated Markdown to stdout. Its tracked destination is `docs/gallery/maintained-models.md`. Pass `--check` to validate all accepted tasks and verify the register and scorecard. Use the [promotion workflow](../../docs/guides/teaching-assessments.md) to update the accepted state.

Bind each review to the exact export's path, size and SHA-256. Use a local source path or HTTPS reference and give every reviewed image a digest and size. An optional `teachingView` selects one image for the learner. Preview verifies evidence bytes before delivery. An accepted local review can declare its exact `library/<family>/<revision>` route. Files that share a route keep their own tasks, views and scores. When a refinement candidate matches a maintained export in SHA-256 and size, the download uses that export's filename and verified bytes.

The [first target review](../../records/campaigns/teaching-asset-target.md), [reopened exemptions](../../records/campaigns/teaching-exemption-recheck.md), and [refinement review](../../records/campaigns/teaching-asset-refinement.md) retain the earlier decisions and comparison evidence. The scorecard links to the explicit historical audit.

The focused authoring run uses the same loopback runner as the full Gallery check. It exercises the real s1233 study through all four surfaces, including an unavailable comparison witness, the exact Library download, and a Stage shared view and its WebP.
Run the browser suites against the local candidate preview with hydrated media. The Library case requires the AG-GAL-018 Git baseline. Archive playback requires the restored teaching-media selection. The lesson-plates case also uses `MODEL_SURVEY_PUBLISHED_PREVIEW_URL` for a separate published rehearsal to check what is included there. The packaged bookmark replay uses the exact public and a test origin in a disposable browser. Pass the packaged project directory to `verify_survey_bookmarks.mjs`.

```sh
python3.12 -m unittest discover -s tests -p 'test_model_survey_*.py' -v
node sites/anatomy-gallery/.local/app/scripts/verify-protected-runtime.mjs
node --test sites/anatomy-gallery/app/tests/r2-assets.test.mjs
node --test sites/anatomy-gallery/app/tests/fdi31-download.test.mjs
node --test sites/anatomy-gallery/tools/preview_gallery.test.mjs
node sites/anatomy-gallery/tools/verify_gallery.mjs --authoring
node sites/anatomy-gallery/tools/verify_gallery.mjs
node sites/anatomy-gallery/tools/verify_gallery.mjs --list
node sites/anatomy-gallery/tools/verify_gallery.mjs --suite catalog --suite scenes
node sites/anatomy-gallery/tools/verify_gallery.mjs --suite lessons --suite evidence
node sites/anatomy-gallery/tools/verify_gallery.mjs --case library
node sites/anatomy-gallery/tools/verify_gallery.mjs --all
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

Exercise the two bilingual ovary entries and image recovery with `node sites/anatomy-gallery/tools/verify_gallery.mjs --ovary` using the browser settings above. The [shared Cardiac Atlas](../../heart/Cardiac_Atlas_Animated/exports/shared-source-r01/) is exercised by the `refinement-scenes` case through both ordinary Library lessons.

Run `node sites/anatomy-gallery/tools/verify_gallery.mjs --case layer-lessons` with the browser settings above to exercise the six right-arm, salivary and pelvic tasks. It checks landmark marking, camera retention, exact-byte rejection, retry and usable answers with WebGL unavailable. Hydrate the small WebP inputs under `app/src/content/gallery/part-images/` when assembling the Gallery.
