# Gallery routes and API

The existing Model Survey Site serves one HTML application. A page link identifies where a visitor was working. An asset URL identifies exact bytes. An API response supplies data. Preserve these three contracts independently when adding a collection or migrating a host.

## Page links

Open the fragment on the Site root, for example `/?view=1#/library/s1233-adrenal/r05`. The browser owns the fragment, so a deep link, reload or Back navigation can use the same Worker entry. A legacy public file URL must still return its expected media. The [migration plan](migration.md#page-addresses-and-file-addresses) owns cross-host delivery and cutover.

| Address on this Site | Visitor action and owner |
| --- | --- |
| `/#/library` | Browse the Asset Library. `q` and `system` in the fragment query preserve a search, e.g. `/#/library?q=adrenal`. |
| `/#/library/s1233-adrenal/r05` | Open the exact revision. Its package owns the bytes and its dated assessment owns the score. The library also offers the existing survey entries under `/#/library/<survey-id>` while their lineages are reconciled. |
| `/#/use-cases/adrenal-localization/region`, `…/right-gland` | Open the authored regional or isolated lesson stop. Each pins s1233 r05. |
| `/#/compare/adrenal-r04-r05` | Open the blind review. A shared comparison records `finish=tissue\|neutral` and `order=ab\|ba` in the fragment query. Both witnesses use the recorded camera. The findings and scores belong to the saved review. |
| `/#/stage/adrenal-v1?view=<encoded JSON>` | Restore a pinned scene recipe and exact export. Bare `/#/stage` opens the authored starting view and also accepts a local GLB. |
| `/rubric` | Stable public rubric address. GET or HEAD returns 302 to `/?view=1#/rubric`. The build reads the [canonical rubric](../../guideline/asset-quality.md). |
| `/#/archive/planning` | Open the dated survey with Overlaps selected and Gaps available. Discover it from **Use Cases → Experiments & Archive**. |
| `/?view=1#swirendo_fdi31`, `/#family-<id>` | Preserve the existing expanded family and its controls, including the verified Balanced download. |

## Data and file endpoints

| Request | Response and failure behavior |
| --- | --- |
| `GET /api/gallery/v1/studies` | Read-only JSON with schema version, authored lessons with ordered stop IDs, and saved reviews with their paired revision hashes. It currently lists one lesson and one review. HEAD has the same status and no body. Other methods return 405. The [study catalogue](../../sites/model-survey/app/src/content/gallery/catalog.js) supplies the API and the UI. |
| `GET /assets/index.json` | Site delivery declarations with filenames, sizes, media types and SHA-256 values. This is a file index. The Library's lineage, editorial review and lesson records provide different information. A declared route can precede upload. |
| `GET /assets/<sha256>/<name>` | Exact file bytes. HEAD, byte ranges, ETag and conditional reads follow the [asset handler](../../sites/model-survey/app/src/content/shared/r2-assets.js). An unknown route returns 404. A declared object with absent or mismatched storage metadata returns 503. The shared scene also checks byte length and SHA-256 before decoding. |
| `PUT /assets/<sha256>/<name>` | Existing guarded upload flow. Requires owner or time-limited upload authorization and checks the declared size and digest. [Storage policy](../../transport/README.md) |

The framework continues to own its existing snapshot, presentation and deployment endpoints. The immutable survey seed supplies legacy catalogue facts. The Site worker owns live delivery. The [read-only local preview](../../sites/model-survey/tools/preview_gallery.mjs) exercises the gallery reads against verified local bytes.

## Sharing and authorship

**Share this view** produces an immutable URL directly in the browser. Its version, revision, exact model hash, selected part, tissue or neutral material, key light, orthographic camera position, target and vertical field determine what reopens. The v1 recipe fixes model placement, background, secondary lights, projection and a 1200 × 960 WebP export. Keep this decoder and these defaults when adding a new version. Invalid or unavailable inputs have explicit recovery states. A local file can be inspected and exported. Sharing it as a gallery preset requires an addressable gallery revision.

The WebP export embeds the preset URL and renderer identity as XMP metadata. An export of a device-local model records its filename in place of a shareable URL. Reviewed Blender images retain their original evidence bindings. [WebP container and XMP](https://developers.google.com/speed/webp/docs/riff_container#metadata)

A visitor can share a view or the exact arrangement of a blind comparison without an account or server write. A maintainer chooses which preset a published record uses. Publishing a finding requires an authored review with inputs, evidence and attribution. A lesson author adopts an updated revision independently.

## Decisions for subsequent migrations

Add a study to the read API when it has an owned lesson or review. Extend the preset schema when a lesson needs new reproducible state, such as a cardiac phase and slice plane. A catalogue API for cross-client asset discovery is a separate design decision once the package-to-lineage reconciliation is ready. The present study API promises only the authored studies listed above.

For a local review, visit the Library and search for “adrenal”. Open r05, follow the lesson to the inferior rim and share its view from Stage. Open that link in a fresh browser session. Then open the Compare link, change the finish and share the comparison. Check that the part and camera survive the first handoff and the side assignment survives the second. The [browser journey](../../sites/model-survey/tools/verify_gallery.mjs) also exercises invalid presets, local GLBs, missing media, the rubric and legacy bookmarks.
