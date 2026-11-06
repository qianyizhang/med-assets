# Model survey Site

[Existing public Site](https://med-assets-model-survey.landy123007.chatgpt.site/) · [local preview](http://127.0.0.1:62099/)

Dated survey at med-assets `e63006dca598031d58bdf66485fed24a24194558`.
Asset directories and review records remain authoritative. Source separation does not refresh the survey or change its features. The later
user-authorized frozen backup adds one public ZIP delivery route.

## Source ownership

| Path | Owner |
|---|---|
| `app/src/content/`, `app/src/theme.css` | Survey interface, theme and R2 asset delivery. |
| `app/.openai/hosting.json`, `app/tests/` | Existing Site identity/bindings and survey-specific Worker tests. |
| `framework.lock.json` | Exact external framework commit, Git tree and integrity-manifest hash. |
| `tools/`, repository `tests/test_model_survey_*.py` | Survey reproduction, framework assembly and checks. |
| `snapshot-reference.json` | Artifact, immutable data, source serialization and publication recovery identities. |
| `.local/publication/` | Ignored existing Sites Git checkout and source history. Also supplies the pinned framework Git objects. |
| `.local/app/` | Ignored complete app assembled from the framework plus survey source. Its restored `AGENTS.md` and integrity checks govern builds. Never edit this generated copy. |
| `.local/preview/` | Preserved original verified split build on port 62099. |

The framework remains in the **existing Sites source repository**, at the locked
revision, as an external dependency. There is no new Site or framework repository.
Fresh checkouts can restore the pinned Git dependency from the public frozen ZIP
in `framework.lock.json`; Sites source authentication is optional for local builds.
The ZIP's included README covers checksum verification, extraction, direct local
builds and Git-bundle restore. Clone `model-survey-backup/framework.bundle` into
`.local/publication/`, then pass that Git directory to `tools/framework.py`.
Publishing still uses the existing Sites owner/source authorization. An owner can
also open the existing source with the Sites helper into `.local/publication/`.
Preparation
then runs offline and reads the pinned Git object, not the remote branch tip,
ignored build output or installed plugin template. Keep the remote history.

`tools/framework.py` checks the commit/tree, runtime-manifest hash, Site bindings,
artifact identity and safe paths, then adds the survey overlays and complete seed.
The dependency's old survey content is excluded, so removing an authored file
cannot silently restore an old report. It refuses missing/wrong dependencies,
links and existing output. Use a fresh
`--output` directory for another build; source, user data and prior builds are
never overwritten. No background download, update or cleanup is scheduled.

## Prepare and build

Restore ignored `app/src/data.json` first. The current source seed is 520,272 bytes;
its hash differs from both the immutable deployed seed and mutable API response.
`tools/restore_snapshot.py` accepts the original inline-image snapshot or the exact
immutable R2 seed, verifies image bindings, and reconstructs the exact source
serialization. It refuses conflicting output and the reordered API response.

The original immutable manifest remains at
`.local/recovery/original-publication-source.json`, also recoverable from
publication commit `f69d31708d87500f761b430de1a0113294ffb1d3`. Use Data's
`hydratePublicationSource` with that original source checkout/manifest to recover
the complete historical snapshot. Never use mutable `/api/snapshot` as immutable
seed recovery. Keep credentials in memory/stdin, outside source and logs.

From the med-assets root, after restoring the pinned Git dependency:

```sh
python3.12 sites/model-survey/tools/restore_snapshot.py PATH_TO_VERIFIED_SNAPSHOT
python3.12 sites/model-survey/tools/framework.py
npm ci --prefix sites/model-survey/.local/app
node DATA_PLUGIN_ROOT/scripts/data-app.mjs build --project-dir sites/model-survey/.local/app --source
```

Use Node 24 and the pinned package lock. `DATA_PLUGIN_ROOT` above denotes the
installed Data plugin path, not another repository dependency. The explicit source
build preserves the custom R2 Worker. Build modes are mutually exclusive:
`--source` produces a complete HTML build; do not combine it with `--separate-data`.
The generated project contains the unchanged protected runtime and its verifier.

For a browser preview of this complete source build, serve its `dist/` with the
Data preview helper. The existing port-62099 preview and offline export remain
available without rebuilding. The registered preview resumes at user login until
stopped. Browser-local presentation belongs to its existing origin.

## Publish and recover

Keep project `appgprj_6aed57a59dc88191a981c07e56d283e7`, artifact identity,
DB/BUCKET bindings, owner environment, stored edits and the **current public**
audience. The retained trial objects, frozen backup and declared Git-pinned repository
payloads use public reads;
writes remain owner-only or require a short-lived scoped upload authorization.

Use the Data and Sites publishing skills with the assembled complete project.
Both build and packaging must use `--source` to preserve the custom Worker.
Reconcile newer remote source, copy the checked materialized source/output into
the existing `.local/publication/` checkout, and append to its history using the
Sites helper. Never push the whole med-assets repository. Never rebuild between
final packaging and publication. Verify full asset uploads/readback as usual.
Source-only separation required no deployment; the backup delivery addition is
published through this existing workflow.

The current public version 4 uses source
`c950ac2c059701944e5444d37518edb2f8a8f6f1`; its deployment and separate immutable,
API-response and source-seed hashes are recorded in `snapshot-reference.json`.
All report fields remain unchanged except that 306 image/thumb values use R2 URLs
binding the original decoded bytes. Variable platform scripts prevent using the
browser HTML response hash as packaged-byte identity.

Ignored original offline assets/exports remain in `app/.data-app-*`, the complete
original authoring history in `.local/recovery/authoring.bundle`, and the exact
version 2 archive in `.local/deployment-v2.tar.gz`. The retained publication `dist/` now matches version 4. Rebuild changed source
before new packaging.

## Checks and limits

```sh
python3.12 -m unittest discover -s tests -p 'test_model_survey_*.py' -v
node sites/model-survey/.local/app/scripts/verify-protected-runtime.mjs
node --test sites/model-survey/app/tests/r2-assets.test.mjs
python3.12 tools/verify.py offline
```

Survey recipes default to this repository; `MED_ASSETS_REPO` can select another
checkout. Preview generation needs Pillow; neutral renders need Blender and
hydrated, hash-matching GLBs. SVG rasterization needs Node/Sharp; browser recipes
need Playwright and a browser. Optional host overrides remain
`MODEL_SURVEY_NODE`, `MODEL_SURVEY_SHARP_MODULE`,
`MODEL_SURVEY_PLAYWRIGHT_MODULE`, `MODEL_SURVEY_BROWSER` and
`MODEL_SURVEY_PREVIEW_URL`. Do not commit regenerated inline-image datasets.

Coverage remains 62 families, 31 products and 141 GLB paths; 92 preview rows use
153 image pairs. Fetus is recipe-only; the FDI31/46 pilot preview is labelled
FDI31. Neutral views remain unreviewed. Existing report disagreements retain
proposed corrections for eye coverage, trabecular spacing and superseded heart
applicability text. No anatomy/clinical/WebGL acceptance is promoted by builds.

Retain source/data/license references, current publication recovery and original
history while the Site depends on them. Review scratch renders and QA captures by
2026-12-06; stop preview users before removing their directory. No automatic
retirement is scheduled. Follow the configured HTTPS proxy for Node publication
on this host (`NODE_USE_ENV_PROXY=1`).

## Frozen backup without Sites authentication

`framework.lock.json.backup` pins the public R2 URL, exact 10,710,642-byte size
and SHA-256 of the frozen ZIP. Verify all three before extraction. It contains
the complete framework Git bundle, frozen buildable source with the exact seed
and npm lock, restore instructions, and the original self-contained offline HTML.
Node/npm dependencies are not bundled; ordinary builds fetch public npm packages
unless cached. The embedded-image offline HTML needs neither npm nor network.

The archive stays outside Git. Preserve this object while the pinned framework
or survey depends on it; retain its delivery manifest entry in future deployments.
The current source's ZIP addition is an overlay on the
frozen framework; the backup intentionally remains byte-identical to its verified
f65265c snapshot. The delivery manifest permits this exact object and serves it
as an attachment. General CI/LFS transport allowlists are unchanged.

Full anonymous R2 readback verified the ZIP's exact size/hash. Anonymous PUT,
DELETE and unlisted ZIP requests were rejected; the report data and an existing
preview image still matched. The temporary asset-upload environment was removed
and version 4 redeployed at environment revision 6; the owner setting is unchanged.

## On-demand retrieval and preview preparation

From the repository root, `python3.12 tools/fetch_asset.py PATH --commit REV`
reads the exact committed LFS pointer and downloads the matching public R2 object
into the ignored, content-addressed cache. It refuses redirects, wrong sizes,
encoding changes, corrupt data and symlink caches. A verified cache hit avoids
network access. Missing/unpublished objects fail explicitly; this command does
not overwrite source paths or silently change providers.

`tools/prepare_r2_assets.py --app sites/model-survey/app --output NEW_DIRECTORY
--site-url https://med-assets-model-survey.landy123007.chatgpt.site` prepares
embedded image bytes and immutable URLs locally, preserving existing manifest
entries and review metadata. It does not upload. Reassemble the complete project
with `tools/framework.py` into a fresh ignored directory after changing overlays,
then follow the source build/publication steps above. The current public trial
and frozen backup are retained; only the existing owner workflow can publish.

## Repository payload migration

The same R2 delivery manifest now covers all 689 LFS payloads and five directly
tracked Git data/evidence blobs >=1 MB at the pinned migration revision. The
copy set is 694 unique payloads / 976,485,579 bytes. Existing preview and backup
routes remain. Check the completed migration result before assuming a newly
declared object is available; reads fail explicitly for unavailable storage.

Use the repository's [R2 retrieval/migration guide](../../transport/README.md#repository-payload-copies-in-r2)
for source verification, bounded upload/readback, on-demand cache/hydration and
retention. Report data and its review statuses are unchanged.
