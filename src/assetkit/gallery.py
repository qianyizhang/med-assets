"""Exact admission and reverse dependencies for the candidate Gallery Library."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

from med_assets.artifacts import repo_file, source_path, unique_keys
from med_assets.teaching import CurrentTeaching
from pydantic import Field, model_validator

from .blobs import verify
from .errors import AssetKitError
from .models import AssetModel
from .registry import AssetRegistry, Export, RecordExportRef

ADMISSION = "sites/anatomy-gallery/library-admission.json"
CANDIDATE_READER = "sites/anatomy-gallery/app/src/content/gallery/library-compiler.js"
LEGACY_DENTAL = "sites/anatomy-gallery/app/src/content/assets/legacy-dental-assets.json"
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class LibraryReader(AssetModel):
    family: str = Field(min_length=1)
    route: str = Field(pattern=r"^library/[^/]+(?:/[^/]+)?$")
    role: Literal["family-media", "listed-revision", "recommended-revision"]

    @model_validator(mode="after")
    def _exact_route(self) -> LibraryReader:
        source_path(self.route)
        return self


class Disposition(AssetModel):
    kind: Literal["replay-only", "historical", "frozen", "external", "unavailable"]
    evidence: str
    reason: str = Field(min_length=1)


class LibraryFile(AssetModel):
    sha256: Digest
    bytes: Annotated[int, Field(strict=True, gt=0)]


class Admission(LibraryFile):
    readers: tuple[LibraryReader, ...] = Field(min_length=1)
    ref: RecordExportRef | None = None
    disposition: Disposition | None = None
    unavailable: str | None = None

    @model_validator(mode="after")
    def _one_owner(self) -> Admission:
        if (self.ref is None) == (self.disposition is None):
            raise ValueError("Expected exactly one native ref or retained disposition")
        if bool(self.unavailable) != bool(
            self.disposition and self.disposition.kind == "unavailable"
        ):
            raise ValueError("Unavailable status must match the disposition")
        if len(set(self.readers)) != len(self.readers):
            raise ValueError("Duplicate Gallery reader")
        return self


class LibraryAdmission(AssetModel):
    schema_version: Literal[1]
    paths: dict[str, Admission] = Field(min_length=1)


class CompiledReader(LibraryFile):
    path: str
    reader: LibraryReader
    unavailable: str | None = None


class CompiledSelection(LibraryFile):
    path: str
    task_id: str
    family_id: str
    collection: str


class CompiledLibrary(AssetModel):
    files: tuple[CompiledReader, ...]
    selections: tuple[CompiledSelection, ...]


def _document(repo: Path, path: str) -> Any:
    return json.loads(repo_file(repo, path).read_bytes(), object_pairs_hook=unique_keys)


def _native_exports(registry: AssetRegistry) -> dict[str, list[tuple[RecordExportRef, Export]]]:
    exports: dict[str, list[tuple[RecordExportRef, Export]]] = defaultdict(list)
    for asset, revision, export in registry.iter_exports():
        record = asset.source_manifest
        if record and PurePosixPath(record).name == "asset.record.json":
            ref = RecordExportRef(
                record=record, asset=asset.id, revision=revision.id, export=export.id
            )
            exports[export.path].append((ref, export))
    return exports


def read_library_admission(
    repo: Path,
    registry: AssetRegistry | None = None,
) -> LibraryAdmission:
    """Check exact package references before projecting the catalog dependencies."""
    admission = LibraryAdmission.model_validate(_document(repo, ADMISSION))
    if registry is None:
        registry = AssetRegistry.load(repo, include_legacy_adapters=False)
    native_paths = _native_exports(registry).keys()
    for path, row in admission.paths.items():
        source_path(path)
        if row.ref is None:
            if path in native_paths:
                raise AssetKitError(f"Gallery native export requires an exact package ref: {path}")
            continue
        if PurePosixPath(row.ref.record).name != "asset.record.json":
            raise AssetKitError(f"Gallery ref requires a package record: {path}")
        source_path(row.ref.record)
        _, _, export = registry.require_record_export(row.ref)
        if (export.path, export.sha256, export.bytes) != (path, row.sha256, row.bytes):
            raise AssetKitError(f"Gallery package ref differs from the exact Library file: {path}")
    return admission


def _check_dispositions(repo: Path, admission: LibraryAdmission) -> None:
    external = {
        claim["path"]: (claim["sha256"], claim["bytes"])
        for claim in _document(repo, LEGACY_DENTAL)["assets"]
    }
    for path, row in admission.paths.items():
        disposition = row.disposition
        if disposition:
            repo_file(repo, disposition.evidence)
            if disposition.kind == "external":
                if disposition.evidence != LEGACY_DENTAL or external.get(path) != (
                    row.sha256,
                    row.bytes,
                ):
                    raise AssetKitError(
                        f"Gallery external delivery differs from its receipt: {path}"
                    )
                continue
            if disposition.kind == "unavailable":
                if repo_file(repo, path, exists=False).exists() or path in external:
                    raise AssetKitError(
                        f"Gallery unavailable export has a file or delivery receipt: {path}"
                    )
                continue
            if disposition.kind == "replay-only":
                if PurePosixPath(disposition.evidence).name != "asset.record.json":
                    raise AssetKitError(
                        f"Gallery replay-only file needs its package source declaration: {path}"
                    )
                owner = _document(repo, disposition.evidence)
                used_sources = {
                    source
                    for revision in owner["revisions"]
                    for source in revision.get("sourceIds", [])
                }
                if not any(
                    claim.get("sourceId") in used_sources
                    and (claim.get("path"), claim.get("sha256"), claim.get("bytes"))
                    == (path, row.sha256, row.bytes)
                    for claim in owner["sources"]
                ):
                    raise AssetKitError(
                        f"Gallery replay-only file differs from its package source: {path}"
                    )
        if path in external:
            raise AssetKitError(
                f"Gallery legacy dental delivery requires an external disposition: {path}"
            )
        blob = verify(repo, path, row.sha256, row.bytes)
        if blob.status not in {"verified", "pointer-match"}:
            raise AssetKitError(
                f"Gallery checkout differs from the Library admission ({blob.status}): {path}"
            )


def _check_compiled_files(admission: LibraryAdmission, compiled: CompiledLibrary) -> None:
    readers: dict[str, set[LibraryReader]] = {}
    for item in compiled.files:
        declared = admission.paths.get(item.path)
        if declared is None:
            raise AssetKitError(f"Missing Gallery Library admission: {item.path}")
        if (item.sha256, item.bytes, item.unavailable) != (
            declared.sha256,
            declared.bytes,
            declared.unavailable,
        ):
            raise AssetKitError(
                f"Compiled Gallery Library identity or availability differs: {item.path}"
            )
        readers.setdefault(item.path, set()).add(item.reader)
    for path, declared in admission.paths.items():
        if readers.get(path) != set(declared.readers):
            raise AssetKitError(f"Compiled Gallery Library reader routes or roles differ: {path}")


def _check_compiled_selections(
    repo: Path, admission: LibraryAdmission, compiled: CompiledLibrary
) -> None:
    expected: dict[str, CompiledSelection] = {}
    for selection, assessment in CurrentTeaching(repo).selected():
        path = selection.path
        declared = admission.paths.get(path)
        if declared is None or declared.ref is None:
            raise AssetKitError(
                f"Maintained Gallery selection requires an admitted package ref: {path}"
            )
        if (declared.sha256, declared.bytes) != (
            assessment.row["export"]["sha256"],
            assessment.row["export"]["bytes"],
        ):
            raise AssetKitError(f"Gallery admission differs from the maintained assessment: {path}")
        expected[path] = CompiledSelection(
            path=path,
            sha256=declared.sha256,
            bytes=declared.bytes,
            task_id=selection.task_id,
            family_id=selection.family_id,
            collection=selection.collection,
        )
    seen: set[str] = set()
    for item in compiled.selections:
        if item.path in seen or expected.get(item.path) != item:
            raise AssetKitError(
                f"Compiled Gallery selection differs from its maintained task: {item.path}"
            )
        seen.add(item.path)
    if missing := expected.keys() - seen:
        raise AssetKitError(
            f"Compiled Gallery is missing maintained selections: {', '.join(sorted(missing))}"
        )


def check_compiled_library(repo: Path, compiled: CompiledLibrary) -> None:
    """Validate the real compiler's observations before writing the candidate read models."""
    admission = read_library_admission(repo)
    _check_compiled_files(admission, compiled)
    _check_dispositions(repo, admission)
    _check_compiled_selections(repo, admission, compiled)


def plan_library_admission(repo: Path, compiled: CompiledLibrary) -> LibraryAdmission:
    """Derive a candidate snapshot from the compiler and owners; keep authored exceptions."""
    current = _document(repo, ADMISSION)["paths"]
    exceptions = {
        path: Disposition.model_validate(row["disposition"])
        for path, row in current.items()
        if "disposition" in row
    }
    observed: dict[str, list[CompiledReader]] = defaultdict(list)
    for item in compiled.files:
        observed[item.path].append(item)
    if stale := exceptions.keys() - observed.keys():
        raise AssetKitError(
            f"Remove retired Gallery dispositions before refreshing: {', '.join(sorted(stale))}"
        )
    native = _native_exports(AssetRegistry.load(repo, include_legacy_adapters=False))
    proposed: dict[str, Admission] = {}
    for path, matches in sorted(observed.items()):
        source_path(path)
        file = matches[0]
        disposition = exceptions.get(path)
        refs = [
            ref
            for ref, export in native.get(path, [])
            if (export.sha256, export.bytes) == (file.sha256, file.bytes)
        ]
        if native.get(path) and not refs:
            raise AssetKitError(
                f"Gallery compiler identity differs from the native package: {path}"
            )
        if len(refs) > 1:
            old_ref = current.get(path, {}).get("ref")
            refs = [ref for ref in refs if ref.to_dict() == old_ref]
            if not refs:
                raise AssetKitError(
                    f"Gallery path has multiple package owners; declare its exact ref: {path}"
                )
        if refs and disposition:
            raise AssetKitError(
                f"Remove retained disposition before admitting its native package export: {path}"
            )
        if not refs and not disposition:
            raise AssetKitError(
                f"Gallery path needs a native export or authored retained disposition: {path}"
            )
        readers = tuple(
            sorted(
                {item.reader for item in matches},
                key=lambda item: (item.family, item.route, item.role),
            )
        )
        proposed[path] = Admission(
            sha256=file.sha256,
            bytes=file.bytes,
            readers=readers,
            ref=next(iter(refs), None),
            disposition=disposition,
            unavailable=file.unavailable,
        )
    admission = LibraryAdmission(schema_version=1, paths=proposed)
    _check_compiled_files(admission, compiled)
    _check_dispositions(repo, admission)
    _check_compiled_selections(repo, admission, compiled)
    return admission


def main() -> None:
    try:
        compiled = CompiledLibrary.model_validate(
            json.load(sys.stdin, object_pairs_hook=unique_keys)
        )
        if sys.argv[1:] == ["--plan"]:
            print(plan_library_admission(Path.cwd(), compiled).to_json())
        else:
            check_compiled_library(Path.cwd(), compiled)
    except (AssetKitError, KeyError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
