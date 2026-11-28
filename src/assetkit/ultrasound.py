"""Read exact package references from the ultrasound recipe owners."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .blobs import safe_path
from .errors import AssetKitError
from .models import AssetModel
from .registry import ExportRef, RecordExportRef

EXTERIOR_ATLAS_CONFIG = "experiments/ultrasound-sweep/exterior-atlas.json"
GALLERY_REFERENCE_CONFIG = "experiments/ultrasound-sweep/gallery-reference-assets.json"


class SweepSceneAssetRef(ExportRef):
    """An exact export with its registration in the sweep scene."""

    registration: str = "unknown"


class ExteriorAtlas(AssetModel):
    schema_version: Literal[1]
    skin: RecordExportRef
    skeleton: RecordExportRef

    def inputs(self) -> Iterable[RecordExportRef]:
        return self.skin, self.skeleton


def read_exterior_atlas(repo: Path) -> ExteriorAtlas:
    """Read the configuration shared by the index and the geometry recipes."""
    return ExteriorAtlas.model_validate_json(safe_path(repo, EXTERIOR_ATLAS_CONFIG).read_bytes())


class GalleryDonor(AssetModel):
    slot: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    edition: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]*$")
    ref: RecordExportRef
    label: str
    space: str
    credit: str
    attribution: str
    guide: str | None = None
    nodes: dict[str, tuple[str, str]]

    @property
    def runtime_case(self) -> str:
        return f"{self.slot}-{self.edition}"


class GalleryReferences(AssetModel):
    schema_version: Literal[1]
    donors: tuple[GalleryDonor, ...]

    @model_validator(mode="after")
    def _unique_slots(self) -> GalleryReferences:
        slots = {donor.slot for donor in self.donors}
        if len(slots) != len(self.donors):
            raise ValueError("Expected one entry per Gallery donor slot")
        return self

    def mammary(self) -> GalleryDonor:
        for donor in self.donors:
            if donor.slot == "breasts_hra":
                return donor
        raise AssetKitError("Missing breasts_hra Gallery donor for the breast acquisition recipe")


def read_gallery_references(repo: Path) -> GalleryReferences:
    return GalleryReferences.model_validate_json(
        safe_path(repo, GALLERY_REFERENCE_CONFIG).read_bytes()
    )
