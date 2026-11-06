# Model survey Site

[Existing private Site](https://med-assets-model-survey.landy123007.chatgpt.site/) · [local preview](http://127.0.0.1:62099/)

Dated, derived survey of med-assets at `e63006dca598031d58bdf66485fed24a24194558`
(2026-11-06). Asset directories and review records remain authoritative. Moving
this source does not refresh the survey or promote any asset review gate.

## Ownership

| Path | Purpose |
|---|---|
| `app/` | Complete authoring source, owned by this repository. Its scoped `AGENTS.md` governs app changes. |
| `tools/` | Survey, preview-generation and browser-check recipes. |
| `snapshot-reference.json` | Immutable dataset, artifact and existing publication identities for recovery. |
| `.local/publication/` | Ignored Sites publishing checkout, retaining its Git history; ignored build output still belongs to original version 2. Publish only this checkout, never the whole med-assets repository. |
| `.local/preview/` | Original verified split build; preview remains on port 62099. |
| `.local/preview-renders/` | Exact input-bound neutral previews and SVG raster cache. These are unreviewed inventory views. |
| `.local/recovery/authoring.bundle` | Verified complete original authoring Git history before adoption into this repository. |
| `.local/deployment-v2.tar.gz` | Exact archive for original version 2. |

Ignored `app/src/data.json` retains the complete small dataset using content-addressed R2
image URLs, matching current publication source `f65265ca3c7d94790a86537e6ef725241fc012ea`.
The original complete inline-image dataset, verified split bundle and portable HTML
remain under ignored `app/.data-app-offline/`. Binary image payloads, generated
builds and local Git checkouts stay outside source Git.

## Build and recovery

Use the installed Data and Sites skills. The local dataset is complete and
contains 153 image pairs as immutable URLs; the protected Data source rules keep
reviewed snapshots outside Git. The original inline-image dataset can
be recovered with Data's `hydratePublicationSource` using the original immutable
manifest at `.local/recovery/original-publication-source.json`, or from that file
in publication commit `f69d31708d87500f761b430de1a0113294ffb1d3`. Verify bytes,
hash and artifact ID against `snapshot-reference.json`; never substitute mutable
hosted data for historical immutable recovery.

On a fresh checkout, open the **existing** Site using the Sites source helper in
`.local/publication/`. Preserve its remote ancestry. Current source includes the
published R2 delivery Worker and its tests. The current remote commit omits its
seed file and removed its recovery manifest. This move retains the original
manifest and adds `tools/restore_snapshot.py`: pass the recovered original
snapshot (or the retained current seed) to restore ignored `app/src/data.json`.
The recipe validates all image bindings and the exact current snapshot hash
before writing; it refuses conflicting output. Copy the seed when preparing
a new publication.
Reconcile any newer remote source before publishing. Never push the whole
med-assets repository to the Sites source endpoint.

For current Worker publication use the Data source build (`--source
--separate-data`) with compatible Vite dependencies, respecting `app/AGENTS.md`.
The preserved original local preview and portable export need no rebuild. Keep
the Site/artifact IDs, database, owner environment, stored edits and owner-only
access. Upload complete immutable assets and verify full readback. The retained publication `dist/` is version 2, so rebuild current source before
new packaging. Package checked output without rebuilding after packaging. Local relocation does not redeploy.

Reproduction recipes default to this med-assets repository; override
`MED_ASSETS_REPO` for another checkout. `tools/build_survey.py` refreshes reviewed
rows from indexed sources; `tools/add_previews.py` embeds retained previews and
needs Pillow. `tools/render_previews.py` runs in Blender with hydrated,
hash-matching inputs. A refresh changes survey content and requires review;
it is separate from moving or publishing existing output. Do not commit regenerated
inline-image payloads to source Git; retain those in ignored
offline/reproduction output and preserve the content-addressed publication data.

SVG rasterization needs Node and Sharp. Browser recipes need Playwright and an
installed browser. Standard package resolution is used; optional overrides are
`MODEL_SURVEY_NODE`, `MODEL_SURVEY_SHARP_MODULE`,
`MODEL_SURVEY_PLAYWRIGHT_MODULE` (module file URLs) and `MODEL_SURVEY_BROWSER`
(browser executable). Browser screenshots go to `.local/qa/`. Follow the host's
browser-launch policy. Keep the preview's existing origin to retain browser-local
presentation state. Its registered Data preview resumes at user login until
explicitly stopped; no survey refresh or cleanup is scheduled.

## Publication and verification

The original publication identities and executable integrity hashes are recorded
in `snapshot-reference.json`. Site ID:
`appgprj_6aed57a59dc88191a981c07e56d283e7`; published source:
`f69d31708d87500f761b430de1a0113294ffb1d3`. The same source checkout and deployment
are retained. A concurrent publication advanced to version 3 during relocation;
its exact source is adopted in `app/` and retained in `.local/publication/`.
All report fields are identical except the 306 image/thumb values: every new R2
URL was verified against the original decoded image SHA-256. The live deployment
identity matches `livePublication` in `snapshot-reference.json`; native status is
succeeded. Platform-injected scripts make the browser HTML hash vary.

- Complete snapshot: 11,729,768 bytes, four queries / 238 rows.
- Coverage: 62 families, 31 products, 141 GLB paths; 92 preview rows / 153 unique images.
- Fetus remains recipe-only without retained model/pixels. The FDI31/46 pilot's
  preview is explicitly FDI31. Neutral Blender views remain unreviewed.
- Existing report disagreements remain labelled with proposed corrections: eye
  coverage, trabecular spacing and superseded heart applicability text.
- Original browser evidence covers tree slices, preview decoding/navigation,
  zoom/fit, keyboard controls and 390px light/dark reflow. Relocation checks reuse
  unchanged content and additionally exercise the relocated preview.
- Relocation preserves original source/data/build bytes and Git history, then
  adopts the concurrently published R2 source and byte-equivalent image references. Required repository offline verification is reported in the PR.
  No new anatomy, clinical, WebGL or signed-in hosted editing acceptance is implied.

Node publication/readback on the current host needs its configured HTTPS proxy
(`NODE_USE_ENV_PROXY=1`); direct Node requests previously reached a Cloudflare
challenge. Native tools own credentials and environment settings. Never retain
credentials in source, archives, command arguments or logs.

Retain source, complete data, source/license references, current publication output
and recovery history while this Site depends on them. Review scratch renders and
QA captures by **2026-12-06**; stop the preview before moving/removing its directory.
The sibling project was retired after source/data/build copy integrity, local
preview checks, image-reference equivalence and hosted deployment verification.
