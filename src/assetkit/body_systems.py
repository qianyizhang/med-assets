"""Body Systems plate replay evidence and its optional 3D lesson inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from med_assets.artifacts import unique_keys
from med_assets.teaching import CurrentTeaching
from pydantic import Field, model_validator

from .blobs import inspect_mesh, safe_path, verify
from .errors import AssetKitError
from .models import AssetModel
from .registry import AssetRegistry, Export, RecordExportRef

DISPLAY_INDEX = "lessons/body-systems/display/index.json"
REPLAY_BINDINGS = "lessons/body-systems/display/replay-bindings.json"
PELVIC_LAYERS = "sites/anatomy-gallery/app/src/content/gallery/pelvic-lesson-layers.json"
COLLECTIONS = "transport/collection-archives.json"
SURVEY_JOBS = "sites/body-systems-survey/jobs.json"
WORKSHOP_INPUTS = "assemblies/workshop-s1233/inputs.json"

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class FileDigest(AssetModel):
    path: str
    sha256: Digest


class ReplayInput(FileDigest):
    bytes: int = Field(gt=0)
    ref: RecordExportRef | None = None
    archive: Literal["teaching-media"] | None = None
    workshop: Literal["cardiovascular", "digestive"] | None = None

    @model_validator(mode="after")
    def _one_owner(self) -> ReplayInput:
        if sum(owner is not None for owner in (self.ref, self.archive, self.workshop)) != 1:
            raise ValueError(f"Expected one replay owner for {self.path}")
        return self


class WorkshopReplay(AssetModel):
    config: FileDigest
    receipt: FileDigest
    mask_audit: FileDigest


class PlateFrame(AssetModel):
    file: str
    sha256: Digest


class RenderReceipt(AssetModel):
    receipt: FileDigest
    owner: str
    inputs: tuple[FileDigest, ...] = Field(min_length=1)
    views: dict[str, tuple[PlateFrame, PlateFrame]]


class PlateKey(AssetModel):
    system: str
    kind: Literal["assembly", "detail"]
    id: str

    @property
    def consumer_id(self) -> str:
        return f"body-systems:{self.system}:{self.kind}:{self.id}"


class PlateReplay(PlateKey):
    scene: str
    view: str


class ReplayBindings(AssetModel):
    schema_version: Literal[1]
    display_index_sha256: Digest
    inputs: tuple[ReplayInput, ...]
    workshop: WorkshopReplay
    scenes: dict[str, RenderReceipt]
    plates: tuple[PlateReplay, ...]


class DisplayFrame(AssetModel):
    path: str
    angle: str
    source_sha256: Digest


class DisplayPlate(AssetModel, extra="ignore"):
    id: str
    kind: Literal["assembly", "detail"]
    title: str
    frames: tuple[DisplayFrame, DisplayFrame]


class DisplaySystem(AssetModel, extra="ignore"):
    id: str
    plates: tuple[DisplayPlate, ...]


class PelvicLayer(AssetModel):
    id: str
    nodes: Annotated[tuple[str, ...], Field(min_length=1)] | None = None


class PelvicCamera(AssetModel):
    position: tuple[float, float, float]
    target: tuple[float, float, float]
    height: float = Field(gt=0)


class PelvicAction(AssetModel):
    path: str
    system: str
    ref: RecordExportRef
    task_id: str
    assessment_sha256: Digest
    camera: PelvicCamera
    layers: tuple[PelvicLayer, ...] = Field(min_length=1)
    answer_layer: str


class BoundPelvicAction(PlateKey):
    ref: RecordExportRef
    path: str
    sha256: Digest
    bytes: int
    parts: tuple[str, ...]


def _json(repo: Path, relative: str):
    return json.loads(safe_path(repo, relative).read_bytes(), object_pairs_hook=unique_keys)


def _archive_members(repo: Path) -> dict[str, str]:
    spec = _json(repo, COLLECTIONS)["teaching-media"]["checksumList"]
    source = safe_path(repo, spec["path"]).read_bytes()
    if len(source) != spec["bytes"] or hashlib.sha256(source).hexdigest() != spec["sha256"]:
        raise AssetKitError(
            "Body Systems teaching-media checksum list differs from its archive pin"
        )
    return {
        name.removeprefix("*"): digest
        for digest, name in (line.split(maxsplit=1) for line in source.decode().splitlines())
    }


def _check_recipe_owners(
    repo: Path, bindings: ReplayBindings, sources: dict[str, ReplayInput]
) -> None:
    """Cross-check frozen snapshots against the independent tracked replay definitions."""
    baseline = {
        (pin["path"], pin["sha256"]) for job in _json(repo, SURVEY_JOBS) for pin in job["inputs"]
    }
    optional = _json(repo, WORKSHOP_INPUTS)["assemblies"]
    for scene, receipt in bindings.scenes.items():
        if receipt.owner == SURVEY_JOBS:
            if any(
                sources[pin.path].ref is None or (pin.path, pin.sha256) not in baseline
                for pin in receipt.inputs
            ):
                raise AssetKitError(
                    f"Body Systems tracked render input differs from its survey job: {scene}"
                )
            continue
        if len(receipt.inputs) != 1:
            raise AssetKitError(f"Body Systems study receipt requires one input: {scene}")
        pin = receipt.inputs[0]
        source = sources[pin.path]
        if source.workshop is not None:
            if (
                receipt.owner != WORKSHOP_INPUTS
                or scene != f"{source.workshop}-s1233"
                or source.workshop not in optional
            ):
                raise AssetKitError(f"Body Systems Workshop scene differs from its recipe: {scene}")
        elif (
            source.archive is not None
            and receipt.owner.startswith("reviews/")
            and Path(receipt.owner).name == "renders.json"
        ):
            review = _json(repo, receipt.owner)
            if (Path(pin.path).name, pin.sha256) != (review["glb"], review["sha256"]):
                raise AssetKitError(
                    f"Body Systems archived input differs from its owning review: {scene}"
                )
        else:
            raise AssetKitError(f"Body Systems render receipt has an unknown owner: {scene}")


def _resolve(repo: Path, registry: AssetRegistry, ref: RecordExportRef) -> Export:
    _, _, export = registry.require_record_export(ref)
    if (
        export.format != "glb"
        or export.frame is None
        or export.frame.convention != "glb-y-up-m"
        or export.frame.units != "m"
    ):
        raise AssetKitError(f"Body Systems GLB frame differs for {export.path}")
    checked = verify(repo, export.path, export.sha256, export.bytes)
    if checked.status not in {"verified", "pointer-match"}:
        raise AssetKitError(
            f"Body Systems GLB identity differs for {export.path}: {checked.status}"
        )
    return export


def read_body_systems(
    repo: Path, registry: AssetRegistry | None = None
) -> tuple[ReplayBindings, tuple[BoundPelvicAction, ...]]:
    """Validate lesson bindings without requiring archived or locally rebuilt survey inputs."""
    raw = safe_path(repo, DISPLAY_INDEX).read_bytes()
    bindings = ReplayBindings.model_validate(_json(repo, REPLAY_BINDINGS))
    if hashlib.sha256(raw).hexdigest() != bindings.display_index_sha256:
        raise AssetKitError("Body Systems replay bindings do not match the display index")
    display: dict[str, DisplayPlate] = {}
    for value in json.loads(raw, object_pairs_hook=unique_keys):
        system = DisplaySystem.model_validate(value)
        for plate in system.plates:
            plate_key = PlateKey(system=system.id, kind=plate.kind, id=plate.id)
            if plate_key.consumer_id in display:
                raise AssetKitError(
                    f"Duplicate Body Systems display plate: {plate_key.consumer_id}"
                )
            display[plate_key.consumer_id] = plate

    sources = {source.path: source for source in bindings.inputs}
    if len(sources) != len(bindings.inputs):
        raise AssetKitError("Duplicate Body Systems replay input")
    plates = {plate.consumer_id: plate for plate in bindings.plates}
    if len(plates) != len(bindings.plates) or plates.keys() != display.keys():
        raise AssetKitError("Body Systems replay bindings omit or duplicate a display plate")
    used_views: set[tuple[str, str]] = set()
    for key, plate in plates.items():
        receipt = bindings.scenes.get(plate.scene)
        source = receipt.views.get(plate.view) if receipt is not None else None
        if source is None:
            raise AssetKitError(f"Unknown Body Systems receipt view for {key}")
        used_views.add((plate.scene, plate.view))
        for original, rendered in zip(source, display[key].frames, strict=True):
            filename = Path(original.file)
            expected = f"lessons/body-systems/display/{plate.scene}-{filename.stem}.webp"
            if (
                filename.name != original.file
                or filename.suffix != ".png"
                or expected != rendered.path
                or original.sha256 != rendered.source_sha256
            ):
                raise AssetKitError(f"Body Systems plate differs from its render receipt: {key}")
    if used_views != {
        (scene, view) for scene, receipt in bindings.scenes.items() for view in receipt.views
    }:
        raise AssetKitError("Body Systems replay bindings include unused receipt views")

    used_paths: set[str] = set()
    for scene, receipt in bindings.scenes.items():
        if (
            not safe_path(repo, receipt.owner).is_file()
            or Path(receipt.receipt.path).parent.name != scene
        ):
            raise AssetKitError(f"Body Systems render receipt has an invalid owner: {scene}")
        for claim in receipt.inputs:
            source = sources.get(claim.path)
            if source is None or source.sha256 != claim.sha256:
                raise AssetKitError(
                    f"Body Systems render input differs from its receipt: {claim.path}"
                )
            used_paths.add(claim.path)
    if used_paths != sources.keys():
        raise AssetKitError("Body Systems replay bindings include unused sources")
    _check_recipe_owners(repo, bindings, sources)

    actions = {
        key: PelvicAction.model_validate(value) for key, value in _json(repo, PELVIC_LAYERS).items()
    }
    if registry is None:
        registry = AssetRegistry.load_records(
            repo,
            [source.ref.record for source in bindings.inputs if source.ref]
            + [action.ref.record for action in actions.values()],
        )

    archives = _archive_members(repo)
    workshop = bindings.workshop
    if (
        workshop.config.path != WORKSHOP_INPUTS
        or verify(repo, workshop.config.path, workshop.config.sha256).status != "verified"
    ):
        raise AssetKitError("Body Systems Workshop recipe differs from its pinned configuration")
    if Path(workshop.mask_audit.path).parent != Path(workshop.receipt.path).parent:
        raise AssetKitError("Body Systems Workshop receipt and mask audit must share their owner")
    for source in bindings.inputs:
        if source.ref is not None:
            export = _resolve(repo, registry, source.ref)
            if (export.path, export.sha256, export.bytes) != (
                source.path,
                source.sha256,
                source.bytes,
            ):
                raise AssetKitError(
                    f"Body Systems native replay pin differs from its receipt: {source.path}"
                )
        elif source.archive is not None:
            if archives.get(source.path) != source.sha256:
                raise AssetKitError(f"Body Systems teaching-media member differs: {source.path}")
        elif Path(source.path) != Path(workshop.receipt.path).with_name(f"{source.workshop}.glb"):
            raise AssetKitError(
                f"Body Systems Workshop source differs from its receipt: {source.path}"
            )

    current = CurrentTeaching(repo)
    bound_actions = []
    for key, action in actions.items():
        plate_key = PlateKey(system=action.system, kind="detail", id=key)
        if plate_key.consumer_id not in display:
            raise AssetKitError(f"Unknown Body Systems pelvic detail: {plate_key.consumer_id}")
        export = _resolve(repo, registry, action.ref)
        selection = current.selections.get(action.path)
        if (
            export.path != action.path
            or selection is None
            or (selection.task_id, selection.assessment_sha256)
            != (action.task_id, action.assessment_sha256)
        ):
            raise AssetKitError(
                f"Body Systems pelvic export differs from its selected assessment: {key}"
            )
        assessment = current.resolve(action.path, action.task_id)
        if (assessment.row["export"]["sha256"], assessment.row["export"]["bytes"]) != (
            export.sha256,
            export.bytes,
        ):
            raise AssetKitError(f"Body Systems pelvic identity differs from its assessment: {key}")
        known_layers = {layer.id for layer in action.layers}
        known_nodes = {node for part in export.parts for node in part.selectors}
        nodes = {node for layer in action.layers for node in layer.nodes or ()}
        if len(known_layers) != len(action.layers) or action.answer_layer not in known_layers:
            raise AssetKitError(f"Invalid Body Systems pelvic layers: {key}")
        if nodes - known_nodes:
            raise AssetKitError(
                f"Unknown Body Systems pelvic selectors: {sorted(nodes - known_nodes)}"
            )
        if export.storage_status == "verified":
            mesh = inspect_mesh(repo, export.path)
            if mesh is None or any(mesh.node_names.count(node) != 1 for node in nodes):
                raise AssetKitError(f"Body Systems pelvic GLB selectors differ: {key}")
        all_parts = any(layer.nodes is None for layer in action.layers)
        assert export.sha256 is not None and export.bytes is not None
        bound_actions.append(
            BoundPelvicAction(
                system=action.system,
                kind="detail",
                id=key,
                ref=action.ref,
                path=export.path,
                sha256=export.sha256,
                bytes=export.bytes,
                parts=tuple(
                    part.id
                    for part in export.parts
                    if all_parts or nodes.intersection(part.selectors)
                ),
            )
        )
    return bindings, tuple(bound_actions)


if __name__ == "__main__":
    read_body_systems(Path.cwd())
