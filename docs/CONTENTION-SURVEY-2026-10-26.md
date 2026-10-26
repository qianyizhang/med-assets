# Repository contention survey — 2026-10-26

Snapshot: main [`6fd567d`](https://github.com/qianyizhang/med-assets/commit/6fd567df1a425157d070d695fc84275a8673ba60), including merged PR87. The Oct 22–26 history contains 188 commits, 98 excluding merges, and 1,897 paths; only 15 paths appear in more than one non-merge commit. Counts below include creation. Rename-aware history, semantic diff sections and original PR heads distinguish contention from initial imports, line drift and two exact workflow-to-archive renames. All 671 LFS-managed files remained pointers; no media download was needed.

| Surface / measured changes | Evidence and classification | Response |
|---|---|---|
| `docs/SCOPED-STUDIES.md`: **15 commits** | Independent PR82/85/87 insertions share the supplement/section boundary; their original heads overlap only in this file. **Reproduced accidental conflicts.** Earlier 34→35→36 migration accounting was intentional; later supplements explicitly add zero to that count. | Preserve the overview and use existing study directories for new entries. This is the implemented slice in [PR89](https://github.com/qianyizhang/med-assets/pull/89). |
| `tools/lfs_transport.py`, `tests/test_lfs_transport.py`: **6 each**; `transport/README.md`: **8** | Repeated sections concern `SOURCE_HOSTS`, exact-host tests and ceilings: [PR37](https://github.com/qianyizhang/med-assets/pull/37), [PR62](https://github.com/qianyizhang/med-assets/pull/62), [PR72](https://github.com/qianyizhang/med-assets/pull/72), [PR77](https://github.com/qianyizhang/med-assets/pull/77), [PR83](https://github.com/qianyizhang/med-assets/pull/83). **Intentional policy synchronization**, not an observed merge conflict. | Keep separately reviewed policy changes and matching tests/documentation. Do not move trusted policy into batch-controlled metadata. |
| `transport/manifests/`: **24 files, each added once** | Content-addressed additions already compose. The [workflow](https://github.com/qianyizhang/med-assets/blob/6fd567df1a425157d070d695fc84275a8673ba60/.github/workflows/bounded-lfs-transport.yml) serializes execution; the executor accepts one manifest-only addition on main. **Intentional publication boundary.** | Preserve trusted code, fixed HTTPS hosts, 32-object/40 MB caps, redirects, exact source/hash checks and independent LFS readback before publishing pointers. |
| Dental `pilot-ingestion.md` and SwirEndo `source-map.json`: **2 each** | Initial pilot followed by [PR76](https://github.com/qianyizhang/med-assets/pull/76) validation of the same specimens. The 52-tooth inventory was added once; UFF uses separate source files. **Intentional source/status coordination; insufficient evidence of cross-study contention.** | Retain canonical identities and review semantics. Independent PR76/79 and PR76/80 pairs merge cleanly; no speculative inventory split. |
| `SHA256SUMS`, `metadata/asset-manifest.json`, `metadata/earlier-collection.json`: **2 each**; baseline ledger: **1** | Initial import/provenance records explain the large line counts. **Historical evidence and shared import contracts**, not recurring generated-index writes. | Preserve checksums, archive/member mappings and negative reviews. New studies already have separate records. |
| Root README: **3**; Firefox workflow, head/abdomen SVGs and tongue README: **2 each** | Mostly creation plus one targeted change. **Insufficient conflict evidence**; the workflow's main-only restriction is intentional. | Add stable root navigation for the selected fix; retain artwork, recipes and workflow restrictions. |

## Reproduction and selected fix

These original-head comparisons both report a content conflict only in `docs/SCOPED-STUDIES.md`:

```sh
git merge-tree --write-tree --name-only aab0b1f 9cc4f99
git merge-tree --write-tree --name-only 24688e8 82efc8e
```

Reconciliations [`8088d4e`](https://github.com/qianyizhang/med-assets/commit/8088d4ea67725881fbc7b323c73683226649f8ad) and [`ff5172b`](https://github.com/qianyizhang/med-assets/commit/ff5172bcd989eb3b89c3433fadfcb47f58085c77) show the preserved union. Comparisons `bd78af1`/`3e3cfa9` (PR76/79) and `bd78af1`/`9775071` (PR76/80) return clean merges with no shared changed paths. Repeated edits alone therefore are not the verdict.

Repository reference/CI inspection found no generator or consumer parsing the overview table; the root README links it for readers. Existing run/revision READMEs already own scope and evidence. Stable directory links remove the shared edit without new metadata. Per-study entries plus generated discovery would add a build dependency here; committing its generated aggregate would recreate contention. A separate UI consumer may justify a small projection later.

Future batches follow [study discovery](ASSET_LAYOUT.md#study-discovery): add their own README with artifact, record, evidence, source/licence and replay links. Retain previous revisions. No global row or bounded-count update is required.

## Process and bounded follow-ups

An optional host-policy PR, a manifest PR and an asset-pointer PR protect different boundaries. Compatible, frozen groups can already share a reviewed batch: [PR81](https://github.com/qianyizhang/med-assets/pull/81) transported 17 objects / 12,213,466 bytes for two groups; [PR82](https://github.com/qianyizhang/med-assets/pull/82) retained their separate provenance and limits. This can reduce serial work within existing caps. It does not permit combining policy code with manifests or skipping readback.

- **Game gallery:** [PR19](https://github.com/qianyizhang/game/pull/19/files) and [PR20](https://github.com/qianyizhang/game/pull/20/files) overlap in exporter evidence/CSS bindings, `ReviewGallery.tsx` props/intro and changelog insertion. These inspected hunks show composition coupling; no game merge conflict was reproduced here. Keep study components separate and check the union of accepted study IDs/anchors before publication, alongside existing image, 600 KiB, offline and unchanged-save checks. No game changes are included.
- **Region adapter:** canonical [regions.json](../body/2d-v4/whole-body-anatomy-v4-spatial/regions.json) resolves 21 unique region IDs to `regions/*.svg`. A legacy viewer's flat `body.svg`/`head.svg` cache is a different contract. Check every published reference against that cache, preserve selector IDs, and permit only approved viewBox changes. This is an adapter invariant, not evidence for a repository-wide rewrite.
- **Contextual study discovery:** newer limited studies need links from the selected organ while retaining its failed-baseline evidence. The sampled [salivary](../reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json) and [urethral](../reviews/urethra_male/2026-10-26-native-context-r01/decision.json) decisions bind artifacts and scope but have no explicit UI asset ID/public review-page URL. First reuse a reliable existing hash/catalog join; otherwise consider only `baselineUiAssetId` and `publicReviewUrl` in study-owned metadata. Derive the inspector mapping without duplicating gates, hashes or provenance. Test spinal cord, salivary and urethral selection, retained baseline links, reachable study pages, unchanged count/status claims and an unrelated organ. Site implementation remains separate.

## Verification and limits

The one-time before/after comparison against `6fd567d` retained 36 rows, all 91 existing links/headings and all 55 linked text files (37 JSON records and 18 Markdown files) byte-for-byte. That is refactor evidence, not a permanent aggregate digest: a model README clarification must not require an unrelated central test edit.

The [existing contract](REVIEW_CONTRACT.md) protects immutable review identities and exact artifact/evidence bindings; the [layout](ASSET_LAYOUT.md) preserves raw sources, licences and historical reviews. It does not freeze every model or diagram README. Existing record validators and per-study integrity checks remain unchanged. Navigation tests check linked destinations, leaving contract fields and payload hashes to their owners.

Only the explicitly historical overview retains a snapshot digest: its fixed migration set and recorded summaries must not silently change when new studies are added. A deliberate correction to that snapshot needs review. Five navigation tests cover this invariant, link/fragment resolution, two independently committed study additions, and a real linked model-README clarification that passes the historical checks with the test file unchanged.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'                 # 36 passed
python3 -m unittest discover -s tests/review_records -p 'test_*.py'  # 8 passed
python3 docs/dental-atlas/validate_inventory.py                    # passed
git diff --check                                                  # passed
```

No generator was introduced, so equivalence replaces a regeneration check. Public URLs, status boundaries, source/licence records, historical failures and transport gates are retained. These checks establish documentation and Git composition, not new media, anatomy, clinical or runtime approval. Independent repository additions are the goal; no formal runtime lock-free guarantee is claimed.
