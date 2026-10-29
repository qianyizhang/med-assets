# Asset delivery: direct LFS first

```text
Reviewed bytes → direct Git LFS upload → fresh GitHub readback → asset-pointer PR
                      │ unresolved technical failure
                      └→ authorized Drive/Site source → bounded CI upload → readback
Drive backup: retain the same verified bytes; not a replacement for repository delivery.
```

## Normal flow

- Check the **current executor**, repository remote and existing authentication;
  connector access does not imply shell access. Try the exact authorized, bounded
  object upload (for example, `git lfs push --object-id origin <reviewed-oid>`),
  not a broad ref push. An old environment failure is not a permanent limitation.
- Record timestamp, executor context, command, exit status and sanitized result.
  Distinguish missing authentication, network failure, quota and action denial;
  do not guess the cause or expose tokens, signed URLs or private billing data.
- Verify size and SHA-256 from a **fresh GitHub download / empty LFS store** before
  opening the matching asset-pointer PR. Preserve the receipt and exact artifact
  identity. Upload success alone is not repository delivery or asset approval.
- Keep a verified backup in the owner's authorized Drive destination. Use Drive
  or a Site as a source fallback only when direct transport fails and its technical
  cause remains unresolved; do not build a staging detour when direct upload works.
- Fallback needs the same byte/hash checks and existing source/publication permissions.
  Do not change sharing, add credentials, widen allowlists or bypass an access/action
  denial. The current CI executor accepts only the Site sources listed below:
  **Drive support is not implied**; any production support needs separate code review.
  Known permission, quota or integrity failures must be resolved, not routed around.

## Bounded CI fallback

One reusable executor replaces per-batch workflow copies. It never commits pointers, pushes Git refs, merges PRs, changes settings, or fetches executable source code.

## CI fallback flow

1. Review an exact manifest and the asset/source/privacy/licensing scope. Save its **unchanged UTF-8 bytes** as `transport/manifests/<sha256-of-file>.json`.
2. Merge a **manifest-only PR adding exactly one file**. This explicitly authorizes that bounded batch. The main-only push trigger compares the event's before/after commits; edits, deletions, multiple files, or mixed code changes stop before any source download/upload. Do not combine executor changes with a transport batch.
3. The pinned main checkout verifies the manifest filename, file hash, committed bytes and fixed limits; downloads and validates **every** source before any upload; checks which OIDs are missing; uploads only those; then downloads every object from GitHub over fresh HTTPS, not the LFS cache.
4. Independently run the readback command below in another cloud executor with the reviewed main manifest. Preserve its sanitized receipt and the Actions run URL in the asset PR. Only then publish/merge matching asset pointers and review evidence.

This is not a new per-commit gate: unrelated commits and asset-pointer PRs do not trigger transfer. Ordinary PR branch hygiene can follow the user's periodic cadence. The implementation PR should contain these four files only; **no batch manifest** is bundled with it.

## Authorized transport PR merges

An assistant may complete a routine transport merge within the owner's existing authorization; this is not authority to merge arbitrary changes or approve an asset candidate. Use the connected GitHub tools, with no new credentials:

1. Confirm the exact PR is manifest-only, its reviewed batch is authorized, and its full head SHA matches the reviewed changes. Check required reviews, CI and branch rules; `mergeable=true` alone is not sufficient.
2. If draft, use `mark_pull_request_ready_for_review`; draft PRs cannot merge. Re-read the PR after the transition.
3. Use `merge_pull_request` with `expected_head_sha` set to the reviewed full SHA and a repository-allowed merge method. If the head changed, stop and review the new changes rather than silently accepting them. Preserve all required checks and protections.
4. Verify the merged state and merge commit, then the upload workflow result and independent fresh LFS readback described above. A successful merge is not proof of successful transport. Record the run URL and sanitized receipt.

GitHub repository write permission and approval to execute a particular action are separate. An action-approval denial before execution is not a GitHub permission or CI failure. Stop the denied action; do not retry through CLI, browser, another agent or token, weaken protections, or obtain broader credentials to bypass it. If the exact transition is genuinely outside the existing authorization, request only that specific scope. If adequate authorization already exists but the action remains blocked, report the unresolved block through the supported feedback/handoff path rather than repeatedly asking for the same permission. Knowing this workflow does not mean an approval block has been removed.

Auto-merge is an optional supported feature when the repository permits it and required reviews/checks remain pending. The connected wrapper does not expose an expected-head guard; prefer the guarded immediate merge for a frozen reviewed manifest. Auto-merge is not a workaround for a denied action.

Transport authorization covers the reviewed upload only. Keep separate candidate anatomy, visual-quality, clinical and runtime approval unchanged; a draft candidate remains draft unless separately authorized.

**Recorded example:** the owner merged [PR78](https://github.com/qianyizhang/med-assets/pull/78) on 2026-10-26. This was not an assistant workaround for the earlier blocked ready transition and does not establish that future action approval will succeed.

References: [draft/ready transitions](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/changing-the-stage-of-a-pull-request), [merge requirements](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request), [merge API SHA guard](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request), [auto-merge](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/automatically-merging-a-pull-request).

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
- A source 403/hash mismatch, unexpected destination response, permission failure or quota error stops the batch. Already-uploaded objects may remain if a later operation fails; do not claim success without complete readback. No automatic batch resubmission or spending-limit adjustment. Source fallback follows the preferred-route conditions above; it is never a workaround for a denied action or known permission/quota/integrity failure.
- This does **not** query billing headroom or guarantee zero fees. Existing budgets/quotas still govern; check known allowance before approving a batch and stop for any new cost decision.
- Hash/format checks prove transport identity, not anatomy, visual quality, licensing, de-identification or recipe reproducibility. Those remain separately reviewed evidence.

## First execution

The first approved manifest-only merge completed successfully on 2026-10-24: [diaphragm transport run](https://github.com/qianyizhang/med-assets/actions/runs/40079101938/job/120828718881). All 10 objects / 6,620,120 bytes passed source verification, missing-only upload, runner readback and separate fresh GitHub download at 08:44:17 UTC. This establishes that bounded run only, not future source availability, billing headroom or anatomy/runtime acceptance. Offline tests remain distinct from live transfer evidence.

Historical executor provenance is retained in the recovery bundle and restoration
evidence under `maintenance/archive/completed-branches/2026-10-24/`; this
implementation has no dependency on deleted pilot branch refs or extracted copies.
