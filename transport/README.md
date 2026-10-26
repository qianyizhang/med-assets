# Bounded LFS transport

One reusable executor replaces per-batch workflow copies. It never commits pointers, pushes Git refs, merges PRs, changes settings, or fetches executable source code.

## Normal flow

1. Review an exact manifest and the asset/source/privacy/licensing scope. Save its **unchanged UTF-8 bytes** as `transport/manifests/<sha256-of-file>.json`.
2. Merge a **manifest-only PR adding exactly one file**. This explicitly authorizes that bounded batch. The main-only push trigger compares the event's before/after commits; edits, deletions, multiple files, or mixed code changes stop before any source download/upload. Do not combine executor changes with a transport batch.
3. The pinned main checkout verifies the manifest filename, file hash, committed bytes and fixed limits; downloads and validates **every** source before any upload; checks which OIDs are missing; uploads only those; then downloads every object from GitHub over fresh HTTPS, not the LFS cache.
4. Independently run the readback command below in another cloud executor with the reviewed main manifest. Preserve its sanitized receipt and the Actions run URL in the asset PR. Only then publish/merge matching asset pointers and review evidence.

This is not a new per-commit gate: unrelated commits and asset-pointer PRs do not trigger transfer. Ordinary PR branch hygiene can follow the user's periodic cadence. The implementation PR should contain these four files only; **no batch manifest** is bundled with it.

## Manifest shape

Use the existing transport format: top-level `objects`, `totalBytes`, optional `objectCount` and `scope`. Each object has `file` (raw identity/display path), `sha256`, `bytes`, and `url`. `file` is metadata only; temporary files are always named by checked OID, never that path.

- Identity transport: no transport-specific fields, optionally `"encoding":"identity"`.
- Gzip GLB: `"encoding":"gzip"`, `transportSha256`, and `transportBytes`. Both compressed bytes and bounded decoded bytes must match. The LFS OID is the **raw GLB** hash.
- GLB, WebP and PNG only. WebP bytes are checked independently of any PNG-derived URL basename.
- Only `https://anatomy-verification.landy123007.chatgpt.site/review/...`, the focused companion `https://anatomy-airway-review.landy123007.chatgpt.site/review/...`, the existing Assets site `https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/review/...`, the dedicated Dental site `https://anatomy-dental-review.landy123007.chatgpt.site/review/...`, and the focused Head/Neck site `https://anatomy-head-neck-review.landy123007.chatgpt.site/review/...` are allowed sources. No credentials, query strings, traversal, other hosts, or cross-origin redirects—even between allowed hosts. Same-origin redirects must still pass the source-path checks. Additional sources/formats require a separate small code review—not manifest-controlled allowlists. A host entry is not batch approval or proof of public availability; every manifest and source byte/hash check remains required.
- Fixed ceilings: 32 unique OIDs, 40,000,000 raw bytes and 40,000,000 transport bytes per batch, 40,000,000 bytes per object/transport, 128 KiB manifest. These are safety ceilings, **not standing approval to spend or upload arbitrary assets**. Each manifest still needs scope review.
- The 40,000,000-byte ceiling accommodates the reviewed muscle (30,517,312 bytes) and breast (37,499,672 bytes) exports in separate, explicitly approved bounded batches. It does not authorize those uploads by itself, change spending limits, or include source archives.

Content-addressed filenames are immutable identities. Fix a manifest by adding a newly reviewed hash-named file, not editing the old one. JSON is parsed strictly as data; duplicate/unknown fields and invalid types are rejected.

## Commands

```sh
# Offline validation; no network or Git writes:
python3 tools/lfs_transport.py validate --manifest-sha256 <64-lowercase-hex>
python3 -m unittest discover -s tests -p test_lfs_transport.py

# Read-only independent verification; no user token or LFS cache:
python3 tools/lfs_transport.py readback --manifest-sha256 <64-lowercase-hex>
```

An optional manual `workflow_dispatch` accepts only that manifest SHA and only runs on main. It can reverify/retry an already-reviewed manifest; missing-only upload avoids duplicate storage, but readback still consumes bandwidth. Current connected GitHub tools expose reads/reruns, **not dispatch**; the normal reviewed-merge push path avoids new credentials or API workarounds. GitHub also supports manual UI/CLI/REST dispatch with appropriate existing access: [official documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

## Security and failure boundaries

- No `pull_request` or `pull_request_target` upload trigger. Repository, event, main ref, checkout commit and manifest hash are checked again in Python.
- One serialized job, 10-minute timeout, pinned official checkout, `contents: write` only, existing ephemeral `GITHUB_TOKEN` authentication. No PAT, secrets, settings, or new permission request. [GitHub token documentation](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).
- Git LFS upload URLs are fixed to this repository with command-scoped overrides, including remote-specific overrides; no manifest-selected destination. [Git LFS configuration](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-config.adoc).
- Source/LFS response sizes and gzip output are bounded. URLs/headers from temporary LFS download actions and raw Git stderr are never logged. Cross-origin redirects are refused rather than forwarding authentication.
- A source 403/hash mismatch, unexpected destination response, permission failure or quota error stops the batch. Already-uploaded objects may remain if a later operation fails; do not claim success without complete readback. No automatic batch resubmission, alternate transport route or spending-limit adjustment.
- This does **not** query billing headroom or guarantee zero fees. Existing budgets/quotas still govern; check known allowance before approving a batch and stop for any new cost decision.
- Hash/format checks prove transport identity, not anatomy, visual quality, licensing, de-identification or recipe reproducibility. Those remain separately reviewed evidence.

## First execution

The first approved manifest-only merge completed successfully on 2026-10-24: [diaphragm transport run](https://github.com/qianyizhang/med-assets/actions/runs/40079101938/job/120828718881). All 10 objects / 6,620,120 bytes passed source verification, missing-only upload, runner readback and separate fresh GitHub download at 08:44:17 UTC. This establishes that bounded run only, not future source availability, billing headroom or anatomy/runtime acceptance. Offline tests remain distinct from live transfer evidence.

Historical executor provenance is retained as inert recipes and restoration evidence under `maintenance/archive/completed-branches/2026-10-24/`; this implementation has no dependency on deleted pilot branch refs.
