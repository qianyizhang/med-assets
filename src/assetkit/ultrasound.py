"""Native recipe dependency for the ultrasound BodyParts3D exterior."""

from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from .blobs import safe_path
from .models import AssetModel
from .registry import RecordExportRef

EXTERIOR_ATLAS_CONFIG = "experiments/ultrasound-sweep/exterior-atlas.json"


class ExteriorAtlas(AssetModel):
    schema_version: Literal[1]
    skin: RecordExportRef
    skeleton: RecordExportRef

    def inputs(self) -> Iterable[RecordExportRef]:
        return self.skin, self.skeleton


def read_exterior_atlas(repo: Path) -> ExteriorAtlas:
    """Read the configuration shared by the index and the geometry recipes."""
    return ExteriorAtlas.model_validate_json(safe_path(repo, EXTERIOR_ATLAS_CONFIG).read_bytes())
