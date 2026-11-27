"""AssetKit: DDD-structured medical teaching asset management library."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import blobs, build, curation, delivery, registry, vocab
from .blobs import BlobRef, MeshStats, inspect_mesh, normalize_path, verify
from .build import (
    BuildResult,
    BuildRunner,
    BuildSpec,
    SyncDiff,
    plan_build,
    run_build,
    sync_manifest,
)
from .curation import CurationStore, QualificationStatus, Review, Selection
from .delivery import (
    BudgetPolicy,
    Consumer,
    DeliveryGraph,
    EconomyReport,
    Pin,
    Recommendation,
    Requirement,
    RuntimeBundle,
    UseCaseMetrics,
)
from .errors import AssetKitError
from .registry import Asset, AssetRegistry, Export, Part, Provenance, Revision
from .vocab import Concept, ConceptEdge, ConceptGraph


@dataclass(frozen=True)
class Workspace:
    """Thin facade composing the bounded contexts for a repository checkout."""

    repository: Path
    vocab: ConceptGraph
    registry: AssetRegistry
    delivery: DeliveryGraph
    curation: CurationStore

    @classmethod
    def load(
        cls,
        repo: Path,
        *,
        include_legacy_adapters: bool = True,
        inspect_glbs: bool = False,
    ) -> Workspace:
        root = repo.resolve()
        return cls(
            repository=root,
            vocab=ConceptGraph.load(root),
            registry=AssetRegistry.load(
                root,
                include_legacy_adapters=include_legacy_adapters,
                inspect_glbs=inspect_glbs,
            ),
            delivery=DeliveryGraph.load(root, include_legacy_adapters=include_legacy_adapters),
            curation=CurationStore.load(root, include_legacy_adapters=include_legacy_adapters),
        )

    def validate(self) -> list[str]:
        self.vocab.validate()
        warnings = self.registry.validate(self.vocab)
        warnings.extend(self.delivery.validate(self.registry))
        self.curation.validate()
        return warnings

    def counts(self) -> dict[str, int]:
        return {
            "concepts": len(self.vocab.concepts),
            "conceptEdges": len(self.vocab.edges),
            **self.registry.counts(),
            **self.delivery.counts(),
            "reviews": len(self.curation.reviews),
            "selections": len(self.curation.selections),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "repository": str(self.repository),
            "counts": self.counts(),
            "vocab": self.vocab.to_dict(),
            "assets": self.registry.to_dict(),
            "consumers": self.delivery.to_dict(),
            **self.curation.to_dict(),
        }


__all__ = [
    "Asset",
    "AssetKitError",
    "AssetRegistry",
    "BlobRef",
    "BudgetPolicy",
    "BuildResult",
    "BuildRunner",
    "BuildSpec",
    "Concept",
    "ConceptEdge",
    "ConceptGraph",
    "Consumer",
    "CurationStore",
    "DeliveryGraph",
    "EconomyReport",
    "Export",
    "MeshStats",
    "Part",
    "Pin",
    "Provenance",
    "QualificationStatus",
    "Recommendation",
    "Requirement",
    "Review",
    "Revision",
    "RuntimeBundle",
    "Selection",
    "SyncDiff",
    "UseCaseMetrics",
    "Workspace",
    "blobs",
    "build",
    "curation",
    "delivery",
    "inspect_mesh",
    "normalize_path",
    "plan_build",
    "registry",
    "run_build",
    "sync_manifest",
    "verify",
    "vocab",
]
