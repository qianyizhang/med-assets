# Local verification

Run from the repository root. The ordinary PR gate needs **Python 3.11+ and Git**,
a full text/pointer checkout, and no third-party Python packages. It makes no
network requests, fetches no LFS media and performs no rendering or uploads.

```sh
python3 tools/verify.py offline
```

This runs every top-level and review-record unit test, with explicit required
suite files and minimum counts. Missing imports, missing or empty required suites,
skips, expected failures, module setup/teardown errors, partial execution and
assertion failures fail the command. Plain
`unittest discover -s tests` does not recurse into all of this repository's
non-package test directories; it is not the complete verification command.

Offline checks also validate all content-addressed transport manifests using the
existing fixed host/size/hash limits, the fixed historical foundation record set, all
tracked LFS pointer syntax/OIDs, and the 591 imported path references. For text,
the command hashes working files. For LFS media, it checks reference OIDs against
the Git index and pointer files when present. It compares pointer sizes against
the historical import manifest and reviewed transport manifests when a matching
record exists, and rejects conflicting sizes for the same OID. For OIDs without a
matching size record, the size is checked only for valid syntax. **It does not
hash hydrated media.** Stage intended LFS pointer changes before checking their
index identities.

The 25 existing transport manifest IDs and 25 selected historical foundation
record paths are protected against accidental omission. New transport manifests
are validated automatically without changing the baseline. New foundation runs
remain outside this historical selector until explicitly covered by a validator.
Intentional historical corrections require review and an updated baseline.

## Scope selection and acceptance

Choose tests by affected behavior and dependencies. Feature changes must reuse or
add relevant E2E journeys and pass scoped validation locally in the authorized
development environment. Include relevant export/reload, consumer interaction and failure
recovery checks; technical integrity does not establish visual or anatomical quality.
Documentation-only changes need applicable documentation/offline checks, not
unrelated functional replays.

Regular hosted CI is a selective core/must-pass sanity layer, not the only or final
delivery guard. Run full suites deliberately for releases, major refactors or
broad/uncertain risk. Each PR records affected scope, chosen commands and rationale,
exact revision, passed/failed/blocked coverage and remaining limits. Hosted green
never replaces required local E2E evidence.

Existing protected runtime restrictions still apply. If local E2E is barred or
prerequisites are unavailable, record it blocked and require a reviewed, explicitly
authorized local mode where needed; never spoof CI flags or bypass execution guards.
This guidance changes no workflow, security control or current CI job. The complete
offline scope described above remains required; it is not a full media/runtime suite.

## Current and historical integrity

`SHA256SUMS` is immutable evidence of the 2026-10-22 import: 591 files, originally
370,698,859 bytes. `metadata/asset-manifest.json` and the earlier archive checksums
retain that historical scope too. Do not regenerate them to conceal later edits.
`shasum -a 256 -c SHA256SUMS` is appropriate for the original snapshot, not current
main: the head annotation change (`5fae2dd`) and abdomen label change (`6c6a9e1`)
legitimately changed two SVGs. Their original/current hashes and reasons are in
`metadata/current-import-overrides.json`; an unrecorded text change fails. An
override for an imported LFS file also requires its reviewed `currentBytes`.
The recorded change-commit fields are review provenance; offline verification
does not establish their ancestry or the intent of a change.

After obtaining actual LFS payloads through an authorized download route:

```sh
python3 tools/verify.py payload-integrity
```

This includes the offline checks, then verifies size and SHA-256 of **every local
tracked LFS payload**, strict foundation artifact/evidence hashes, and the 11
existing bounded-package validators listed in `tools/verify.py`. Unresolved
pointers fail. No third-party Python dependencies are needed for this mode.
Do not use Python `-O`, which disables assertions in the retained package checks;
the entrypoint rejects it. The result is local byte identity and selected package
consistency, not exhaustive geometry, fresh remote availability or review of pixels.

## Dental tests and replay

The dental suite is separate and required when changing the UFF tool. It includes
six synthetic/safety tests and one actual pinned-GLB hash assertion; all seven must
pass. It is **not included or reported as passed** by either command above.

Use an isolated virtual environment. The historical replay pins are preserved at
[`tools/dental/requirements-uff.txt`](../tools/dental/requirements-uff.txt); they
require NumPy, SciPy, scikit-image, Pillow, trimesh, point-cloud-utils and PyMeshLab.
Package availability and native-library support must be established on the target
platform; do not replace a missing dependency with a skipped test.

```sh
python3 -m venv /tmp/med-assets-dental-venv
/tmp/med-assets-dental-venv/bin/python -m pip install -r tools/dental/requirements-uff.txt
/tmp/med-assets-dental-venv/bin/python tools/verify.py dental
```

Source replays stay recipe-specific in this first maintenance slice. They are not
part of ordinary PR CI. For the small deterministic esophageal illustration:

```sh
python3 tests/esophagus_wall/replay.py --output /tmp/esophagus-NEW-run
```

Read its [recipe prerequisites](../tests/esophagus_wall/README.md) first: Blender
4.3.2, Pillow and Linux DejaVu/Noto CJK font paths used by the label scripts. A new
output directory is required. Check `replay-result.json` for the exact default GLB
hash and inspect the rendered pixels separately. Successful process exit alone
does not certify the expected hash, anatomy, or browser runtime. The UFF source
replay additionally requires its pinned public ZIP, which is not bundled here.
Do not mass-edit historical recipes or their per-organ metadata to standardize
fonts/dependencies.

## Metadata-only replay

`tools/patch_scene_metadata.py` owns the scene-extra patch behavior for the 15
organ alternatives and L3. Each package keeps its original `approved-patch.json`
and exact input/output hashes; its README gives the command with `--patch`.
The old per-organ script copies have been removed. Their original implementations
remain in Git history at `cb93598`.

The tool checks source identity, permitted field operations and target identity
before creating output, preserves all other GLB content and refuses an existing
output file. Synthetic CLI tests run in offline CI; they do not certify model
geometry, pixels or anatomy. Actual replay still needs the exact baseline bytes.

## CI and quality boundaries

`offline-verification.yml` uses `pull_request`, `contents: read`, a pinned checkout
with `persist-credentials: false`, and no secrets, uploads or media hydration.
It intentionally runs the complete **offline scope**, not every package replay.
Missing dental/replay prerequisites therefore cannot masquerade as a suite pass.

The existing bounded LFS upload workflow and its source-host, size, hash and fresh
readback controls remain separate and unchanged. Native downloads working on one
machine do not establish upload authorization or remove that transport need.
The manual browser workflow also remains separate. Technical integrity, actual
visual review, anatomical/clinical approval, browser runtime and remote publication
are independent gates; none is promoted by this command.
