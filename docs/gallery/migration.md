# Migration to Anatomy Gallery

Move public med-assets experiences to the existing Site under the Anatomy Gallery name. The [campaign](../../records/campaigns/anatomy-gallery-consolidation.md) holds wave order and work items. The [census](existing-visualizations.md) records existing experiences and their owners. The [glossary](../../GLOSSARY.md#gallery-and-surfaces) defines the destination terms.

## Destinations

| Existing experience | Destination and first acceptance check |
| --- | --- |
| Model Survey | Evolve in place into **Asset Library**. Keep family bookmarks, the FDI31 entry, exact downloads and the dedicated rubric link. A visitor can find two adrenal lineages, choose a revision and see its rating or **Unrated**. |
| Anatomy Verification | Give substantive findings a page in **Compare**, including single-revision checks against source evidence. Carry the candidate selection and evidence order from old bookmarks. Bring teaching-only pages such as oral spaces into **Use Cases**. Represent ledger statuses faithfully, including rejected or incomplete work. The exact BodyParts3D adrenal review is the first handoff and returns to the selected Library family. |
| Body & Heart | The reference-frame-1 plate is in **Use Cases** alongside Cardiovascular in Body Systems. The studio and synchronized 3D interaction are deferred. Scoped marrow and pelvic reviews belong in Compare, with downloads from exact Library exports. |
| Head & Neck Review | Teach gland location and the supported duct course in **Use Cases**. State the unresolved crossing at the relevant view and link to the rejected reconstruction and its evidence in **Compare**. Link the exact glands and context exports in Library. This is the first complete legacy collection migration. |
| Airway Review | Give bronchial, tracheal and nasal studies revision-specific **Compare** pages. Add teaching views to respiratory Use Cases where they support the lesson. Preserve the distinction between trachea r05 and r06 and between the nasal airspace and its surrounding tissue. |
| Dental Review | Put the UFF specimen, dental tools and other public models in **Asset Library**. Give UFF extraction and FDI31 interface evidence separate **Compare** pages. Keep the verified inspector link from the UFF revision and Compare. The FDI31 control review sheet is in **Use Cases**. The authored specimen states and schematic posters are in **Experiments & Archive**, with links to the related existing films. The native inspector, layer editor and authored motion are deferred. |
| FDI31 Focus Review | Keep the existing retirement notice as a compatibility entry. Verify its links reach the exact Balanced specimen page and download after Library routing changes. The earlier interface study retains its own review identity. |
| Body Systems, One Breath and other local lessons | **Use Cases** and Respiratory lead to the original bilingual One Breath storyboard and its replay package. The phase controls are deferred. Fold arch identification, static locators and route diagrams into relevant teaching stops. Adrenal’s blind A/B study belongs in Compare. |
| Small collections, local prototypes and generated reports | Merge useful stops into a maintained use case. Collect distinct retained public experiments, such as a kidney locator trial or dental film treatment, in **Use Cases → Experiments & Archive**, with date, source and limitation. Omit duplicate shells, authoring harnesses and disposable renders from public navigation. Keep unique evidence with its package. The ordinary Site carries the retired adrenal pilot's three bookmarks. [Routes](routes-and-api.md#page-links) |

## Delivery order

Follow the [campaign waves](../../records/campaigns/anatomy-gallery-consolidation.md#work). For each collection, reconcile its package records, scene inputs, lesson exports, catalogue entries and delivery index before cutover. Every public scene object must resolve to its exact Library revision or parent export. Collection work can proceed while inventory and ratings for other collections remain open.

During Wave 2, reuse the current exports, shots and controls wherever they already support the visitor’s task. Move them to their maintaining package, update Gallery consumers and remove superseded shells or copies in the same migration. Keep the Gallery build and its visitor journeys working after each move. If a move breaks a dependency used only by a legacy site, record the affected view and defer repair until the walkthrough decides whether to rebuild or prune it. Avoid adding compatibility shims solely to keep those sites building. Record the result against each collection in [AG-GAL-013](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md). If the task needs new evidence, a reshoot or a rebuilt interaction, record the gap for the [end-of-migration walkthrough](../../records/campaigns/anatomy-gallery-consolidation.md#between-waves-2-and-3--feel-the-vibe). Use the agreed direction to scope any Wave 3 rework. Keep the dated census as the baseline.

For the repository-wide inventory, count lineages and revisions separately from file paths. At `22eb216` the tracked baseline included 146 GLB paths plus STL, OBJ and Blender files. Give public assets a discoverable Library disposition, including historical and metadata-only entries. Map duplicate bytes to aliases. Make missing public exports visible as unavailable. Record the owner and reason for excluding source inputs, restricted files and internal fixtures.

Test each specialist interaction before retiring its corresponding viewer. Leave public cutovers until after the local walkthrough. At cutover, check the interactions selected for retention and the published addresses that still have consumers. If the synchronized Body & Heart journey is selected for rework, reopen the 3D model at reference frame 1 and its matching slice plane. The retained volumes represent that single frame. [Imaging source and coordinate convention](../../heart/synthetic-imaging/beating-heart/imaging/README.md)

## Page addresses and file addresses

A page address opens an experience. A file address returns the bytes for a particular model or piece of evidence. For example, the [Head & Neck manifest](../../transport/manifests/7b3860f7d29b8cf4e19190dee4bf7499bbe69e9924c7057021460edc4239fe53.json) lists two GLBs and seven WebPs. The gland model entry identifies its original URL, repository path, 129,736 bytes and SHA-256 beginning `a53134ec`. Sending that request to an HTML retirement notice would break the download.

The following static comparison uses the manifests and index at `22eb216`. To repeat it on a current checkout, group unique object URLs in the [transport manifests](../../transport/manifests/) by host and match each object's canonical `sha256` and `bytes` to an entry in the [Site delivery index](../../sites/anatomy-gallery/app/src/content/assets/delivery-index.json). A match identifies a recorded copy. Check live responses separately at cutover.

| Legacy host | Distinct file URLs in manifests | Matched in Site index |
| --- | ---: | ---: |
| Head & Neck Review | 9 | 9 |
| Airway Review | 13 | 13 |
| Dental Review | 28 | 24 |
| Anatomy Verification | 120 | 120 |
| Body & Heart | 19 | 19 |

The four Dental entries unmatched at the baseline were the [mouth-mirror GLB and three PNGs](../../transport/manifests/96dfb7956224d3331b0a095f26e4d89f34e8d7a4c6054f8b52bc826b041dda45.json). The [collection readback](../../records/work-items/items/AG-GAL-015-verify-static-reviews.md#2026-11-22-collection-checks) verified all four original URLs against their pins. The preview can recover these files from legacy delivery or its local cache. Their original delivery paths still have consumers.

For published URLs with known consumers, record the destination and verify the migration, including any required fragment. Retire internal beta aliases and their entries when their readers move. Record expected media type and byte identity for files. New gallery pages load live 3D models from the Site’s hash-addressed R2 URLs. Serve migrated display images as WebP and keep original bytes at evidence addresses used by active readers. For compressed transport entries, check the recorded transport and decoded identities. [Display images](design.md#display-images) · [Delivery and backup](../../transport/README.md) · [Beta retention](../WORKFLOW.md#retention)

The [guarded LFS transport](../../transport/tools/lfs_transport.py) reads digest-pinned manifests and refuses cross-origin redirects. For a legacy file URL used by that path, keep a compatible exact-byte response on the original host, or migrate the consumer through its own reviewed contract and verify it before retirement. Retain manifests that still drive a download, recovery or integrity check. A page redirect to the new Site can coexist with continued file delivery at the old paths.

A collection migration can close once its visitor experience runs on Anatomy Gallery and its old bookmarks and required file addresses have tested dispositions. Publish page redirects or notices only after testing the new journeys and old fragments. A compatibility-only host can continue serving exact files. A later shutdown requires its own decision, tracked for Head & Neck in [AG-GAL-008](../../records/work-items/items/AG-GAL-008-retire-head-and-neck-host.md).

The [Head & Neck and Airway rehearsal](../../records/work-items/items/AG-GAL-013-reconcile-gallery-coverage.md#2026-11-22-joint-release-rehearsal) tests an explicit Gallery link on the original HTML and a notice on the exact missing bronchial r13 path. The link can resolve a browser fragment while the original content stays available. Route rules should match the named HTML paths exactly. Keep the previous page and file mappings ready to restore independently, and verify the original pinned file response after each rollback.
