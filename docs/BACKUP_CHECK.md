# Current mirror planning and offline byte checks

- **Goal** · One current mirror of an exact Git commit, with LFS payloads at their repository paths.
- **Delivery status** · Tested tooling only, 2026-11-06. Remote full-tree sync, connector compatibility, readback and restore remain unverified. [Acceptance decision](DECISIONS.md).
- **Requirements** · Python 3.11+, Git 2.45+ and POSIX `dir_fd` / `O_NOFOLLOW`. Local checks run offline. Use a stable, fully downloaded snapshot.
- **Owners** · [Read-only CLI and manifest validation](../tools/backup_check.py), [connector request/response contracts](../tools/backup_transfer.py), [byte-check regressions](../tests/test_backup_check.py), [transfer regressions](../tests/test_backup_transfer.py).

## Inventory and actual local byte checks

| Goal | CLI selector | Evidence |
| --- | --- | --- |
| Inventory | `--commit "$commit" --inventory` | Paths, Git blob hashes, LFS pointer identities and sizes from the exact commit. |
| Local tree | `--commit "$commit" --backup-tree PATH` | Actual file SHA-256 and size at each repository path. |
| Local ZIP | `--commit "$commit" --backup-zip PATH` | Same byte check with exact root-relative member names. ZIP stays intact. |

```sh
commit=$(git rev-parse HEAD)
python3 tools/backup_check.py --commit "$commit" --backup-tree /path/to/downloaded-tree
```

- **Exit codes** · `0` successful operation, `1` byte-check gaps, `2` invalid input or check failure. Confirm `completeCurrentTree: true` for coverage. Inventory and planning give no coverage verdict.
- **Gaps** · `missing`, `mismatched`, `pointer_only` and `unverifiable` yield `needs_copy`. `plannedCopyBytes` counts each affected path. Verify exact source bytes before any separately authorized transfer.
- **Fail closed** · Git lazy fetching/transports and local attribute overrides are refused. Symlinks and submodules in the source tree, unsafe or duplicate ZIP paths and unreadable bytes cannot establish coverage. Extra backup files are ignored.
- **Reports** · JSON on stdout. Keep reports containing private paths outside Git and use fresh output names.

## Scope and older source archives

| Claim | Coverage |
| --- | --- |
| Current tree | One committed revision at exact paths. Working changes, Git history, other branches, permissions and external/private inputs fall outside it. |
| Historical archives | [Import identities](WORKFLOW.md#import-and-source-integrity) cover another path layout. Compare exact member hashes and sizes with a separate path mapping. Split archives, filenames, timestamps and CRCs provide no current-mirror coverage. |
| Live backup | Requires independent remote readback and restore evidence. A local check confers no transfer, replacement or cleanup authority. |

## One current-state manifest

- **Private checkpoint** · One manifest with `schemaVersion`, `revision`, exact commit identity, accepted `files` and interrupted/unpublished `staged` entries. Schema and limit live in [the validator](../tools/backup_check.py).
- **Byte and object identity** · Each row binds path, expected hash/size, exact remote ID/version and evidence. Staged rows bind a `forCommit`. Verified staged rows need explicit adoption.
- **Digest** · Pin the intended local checkpoint SHA-256. Fresh remote reads and concurrency control are independent requirements.

```json
{"schemaVersion":1,"revision":0,"commit":null,"files":[],"staged":[]}
```

```sh
python3 tools/backup_check.py --commit "$commit" --plan-manifest "$manifest_path" \
  --expected-manifest-sha256 "$expected_digest"
```

## Incremental plan and storage estimates

| Result | Acceptance before execution |
| --- | --- |
| `reuse_candidate` | Fresh object availability, identity and byte evidence where metadata is insufficient. |
| `verify_candidate` | Remote verification and explicit adoption of matching unverified or staged content. |
| `upload` | Separate authority, exact source bytes and an applicable destination budget. Failed/mismatched objects never suppress it. |
| Replacement, obsolete and staged candidates | Review exact object IDs, shared references and interrupted work before any separately authorized cleanup. |

- **Planning scope** · Deduplicate by SHA-256 and size across paths. Count listed storage per remote ID. Quota, unlisted objects and provider revision retention fall outside these estimates.
- **Budget** · Use unique upload bytes, largest payload, and the all-candidates-fail contingency. Recalculate as the mirror changes. Initial staging estimates cover one changed file and listed staged bytes.
- **Exit** · A valid plan exits `0` even with pending uploads. Planner output carries no remote coverage, freshness or atomic compare-and-swap claim.

## Serialized exclusive-writer connector workflow

| Goal | Acceptance |
| --- | --- |
| One writer | Authorized destination and explicit exclusive-writer agreement across hosts and manual edits. Local journal lock covers one work directory. Remote compare-and-swap requires independent provider support. |
| Exact stage | `prepare_one()` binds the authorized plan, commit/path and payload hash/size. Use a fresh private stage and explicit file budget. See `backup_transfer.py --capabilities` and `--help`. |
| Safe create | Durable intent before upload. Preserve the known result even when readback fails. Reconcile uncertain creates by complete, unique name/parent/size evidence. A missing, ambiguous or paginated result stops progress. |
| Verified object | Fetch by confirmed ID and check SHA-256, size and parent. Require stable real provider version where available. Explicit exclusive-writer receipts may carry a null version. |
| Bounded batch | Shared cap of 64 objects / 64 MiB across pending and verified-unpublished work. An individually larger permitted object runs alone. Budget scratch for staging plus readback. |
| Publish checkpoint | Empty unresolved-operation set, fresh exact pre-read, same manifest ID and exact readback. An old value during an uncertain write leaves the operation unresolved. |
| Complete mirror | Accepted files/commit advance only after full verified coverage and resolved cleanup. Reused immutable objects need a fresh availability check. Replacement/obsolete work stops at `cleanup_required`. |

| Coordinator | Journal and continuation |
| --- | --- |
| `SerializedSync` | V1 and one active upload. |
| `TwoLaneSync` | V2, at most two reserved payloads. Persist both reservations before dispatch. Drain and persist sibling results even after one worker fails. |
| `PayloadPoolSync` | V3 with a persisted 2, 4 or 8 lane ceiling. Same shared budget and unresolved-operation barrier. |

- **Recovery** · One coordinator and one journal. Retain unresolved intents, reservations, verified receipts and all remote IDs. Reconcile before dispatching further mutations. A resumed completed journal records the original result. Fresh coverage needs a fresh check.
- **Migration** · Proposals require a verified idle predecessor and exclusive lock. Source rebind compares every retained path/hash/size and changes staged bindings only. Require journaled pre-read, write and exact readback before migration. Review installation and continuation authority separately.
- **Execution** · Tool returns requests for an authorized host. Existing receipts establish historical scope only. Upload, publication, cleanup and restart require applicable authorization.
