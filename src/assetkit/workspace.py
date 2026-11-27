"""Repository workspace and typed results for cross-module asset queries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .curation import (
    CurationStore,
    GalleryProjection,
    Qualification,
    QualificationStatus,
    R2SyncItem,
    Review,
    Selection,
)
from .delivery import (
    BudgetPolicy,
    Consumer,
    DeliveryGraph,
    EconomyReport,
    ImpactResult,
    ResolveResult,
    RuntimeBundle,
)
from .errors import AssetKitError
from .models import AssetModel
from .registry import AssetRegistry, CoordinateFrame, Part, Provenance, VoxelGrid
from .vocab import ConceptGraph


class AssetSummary(AssetModel):
    id: str
    title: str
    kind: str
    owner_dir: str
    source_manifest: str | None = None
    revisions: tuple[str, ...] = ()


class PartSummary(AssetModel):
    asset_id: str
    revision_id: str
    export_id: str
    export_path: str
    part_id: str
    label: str
    selectors: tuple[str, ...] = ()


class ConsumerSummary(AssetModel):
    id: str
    title: str
    kind: str
    owner_path: str


class FindResult(AssetModel):
    query: str
    assets: tuple[AssetSummary, ...] = ()
    parts: tuple[PartSummary, ...] = ()
    consumers: tuple[ConsumerSummary, ...] = ()


class AssetHeader(AssetModel):
    id: str
    title: str
    kind: str
    owner_dir: str
    source_manifest: str | None = None
    families: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    status: str | None = None


class ShowExportView(AssetModel):
    id: str
    path: str
    format: str
    role: str
    variant: str
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None
    storage_status: str
    parts: tuple[Part, ...] = ()
    voxel_grid: VoxelGrid | None = None
    frame: CoordinateFrame | None = None
    qualification: QualificationStatus


class ShowRevisionView(AssetModel):
    id: str
    status: str
    recipe: str | None = None
    provenance: Provenance
    capabilities: tuple[str, ...] = ()
    exports: tuple[ShowExportView, ...] = ()
    frame: CoordinateFrame | None = None


class TaskAdoptionView(AssetModel):
    use_id: str
    consumer_id: str
    revision_id: str
    export_path: str
    sha256: str | None = None
    part_ids: tuple[str, ...] = ()
    requirement_ids: tuple[str, ...] = ()
    adoption_status: str
    qualified: bool
    qualification_decisions: tuple[str, ...] = ()
    assessments: tuple[Review, ...] = ()


class ShowAssetResult(AssetModel):
    target: str
    found: Literal[True] = True
    status: Literal["ok"] = "ok"
    kind: Literal["asset"] = "asset"
    asset: AssetHeader
    revisions: tuple[ShowRevisionView, ...] = ()
    tasks: tuple[TaskAdoptionView, ...] = ()
    reviews: tuple[Review, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    selections: tuple[Selection, ...] = ()


class ShowConsumerResult(AssetModel):
    target: str
    found: Literal[True] = True
    status: Literal["ok"] = "ok"
    kind: Literal["consumer"] = "consumer"
    consumer: Consumer


class UnknownTargetResult(AssetModel):
    target: str
    found: Literal[False] = False
    status: Literal["unknown-target"] = "unknown-target"


ShowResult = ShowAssetResult | ShowConsumerResult | UnknownTargetResult


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
            "qualifications": len(self.curation.qualifications),
            "adoptions": len(self.curation.adoptions),
            "selections": len(self.curation.selections),
        }

    def resolve(self, consumer_id: str, requirement_id: str | None = None) -> ResolveResult:
        return self.delivery.resolve(
            consumer_id, self.registry, self.vocab, self.curation, requirement_id
        )

    def impact(self, target: str) -> ImpactResult:
        return self.delivery.impact(target, self.registry, self.curation)

    def bundle(self, consumer_id: str) -> RuntimeBundle:
        return self.delivery.bundle_for(consumer_id, self.registry)

    def economy(self, policy: BudgetPolicy | None = None) -> EconomyReport:
        return self.delivery.economy(self.registry, policy)

    def compile_gallery(self) -> GalleryProjection:
        return self.curation.compile_gallery(self.registry, self.delivery)

    def plan_r2_sync(self) -> list[R2SyncItem]:
        return self.curation.plan_r2_sync(self.registry, self.delivery)

    def find(self, query: str) -> FindResult:
        """Discover assets, parts, or consumers matching a case-insensitive query."""
        needle = query.strip().lower()
        assets_hit: list[AssetSummary] = []
        parts_hit: list[PartSummary] = []
        consumers_hit: list[ConsumerSummary] = []

        for asset in self.registry.assets:
            haystack = " ".join(
                (asset.id, asset.title, asset.owner_dir, *asset.concepts, *asset.families)
            ).lower()
            if not needle or needle in haystack:
                assets_hit.append(
                    AssetSummary(
                        id=asset.id,
                        title=asset.title,
                        kind=asset.kind,
                        owner_dir=asset.owner_dir,
                        source_manifest=asset.source_manifest,
                        revisions=tuple(r.id for r in asset.revisions),
                    )
                )
            for rev in asset.revisions:
                for exp in rev.exports:
                    for part in exp.parts:
                        phay = " ".join(
                            (part.id, part.label, *part.selectors, *part.concepts)
                        ).lower()
                        if needle and needle in phay:
                            parts_hit.append(
                                PartSummary(
                                    asset_id=asset.id,
                                    revision_id=rev.id,
                                    export_id=exp.id,
                                    export_path=exp.path,
                                    part_id=part.id,
                                    label=part.label,
                                    selectors=part.selectors,
                                )
                            )

        for consumer in self.delivery.consumers:
            chay = " ".join(
                (consumer.id, consumer.title, consumer.kind, consumer.owner_path)
            ).lower()
            if not needle or needle in chay:
                consumers_hit.append(
                    ConsumerSummary(
                        id=consumer.id,
                        title=consumer.title,
                        kind=consumer.kind,
                        owner_path=consumer.owner_path,
                    )
                )

        return FindResult(
            query=query,
            assets=tuple(assets_hit),
            parts=tuple(parts_hit),
            consumers=tuple(consumers_hit),
        )

    def show(self, target: str) -> ShowResult:
        """Inspect a maintained asset (or consumer) with its exports, assessments, and decisions."""
        matched_assets, _ = self.registry.match_target(target)
        if len(matched_assets) > 1:
            raise AssetKitError(f"Ambiguous target {target!r}; use one of {sorted(matched_assets)}")
        if matched_assets:
            asset = self.registry.get(next(iter(matched_assets)))
            if asset is not None:
                asset_paths = {exp.path for rev in asset.revisions for exp in rev.exports}
                revisions_out: list[ShowRevisionView] = []
                for rev in asset.revisions:
                    exports_out: list[ShowExportView] = []
                    for exp in rev.exports:
                        qual = self.curation.qualification_for(
                            exp.path, exp.sha256, asset_id=asset.id, revision_id=rev.id
                        )
                        exports_out.append(
                            ShowExportView(
                                id=exp.id,
                                path=exp.path,
                                format=exp.format,
                                role=exp.role,
                                variant=exp.variant,
                                sha256=exp.sha256,
                                bytes=exp.bytes,
                                triangles=exp.triangles,
                                storage_status=exp.storage_status,
                                parts=exp.parts,
                                voxel_grid=exp.voxel_grid,
                                frame=exp.frame,
                                qualification=qual,
                            )
                        )
                    revisions_out.append(
                        ShowRevisionView(
                            id=rev.id,
                            status=rev.status,
                            recipe=rev.recipe,
                            provenance=rev.provenance,
                            capabilities=rev.capabilities,
                            exports=tuple(exports_out),
                            frame=rev.frame,
                        )
                    )

                adoptions = self.curation.adoptions_for(asset_paths, {asset.id})
                tasks_out: list[TaskAdoptionView] = []
                for adop in adoptions:
                    task_qual = self.curation.qualification_for(
                        adop.export_path,
                        adop.sha256,
                        use_id=adop.use_id,
                        asset_id=asset.id,
                        revision_id=adop.revision_id,
                    )
                    matching_ids = set(task_qual.review_ids)
                    matching_reviews = tuple(
                        r for r in self.curation.reviews if r.id in matching_ids
                    )
                    tasks_out.append(
                        TaskAdoptionView(
                            use_id=adop.use_id,
                            consumer_id=adop.consumer_id,
                            revision_id=adop.revision_id,
                            export_path=adop.export_path,
                            sha256=adop.sha256,
                            part_ids=adop.part_ids,
                            requirement_ids=adop.requirement_ids,
                            adoption_status=adop.status,
                            qualified=task_qual.qualified,
                            qualification_decisions=task_qual.qualification_decisions,
                            assessments=matching_reviews,
                        )
                    )

                return ShowAssetResult(
                    target=target,
                    asset=AssetHeader(
                        id=asset.id,
                        title=asset.title,
                        kind=asset.kind,
                        owner_dir=asset.owner_dir,
                        source_manifest=asset.source_manifest,
                        families=asset.families,
                        concepts=asset.concepts,
                        unresolved=asset.unresolved,
                        status=asset.status,
                    ),
                    revisions=tuple(revisions_out),
                    tasks=tuple(tasks_out),
                    reviews=self.curation.reviews_for(asset_paths, {asset.id}),
                    qualifications=self.curation.qualifications_for(asset_paths, {asset.id}),
                    selections=self.curation.selections_for(asset_paths, {asset.id}),
                )

        consumer = self.delivery.get(target)
        if consumer is not None:
            return ShowConsumerResult(target=target, consumer=consumer)

        return UnknownTargetResult(target=target)

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
