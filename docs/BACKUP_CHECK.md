# Current mirror planning and offline byte checks

`tools/backup_check.py` inventories **one exact committed tree** and produces a
dry-run incremental plan for one current mirror and one small current-state
manifest. It also checks actual local files or ZIP members against SHA-256 and
size. LFS pointers do not count as retained media. It prints JSON to stdout and
never transfers files, writes a manifest, replaces or deletes objects, downloads,
extracts ZIPs, schedules work or changes Git configuration. It contains no remote
writer, log history or snapshot builder. No Drive credentials, network service
or Python packages are needed. Requirements: Python 3.11+,
[Git 2.45+](https://git-scm.com/docs/git/2.45.0) (`--no-lazy-fetch`) and Linux
(`dir_fd` / `O_NOFOLLOW`). Git LFS itself is not needed.

## One current-state manifest

Keep this operational manifest outside the public checkout. Its exact root
fields are `schemaVersion: 1`, nonnegative integer `revision`, `commit` (the full
commit of the current mapping, or `null` when `files` is empty), `files` and
`staged`. There are no snapshots, segments, predecessors or retained payload
versions. A bootstrap manifest can be:

```json
{"schemaVersion":1,"revision":0,"commit":null,"files":[],"staged":[]}
```

Every record in `files` has exactly these fields:

| Field | Contract |
| --- | --- |
| `path` | Exact safe relative path in the current mapping. |
| `sha256`, `size` | Expected payload SHA-256 and nonnegative integer byte size. |
| `remote` | Exactly `fileId`, `version`, `sha256`, `size`. IDs/version tokens are explicit opaque identities. A version may be `null` for explicit exclusive-writer evidence or unverified data. Remote size records the object's bytes. |
| `verification` | Exactly `status`, `method`, `at`. `verified` or `failed` uses `sha256-size-readback` with a real version, or `exclusive-writer-sha256-size-readback` with a null version, and an exact UTC timestamp. `unverified` uses `none` and `null`. A verified record must match expected SHA-256 and size. |

`staged` records have the same fields plus `forCommit`, an exact source commit.
They describe temporary or interrupted work separately from the accepted current
mapping. Even a verified staged object is not automatically adopted. Unverified
current entries remain verification candidates. Duplicate paths in either array,
unknown fields, conflicting byte sizes, conflicting identities/versions for one
remote ID, and an ID appearing as both current and staged are rejected. The same
remote ID may serve several paths only when its content and evidence agree.
The manifest is limited to 16 MiB. Symlink/nonregular manifest files are refused.

Set `expected_digest` to the SHA-256 retained for the selected manifest revision,
and `commit` to the full selected Git commit. Commands are templates:

```sh
python3 tools/backup_check.py --validate-manifest /path/to/current-manifest.json \
  --expected-manifest-sha256 "$expected_digest"
python3 tools/backup_check.py --commit "$commit" \
  --plan-manifest /path/to/current-manifest.json \
  --expected-manifest-sha256 "$expected_digest" > /tmp/incremental-plan.json
```

The required digest rejects a stale or changed **local** manifest checkpoint.
It does not discover the latest remote manifest or authenticate an arbitrary
checkpoint. A digest computed from an outdated download remains outdated. It is
**not atomic remote compare-and-swap**. No such connector capability is asserted.
Without an explicit exclusive-writer agreement, a writer needs supported revision
or precondition controls and must otherwise stop. The serialized adapter below
instead relies on an accepted exclusive-writer guarantee, checks actual checkpoint
bytes, and never labels that guarantee atomic CAS or last-writer-wins.

## Incremental plan and storage estimates

Planning groups expected files by exact SHA-256 and size while retaining every
current commit/path mapping. Repeated paths with identical bytes need one payload.
These actions are proposals, never proof of current remote availability:

| Action | Meaning |
| --- | --- |
| `reuse_candidate` | A historically verified current object matches the bytes. Check existence, version and checksum; read back bytes when metadata does not establish identity. Old verification times do not prove freshness. |
| `verify_candidate` | Matching unverified current data or staged data needs remote validation/readback and explicit adoption before reuse. |
| `upload` | No eligible matching object is listed. Transfer only this new/changed unique payload in a separately authorized execution. |

Failed or mismatched objects cannot suppress a planned upload. A plan can reuse
identical content across renamed paths. `replacementCandidates` and
`obsoleteCandidates` report path/mapping changes; they are **not remote deletion
instructions**. An obsolete path's remote ID may still serve desired content.
`stagedReviewCandidates` preserves interrupted work for review without promoting
it or automatically cleaning it up.

`budget` reports exact deduplicated upload counts/bytes under the stated candidate
assumptions, listed current/staged physical bytes (counting a shared ID once),
desired unique payload bytes and largest payload size. If candidates fail live
checks, `uploadBytesIfAllCandidatesFail` gives the full-content contingency.
`additionalStagingPeakBytesIfCandidatesFail` bounds one replacement in that case.
These estimates cover only manifest-listed objects; unlisted archives, partial
snapshot parts, other Drive files and quota are outside the model.

`additionalStagingPeakBytes` is the largest planned upload: the proposal stages
**one changed file at a time**. `temporaryStagingPeakBytes` includes already-listed
staged objects. `initialStepTotalPeakBytes` also includes the listed current
mirror. This is an initial-step estimate, not a full-run peak: accepted new files
change the footprint. A future executor must recalculate after each accepted
file and pause before unresolved replacement/removal. It should verify source
and uploaded bytes, obtain applicable replacement/removal permission, and resolve
the previous copy before continuing. The intended final state is one latest
mirror, without accumulating snapshots or old payload versions.

Individual file sizes, rather than the sum of the collection, determine transfer
needs. In the selected public tree examined for this proposal, the largest file
is **42,497,262 bytes**, below the observed 100 MiB connector limit. A file-level
executor therefore needs no ZIP chunk workaround for that tree. The planner
reports the actual `largestPayloadBytes` for each selected revision; it imposes
no unverified provider-capability assumptions.

Manifest validation and plan exit code **0** mean valid local metadata/a valid
dry-run plan, even when uploads are needed. `remoteCoverageVerified`,
`remoteManifestFreshnessChecked` and `atomicRemoteCAS` remain false. Missing or
stale expected digests and invalid manifests exit **2**. No metadata-only mode
reports `completeCurrentTree`.

## Inventory and actual local byte checks

Resolve the intended revision first, then pass its full commit ID explicitly:

```sh
commit=$(git rev-parse HEAD)
python3 tools/backup_check.py --commit "$commit" --inventory > /tmp/expected-tree.json
python3 tools/backup_check.py --commit "$commit" \
  --backup-tree /path/to/local-downloaded-snapshot > /tmp/backup-check.json
# Alternatively, a local ZIP whose member paths start at the repository root:
python3 tools/backup_check.py --commit "$commit" \
  --backup-zip /path/to/local-snapshot.zip > /tmp/backup-check.json
```

Use a stable, fully downloaded local snapshot. A mounted provider that fetches
files on demand can itself cause network reads; this tool cannot control that
provider. A ZIP with a wrapper directory must be prepared separately; the tool
never guesses roots, renames paths or accepts a metadata-only inventory as proof.
Keep reports outside the checkout: they may contain private operational paths
or names, and are not intended for Git commits. Shell redirection overwrites an
existing report; choose a fresh report path when preserving prior evidence.

`--inventory` exports every tracked regular file's exact expected path, SHA-256,
size and kind (`git` or `lfs`), with the resolved commit and unique-object totals.
Git files are hashed directly from committed blobs. LFS identity and size come
from committed pointers, checked against that commit's attributes. Dirty working
files and staged changes are excluded. Every Git command uses the explicit
`--no-lazy-fetch` option and denies all transport protocols with
`GIT_ALLOW_PROTOCOL=''`. Older Git versions that lack the option fail before
reading repository objects; the tool never retries without it. This avoids
relying on an environment variable that older Git may ignore. Missing Git objects
fail without lazy fetching. Local `info/attributes` overrides are refused because
they could change the interpretation of the committed tree. No backup has been
verified by exporting an inventory alone.

Check results contain one status per expected path:

| Status | Meaning |
| --- | --- |
| `verified` | Actual local bytes match both expected SHA-256 and size. |
| `missing` | The expected path is absent. |
| `mismatched` | Size or SHA-256 differs, including truncated/corrupt content. |
| `pointer_only` | An LFS pointer was retained instead of its media payload. |
| `unverifiable` | Cannot safely read the payload, e.g. symlink, nonregular file, permission failure, encrypted member or bad ZIP CRC. |

Every gap receives `action: "needs_copy"`; `plannedCopyBytes` sums expected bytes
at those paths, counting repeated paths separately. This is a **plan only**. It
does not establish that a good source copy is locally available or authorize
replacing the target. Preserve questionable existing files and obtain exact
verified source bytes before a separate transfer. Rerun the check on the resulting
downloaded snapshot to verify it. Extra backup files are ignored and never deleted.

Byte-check exit codes: **0** = all expected contents verified (or inventory exported),
**1** = backup has gaps, **2** = invalid input or inventory/check failure.
Only check mode can return `completeCurrentTree: true`; inspect that field as well
as the exit code. Unsafe or duplicate ZIP paths fail the entire check. ZIPs are
read in place, never extracted; member reads are bounded by expected sizes.

## Scope and older source archives

`completeCurrentTree` means byte coverage of this one committed tree at exact
repository paths. It does **not** establish full Git history, a Git clone, other
branches, untracked/private masters, external assets, executable permissions,
licensing/clinical review, Drive upload success, remote availability or restore
testing. Symlinks and submodules in the Git tree are unsupported and fail closed.

The historical `SHA256SUMS` and `metadata/asset-manifest.json` describe the initial
591-member import, not today's full tree. Preserve them unchanged. Original source
ZIPs use different member paths: this checker does not map those archives through
the import manifest or search their members by hash. Checking an old source ZIP
directly therefore reports exact-path gaps; it cannot decide whether differently
named members retain equivalent bytes. Such archives require a separate member
SHA-256/size audit and path mapping. Source archives and opaque split-archive
parts are not individual-file current-mirror records; do not promote an unfinished
archive transfer into verified per-file evidence. A matching archive filename,
timestamp, saved checksum or ZIP CRC alone does not establish current-tree coverage.

Focused tests: `python3 -m unittest discover -s tests -p test_backup_check.py`.
The normal `python3 tools/verify.py offline` command discovers these tests too.
Screenshots are not applicable to this command-line, nonvisual change.

## Serialized exclusive-writer connector workflow

`tools/backup_transfer.py` keeps the checker read-only and supplies a serialized
request/response workflow for the existing connector. The Python module never
invokes a connector or makes network requests; an authorized host executes the
returned requests and passes back observed results/bytes. Tests use synthetic
Git objects and an in-memory Drive fixture. There is no deletion, sharing or
credential implementation, and no automatic cleanup.

```sh
python3 tools/backup_transfer.py --capabilities
python3 tools/backup_transfer.py --capabilities --exclusive-writer
# Local staging only; all values below are caller-selected operational inputs:
python3 tools/backup_transfer.py --commit "$commit" --path "$tracked_path" \
  --manifest "$manifest_path" --expected-manifest-sha256 "$expected_digest" \
  --work "$one_job_directory" --folder-id "$destination_folder_id" --max-bytes "$one_file_budget" \
  --exclusive-writer
```

Only a file classified for upload by the existing planner can be prepared.
Normal Git bytes come from the exact commit; LFS payload bytes must match its
pointer SHA-256 and size. The explicit per-file budget cannot exceed the observed
100 MiB connector limit. Untracked paths, stale manifest checkpoints, unresolved
staged objects, symlink job directories and mismatched source bytes fail closed.
Preparation retains `prepared.json` and `payload.bin`; failures preserve them.
Use one active payload stage. Its exact bytes are checked again before upload
intent, and its upload/readback must resolve before another payload. The host
must keep local scratch bounded; this adapter does not delete retained artifacts.

The returned upload envelope uses only `upload_file`'s supported `file_uri`,
`file_name`, `mime_type` and `parent_folder_id` arguments. The deterministic
operation name supports reconciliation; it is **not** a server idempotency token.
`confirmed_upload()` parses a completed connector result without treating it as
byte verification. After an uncertain outcome, `reconcile_one()` requires exactly
one matching name/parent/size from a complete search. Zero results, multiple
results or pagination stop progress; none triggers an automatic upload retry.
Re-running preparation for the same job offers only reconciliation, never another
upload. Interrupted or damaged local staging also stops without overwriting it.

`readback_requests()` generates metadata and raw `fetch` requests using an observed
connector URL. The host would materialize the returned authenticated file reference.
`verify_readback()` hashes that downloaded file. Its default stronger mode requires
the same real provider version before and after download. Normalized Drive
metadata omits version/checksum fields, so explicitly accepted `exclusive_writer=True`
uses null-version receipts marked `exclusive-writer-sha256-size-readback` instead.
It still checks actual bytes, returned file ID, parent and size. It invents no
version or checksum evidence from a timestamp.

`draft_staged_manifest()` checks the original local manifest checkpoint again and
returns a validated JSON proposal with one verified staged receipt and an advanced
revision. It leaves accepted `files`, the source manifest and all remote files
unchanged. It does not adopt an object as current or publish anything. Replacement
or cleanup still requires explicit authorization before a subsequent payload.

`SerializedSync` requires `exclusive_writer=True` and a fixed private work directory
for the selected mirror. Its `fcntl` lock rejects another **local** run in that
directory. It is not a remote/global lock: other machines, jobs using different
directories and manual edits must be excluded by the accepted operational agreement.
The current journal is checksum-protected, fsynced and atomically replaced locally.
An interrupted checkpoint stops rather than silently discarding intent.
A later fresh run must fetch the remote manifest and recheck object availability.
Reopening a journal marked complete resumes that run's recorded evidence; it does
not establish fresh remote verification.

The host handshake is:

1. Bootstrap only after a complete empty-name search for a new mirror. Persist
   `bootstrap_intent()` before `upload_file`; reconcile uncertainty and verify the
   actual manifest bytes by its confirmed ID before accepting the checkpoint.
2. `upload_intent()` persists the unique operation before returning `upload_file`.
   `upload_known()` records a confirmed ID or a complete, unique reconciliation.
   Read back by that ID, hash/size-check it and call `payload_verified()`.
3. Accumulate at most **64 unique payloads / 64 MiB** of verified unpublished data
   (one individually larger permitted file occupies a batch alone). One upload
   is active at a time. `status()` reports listed payload bytes, unresolved-upload
   budget and unpublished verified bytes as the run advances.
4. Fetch the current manifest's actual bytes. `manifest_intent()` requires exact
   equality to the durable checkpoint before returning `update_file` for the
   **same manifest ID**. There is no If-Match/precondition argument. This is the
   exclusive-writer guarantee, **not atomic remote CAS**.
5. `observe_manifest()` advances only after fetching the exact proposed bytes by
   the pinned manifest ID. An old value after an uncertain call is **not** proof
   the in-flight write failed. No mutation/retry is issued while unresolved.

During bootstrap/partial progress, verified target records stay in `staged`, each
bound to `forCommit`; accepted `files` and their completed `commit` remain unchanged.
Only full verified coverage with no cleanup gap promotes all target mappings and
sets `completeCurrentTree`. No mixed mapping is assigned a completed commit.
Identical content serves all its expected paths with one immutable remote ID.
Unchanged accepted immutable objects require a fresh ID/parent/size availability
observation under the exclusive-writer policy; a mismatch stops. `finish_unchanged()`
can then complete without new payload or manifest writes.

Replacement/obsolete targets are proposed with exact IDs/bytes. The verified partial
checkpoint may be saved, then the run enters `cleanup_required` and stops before
another payload. No old copy is removed and no cleanup request is emitted. Existing
backups outside the selected mirror are never implicit cleanup targets.

`initial_mirror_budget()` computes exact unique payload bytes and a deterministic
bounded-batch metadata estimate. Future ID lengths must be stated; manifest reads,
pre-reads and writes count as traffic. Provider-managed manifest revision retention,
protocol/file-bridge overhead and free quota are not inferred. The scope is the
selected exact public commit, not a later PR/merge head; later changes require a
small fresh incremental pass before claiming a match to new main.

For a host that supports two payload calls concurrently, `TwoLaneSync` retains one
coordinator and the same work-directory lock. It uses a strict version-2 journal
with `v2:` phases, which the old version-1 mutators cannot accept. Bootstrap remains
the version-1 handshake. Stop and release the old runner before migration; only a
positively idle journal with no pending operation, unpublished batch or cleanup
can produce `migration_proposal()`. Install its checksum envelope under that same
local lock only after review. Never run the two coordinators together.

The host stages only `next_paths()` (at most two distinct payloads), then calls
`reserve_wave()` and `dispatch_wave()`. Both slot/byte reservations are fsynced
before either upload request escapes. Pending and verified-unpublished payloads
share the original **64-object / 64 MiB batch**, using the same sorted partition;
an individually larger permitted object runs alone. This is not a separate budget
per lane. Source staging plus downloaded readback can temporarily require twice
the wave's payload bytes; release verified local scratch before staging the next
wave. Existing source files are outside that scratch estimate.

`run_payload_wave()` uses `asyncio.gather(return_exceptions=True)` to drain both
host workers, including a successful sibling of a rejected call. Each worker must
upload once, download by returned ID, check actual SHA-256/size with
`verify_readback()`, and return its result and receipt. It must preserve a known
upload result even if its later readback fails. Workers never write journals or
manifests. `settle_wave()` persists results and receipts through the sole coordinator;
missing, ambiguous or failed outcomes retain reservations and halt new dispatch.
There is no automatic mutation retry. `lane_known()` reconciles exact unique
operation-name search results, `lane_verified()` accepts the verified bytes, and
`resume_reconciled()` requires no unresolved lanes, the unchanged checkpoint and
expired shared backoff. A remote ID cannot serve different upload operations.
After a crash before result persistence, reconcile every dispatched operation;
never re-dispatch its create. Receipt replay is idempotent within the current batch.

Keep accumulating the bounded batch rather than publishing every pair.
`manifest_intent()` cannot cross an unresolved-lane barrier. Its pre-read,
same-ID write and exact-byte readback retain the exclusive-writer guarantee and
make no atomic remote-CAS claim. An uncertain manifest write remains blocked even
if a read still returns the old bytes.

A changed source head requires comparing **every** retained path/hash/size against
the new exact tree. `source_rebind_proposal()` preserves all remote IDs and accepted
files/commit, advances the revision and changes only staged target bindings.
It returns bytes, not a mutation request. The host must separately journal that
intent, pre-read the old checkpoint, write once and read back the exact proposal
before supplying `verified_rebound` to the pure migration proposal. This module
never silently changes the remote source binding or installs a migration. A
conflicting retained path stops for review with no receipt dropped. Publication,
live migration, resumed transfer and cleanup remain separate operational actions.
