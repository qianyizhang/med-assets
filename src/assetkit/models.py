"""Shared Pydantic v2 base model for AssetKit domain objects and query views."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AssetModel(BaseModel):
    """Immutable domain/view model with camelCase JSON aliases and no null noise."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a deterministic camelCase dict omitting unset None fields."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to deterministic camelCase JSON omitting unset None fields."""
        return self.model_dump_json(indent=indent, by_alias=True, exclude_none=True)
