---
description: Determine when the compatibility-only Head & Neck host can be shut down safely.
scope: backlog item
status: stable
last_update: 2026-11-22
document_class: work_record
work_id: AG-GAL-008
work_status: deferred
work_kind: decision
added: 2026-11-20
tags: transport, gallery
depends_on: AG-GAL-003
residual_of: none
residual_items: none
---

# AG-GAL-008 — Evaluate full Head & Neck host shutdown

## Intent

Decide whether the legacy Head & Neck host can stop serving traffic after its visitor experience moves to Anatomy Gallery.

## Acceptance Criteria

- [ ] Trace consumers of the nine original file addresses and page bookmarks, including guarded LFS transport and pinned historical links. Record their verified replacements or explicit retirement decisions.
- [ ] Prove that required file routes still return the expected media and exact bytes, or that their consumers have passed a reviewed migration. Test bookmarks and fragments with the intended final routing.
- [ ] Record a shutdown decision with evidence, remaining obligations and rollback or recovery. If dependencies remain, keep compatibility delivery and document what would reopen the decision. Execute any shutdown through separate authorized work.

## Context and Trade-offs

The [Head & Neck migration](AG-GAL-003-migrate-head-and-neck.md) can complete with the host in compatibility-only service. The [guarded transport contract](../../../docs/gallery/migration.md#page-addresses-and-file-addresses) refuses cross-origin redirects. The [Head & Neck manifest](../../../transport/manifests/7b3860f7d29b8cf4e19190dee4bf7499bbe69e9924c7057021460edc4239fe53.json) preserves the original addresses.

## Status History

| Date | Actor | From | To | Reason / evidence |
| --- | --- | --- | --- | --- |
| 2026-11-20 | Maintainer and Codex | — | deferred | Captured the accepted separate host shutdown decision |

## Implementation Ledger

### 2026-11-22 file-service rehearsal

**No-go for host shutdown.** The Head & Neck review's `/page.js` reads `/data.json`, which pins links to all nine model and evidence files by URL, size and SHA-256. Those links and the [review decision](../../../reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json) agree with the digest-pinned [transport manifest](../../../transport/manifests/7b3860f7d29b8cf4e19190dee4bf7499bbe69e9924c7057021460edc4239fe53.json). The guarded LFS downloader can still select that manifest. The Gallery binds the same identities to nine hash-addressed responses and uses them in its lesson, Compare and Library. Keep the changelog, language and display controls, and the original record, license and evidence links with the old review.

The local stand-in served all nine complete original bodies and the preview served all nine exact Gallery bodies. The real guarded manifest loader and downloader's transport-size, digest and file-format checks passed with the network read pointed at the stand-in. The hosted GETs on 2026-11-22 returned 200 and matched all nine on each host. Recorded media types were `image/webp` for the witnesses, `application/octet-stream` for the legacy GLBs and `model/gltf-binary` for the Gallery GLBs. These manifests pin identity transport. Both legacy GLBs supported HEAD and answered range requests with complete 200 responses. The guarded consumer uses a full GET. The Gallery reported exact 206 ranges.

#### Rollback

1. Before any public handoff, capture the currently served legacy deployment, asset routing and backing store, including `/style.css`, `/page.js`, `/data.json` and the changelog. Keep the previous Gallery HTML, Worker, snapshot and presentation bindings with the deployment record.
2. To revert the Head & Neck handoff, restore its original `/` and `/review/salivary-native-r02/` pages. Open the review at `#changelog` and `#downloads` and follow an original download. The stand-in restored both original HTML byte sequences and rechecked every scoped file at its old URL.
3. If backing delivery changes or fails, restore the previous origin file mapping and exact object at the **original URL** from the retained deployment or the matching verified canonical LFS export. Run a full GET with identity encoding and redirect following disabled. Check HTTP 200, media type, byte count and SHA-256 against the manifest, then run the guarded download checks and reopen the old consumer. The rehearsal served the gland GLB from a second backing source at the same path, then injected a cross-origin redirect and a 503. The redirect guard refused the redirect. Restoring the original backing passed the full check again.

Reopen the shutdown decision after reviewed migrations or explicit retirement of each pinned consumer, and after evidence shows how every retained legacy bookmark and function will work. The [joint receipt](AG-GAL-013-reconcile-gallery-coverage.md#2026-11-22-joint-release-rehearsal) owns hosted acceptance of the page handoff.


### Hosted rollback point

The owner-held public v1 source matched both active page bodies after removing the platform script. Static routing served the same root HTML for `/` and `/review/salivary-native-r02/`. The dedicated owner-only copy preserved the original static layout in its rollback version. Its handoff adds an explicit review index and retains the legacy file handlers. Both versions returned all nine exact files. The hosted rollback restored both original page bodies and all nine pins while Airway and Gallery stayed available. Keep the original deployment, static source and consumer pins available. [Deployment and release evidence](AG-GAL-013-reconcile-gallery-coverage.md#legacy-host-release-rehearsal)
