"""Core domain model and structural invariants for AssetKit.

Six first-class entities:
  Concept, Asset, Revision, Consumer, Review, Selection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

ASSET_KINDS = frozenset({"model", "assembly", "diagram", "rig", "generator", "detail"})
REVISION_STATUSES = frozenset({"provisional", "active", "deprecated", "retired"})
REGISTRATION_STATES = frozenset(
    {"native", "registered", "fitted", "illustrative", "synthetic", "unknown"}
)
CONSUMER_KINDS = frozenset(
    {
        "lesson-stop",
        "ultrasound-sweep",
        "ultrasound-tour",
        "ultrasound-case",
        "scene",
        "site",
        "other",
    }
)
REQUIREMENT_STATUSES = frozenset({"satisfied", "provisional", "open-gap", "rebuild-required"})
REVIEW_STATUSES = frozenset({"accepted", "provisional", "blocked", "rejected"})
HIERARCHICAL_EDGES = frozenset({"part_of", "is_a"})
EDGE_TYPES = frozenset(
    {
        "part_of",
        "is_a",
        "located_in",
        "produces",
        "participates_in",
        "supplied_by",
        "drains_to",
        "innervates",
        "articulates_with",
        "attaches_to",
        "connected_to",
    }
)


class AssetKitError(ValueError):
    """Raised when catalog data violates domain or storage invariants."""


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptEdge:
    subject: str
    predicate: str
    object: str
    evidence: str | None = None


@dataclass(frozen=True)
class ConceptGraph:
    concepts: tuple[Concept, ...] = ()
    edges: tuple[ConceptEdge, ...] = ()

    def validate(self) -> None:
        ids = {c.id for c in self.concepts}
        if len(ids) != len(self.concepts):
            raise AssetKitError("Duplicate concept id")
        for c in self.concepts:
            if not c.id.strip() or not c.label.strip():
                raise AssetKitError(f"Concept requires non-empty id and label: {c}")

        seen: set[tuple[str, str, str]] = set()
        parents: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.predicate not in EDGE_TYPES:
                raise AssetKitError(f"Unsupported concept edge predicate: {edge.predicate}")
            if edge.subject not in ids or edge.object not in ids:
                raise AssetKitError(f"Concept edge references unknown concept: {edge}")
            key = (edge.subject, edge.predicate, edge.object)
            if key in seen:
                raise AssetKitError(f"Duplicate concept edge: {key}")
            seen.add(key)
            if edge.predicate in HIERARCHICAL_EDGES:
                parents.setdefault(edge.subject, []).append(edge.object)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise AssetKitError(f"Cycle in hierarchical concept graph at '{node}'")
            if node in visited:
                return
            visiting.add(node)
            for parent in parents.get(node, ()):
                visit(parent)
            visiting.remove(node)
            visited.add(node)

        for node in ids:
            visit(node)

    def ancestors(self, concept_id: str) -> set[str]:
        """Return all hierarchical ancestors (part_of / is_a) of concept_id."""
        parents: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.predicate in HIERARCHICAL_EDGES:
                parents.setdefault(edge.subject, []).append(edge.object)
        found: set[str] = set()
        stack = list(parents.get(concept_id, ()))
        while stack:
            curr = stack.pop()
            if curr not in found:
                found.add(curr)
                stack.extend(parents.get(curr, ()))
        return found

    def descendants(self, concept_id: str) -> set[str]:
        """Return all hierarchical descendants (part_of / is_a) of concept_id."""
        children: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.predicate in HIERARCHICAL_EDGES:
                children.setdefault(edge.object, []).append(edge.subject)
        found: set[str] = set()
        stack = list(children.get(concept_id, ()))
        while stack:
            curr = stack.pop()
            if curr not in found:
                found.add(curr)
                stack.extend(children.get(curr, ()))
        return found


@dataclass(frozen=True)
class Provenance:
    """Source, subject, spatial frame, and registration honesty record.

    Attached as a default on Revision and optionally overridden per Part or Pin
    so hybrid/multi-source assets and foreign overlays remain explicit.
    """

    source: str | None = None
    subject: str | None = None
    license: str | None = None
    units: str | None = None
    axes: tuple[str, ...] = ()
    laterality: str | None = None
    registration: str = "unknown"
    transform: tuple[float, ...] | None = None
    derived_from: str | None = None
    limits: tuple[str, ...] = ()

    def validate(self, context: str) -> None:
        if self.registration not in REGISTRATION_STATES:
            raise AssetKitError(f"Invalid registration '{self.registration}' in {context}")
        if self.transform is not None and len(self.transform) != 16:
            raise AssetKitError(f"Transform matrix must have 16 values in {context}")


@dataclass(frozen=True)
class Part:
    """An addressable sub-structure inside an Export."""

    id: str
    label: str
    selectors: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    kind: str = "mesh-node"
    selectable: bool = True
    context_only: bool = False
    bytes: int | None = None
    triangles: int | None = None
    provenance: Provenance | None = None

    def validate(self, context: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Part requires non-empty id in {context}")
        if self.selectable and self.context_only:
            raise AssetKitError(
                f"Part '{self.id}' in {context} cannot be both selectable and context_only"
            )
        if self.bytes is not None and self.bytes < 0:
            raise AssetKitError(f"Negative bytes on part '{self.id}' in {context}")
        if self.triangles is not None and self.triangles < 0:
            raise AssetKitError(f"Negative triangles on part '{self.id}' in {context}")
        if self.provenance is not None:
            self.provenance.validate(f"{context}:part:{self.id}")


@dataclass(frozen=True)
class Export:
    """A concrete deliverable payload produced by a Revision."""

    id: str
    path: str
    format: str
    role: str = "teaching-mesh"
    variant: str = "normal"
    sha256: str | None = None
    bytes: int | None = None
    triangles: int | None = None
    storage_status: str = "unverified"
    parts: tuple[Part, ...] = ()

    def validate(self, context: str) -> None:
        if not self.id.strip() or not self.path.strip():
            raise AssetKitError(f"Export requires non-empty id and path in {context}")
        if self.bytes is not None and self.bytes < 0:
            raise AssetKitError(f"Negative export bytes on '{self.id}' in {context}")
        if self.triangles is not None and self.triangles < 0:
            raise AssetKitError(f"Negative export triangles on '{self.id}' in {context}")
        seen_parts: set[str] = set()
        for part in self.parts:
            if part.id in seen_parts:
                raise AssetKitError(f"Duplicate part id '{part.id}' in {context}:{self.id}")
            seen_parts.add(part.id)
            part.validate(f"{context}:{self.id}")


@dataclass(frozen=True)
class Revision:
    """An immutable iteration of an Asset."""

    id: str
    status: str = "provisional"
    recipe: str | None = None
    provenance: Provenance = field(default_factory=Provenance)
    capabilities: tuple[str, ...] = ()
    exports: tuple[Export, ...] = ()

    def validate(self, asset_id: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Revision requires non-empty id in asset '{asset_id}'")
        if self.status not in REVISION_STATUSES:
            raise AssetKitError(f"Invalid revision status '{self.status}' in {asset_id}@{self.id}")
        self.provenance.validate(f"{asset_id}@{self.id}")
        seen: set[str] = set()
        for exp in self.exports:
            if exp.id in seen:
                raise AssetKitError(f"Duplicate export id '{exp.id}' in {asset_id}@{self.id}")
            seen.add(exp.id)
            exp.validate(f"{asset_id}@{self.id}")


@dataclass(frozen=True)
class Asset:
    """An independently maintained reusable work (authoring unit)."""

    id: str
    title: str
    kind: str
    owner_dir: str
    families: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    revisions: tuple[Revision, ...] = ()
    source_manifest: str | None = None

    def validate(self) -> None:
        if not self.id.strip() or not self.owner_dir.strip():
            raise AssetKitError(f"Asset requires non-empty id and owner_dir: {self}")
        if self.kind not in ASSET_KINDS:
            raise AssetKitError(f"Invalid asset kind '{self.kind}' on '{self.id}'")
        seen: set[str] = set()
        for rev in self.revisions:
            if rev.id in seen:
                raise AssetKitError(f"Duplicate revision '{rev.id}' on asset '{self.id}'")
            seen.add(rev.id)
            rev.validate(self.id)


@dataclass(frozen=True)
class Requirement:
    """A machine-readable statement of what a Consumer needs."""

    id: str
    description: str
    status: str = "open-gap"
    concepts: tuple[str, ...] = ()
    parts: tuple[str, ...] = ()
    variant: str | None = None
    subject: str | None = None
    capabilities: tuple[str, ...] = ()

    def validate(self, consumer_id: str) -> None:
        if not self.id.strip():
            raise AssetKitError(f"Requirement requires non-empty id in '{consumer_id}'")
        if self.status not in REQUIREMENT_STATUSES:
            raise AssetKitError(
                f"Invalid requirement status '{self.status}' in {consumer_id}:{self.id}"
            )


@dataclass(frozen=True)
class Pin:
    """An explicit Consumer dependency on an exact Asset Export / Parts."""

    asset_id: str
    revision_id: str
    export_id: str
    requirement_id: str | None = None
    parts: tuple[str, ...] = ()
    sha256: str | None = None
    registration: str = "unknown"
    transform: tuple[float, ...] | None = None
    limits: tuple[str, ...] = ()

    def validate(self, consumer_id: str) -> None:
        if not self.asset_id.strip() or not self.revision_id.strip() or not self.export_id.strip():
            raise AssetKitError(f"Incomplete pin in consumer '{consumer_id}': {self}")
        if self.registration not in REGISTRATION_STATES:
            raise AssetKitError(
                f"Invalid pin registration '{self.registration}' in consumer '{consumer_id}'"
            )
        if self.transform is not None and len(self.transform) != 16:
            raise AssetKitError(f"Pin transform must have 16 values in '{consumer_id}'")


@dataclass(frozen=True)
class Consumer:
    """An authored teaching experience or delivery surface."""

    id: str
    title: str
    kind: str
    owner_path: str
    requirements: tuple[Requirement, ...] = ()
    pins: tuple[Pin, ...] = ()
    local_files: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id.strip() or not self.owner_path.strip():
            raise AssetKitError(f"Consumer requires non-empty id and owner_path: {self}")
        if self.kind not in CONSUMER_KINDS:
            raise AssetKitError(f"Invalid consumer kind '{self.kind}' on '{self.id}'")
        req_ids: set[str] = set()
        for req in self.requirements:
            if req.id in req_ids:
                raise AssetKitError(f"Duplicate requirement '{req.id}' in '{self.id}'")
            req_ids.add(req.id)
            req.validate(self.id)
        for pin in self.pins:
            pin.validate(self.id)
            if pin.requirement_id is not None and pin.requirement_id not in req_ids:
                raise AssetKitError(
                    f"Pin references unknown requirement '{pin.requirement_id}' in '{self.id}'"
                )


@dataclass(frozen=True)
class Review:
    """Dated, immutable qualification evidence bound to an exact Export or Part."""

    id: str
    export_path: str
    task_id: str
    task: str
    status: str
    owner_path: str
    sha256: str | None = None
    asset_id: str | None = None
    part_id: str | None = None
    scores: dict[str, Any] = field(default_factory=dict)
    limits: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id.strip() or not self.export_path.strip():
            raise AssetKitError(f"Review requires non-empty id and export_path: {self}")
        if self.status not in REVIEW_STATUSES:
            raise AssetKitError(f"Invalid review status '{self.status}' on '{self.id}'")


@dataclass(frozen=True)
class Selection:
    """Explicit editorial/release choice separating curation from qualification."""

    id: str
    kind: str  # "teaching-default" | "recommended-revision" | "release-admitted"
    export_path: str
    owner_path: str
    collection_id: str | None = None
    family_id: str | None = None
    task_id: str | None = None
    review_id: str | None = None
    asset_id: str | None = None
    revision_id: str | None = None


@dataclass(frozen=True)
class Catalog:
    """Complete read-model projection of a repository."""

    repository: str
    concepts: ConceptGraph = field(default_factory=ConceptGraph)
    assets: tuple[Asset, ...] = ()
    consumers: tuple[Consumer, ...] = ()
    reviews: tuple[Review, ...] = ()
    selections: tuple[Selection, ...] = ()

    def validate(self) -> list[str]:
        """Validate structural invariants and return non-fatal warnings."""
        self.concepts.validate()
        known_concepts = {c.id for c in self.concepts.concepts}
        warnings: list[str] = []

        asset_map: dict[str, Asset] = {}
        export_index: dict[tuple[str, str, str], Export] = {}
        for asset in self.assets:
            if asset.id in asset_map:
                raise AssetKitError(f"Duplicate asset id '{asset.id}'")
            asset.validate()
            asset_map[asset.id] = asset
            if known_concepts:
                for cid in asset.concepts:
                    if cid not in known_concepts:
                        warnings.append(f"Asset '{asset.id}' references undeclared concept '{cid}'")
            for rev in asset.revisions:
                for exp in rev.exports:
                    export_index[(asset.id, rev.id, exp.id)] = exp

        seen_consumers: set[str] = set()
        for consumer in self.consumers:
            if consumer.id in seen_consumers:
                raise AssetKitError(f"Duplicate consumer id '{consumer.id}'")
            seen_consumers.add(consumer.id)
            consumer.validate()
            for pin in consumer.pins:
                key = (pin.asset_id, pin.revision_id, pin.export_id)
                exp = export_index.get(key)
                if exp is None:
                    warnings.append(
                        f"Consumer '{consumer.id}' pin references unknown export "
                        f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                    )
                else:
                    if pin.sha256 and exp.sha256 and pin.sha256 != exp.sha256:
                        raise AssetKitError(
                            f"Pin sha256 mismatch for {consumer.id} -> {key}: "
                            f"{pin.sha256} != {exp.sha256}"
                        )
                    if pin.parts:
                        known_parts = {p.id for p in exp.parts}
                        if known_parts:
                            missing = [p for p in pin.parts if p not in known_parts]
                            if missing:
                                warnings.append(
                                    f"Consumer '{consumer.id}' pin requests unknown parts "
                                    f"{missing} on {key}"
                                )

        seen_reviews: set[str] = set()
        for review in self.reviews:
            if review.id in seen_reviews:
                raise AssetKitError(f"Duplicate review id '{review.id}'")
            seen_reviews.add(review.id)
            review.validate()

        return warnings

    def summary_counts(self) -> dict[str, int]:
        revisions = sum(len(a.revisions) for a in self.assets)
        exports = sum(len(r.exports) for a in self.assets for r in a.revisions)
        parts = sum(len(e.parts) for a in self.assets for r in a.revisions for e in r.exports)
        requirements = sum(len(c.requirements) for c in self.consumers)
        pins = sum(len(c.pins) for c in self.consumers)
        open_gaps = sum(
            1
            for c in self.consumers
            for req in c.requirements
            if req.status in {"open-gap", "rebuild-required"}
        )
        return {
            "concepts": len(self.concepts.concepts),
            "conceptEdges": len(self.concepts.edges),
            "assets": len(self.assets),
            "revisions": revisions,
            "exports": exports,
            "parts": parts,
            "consumers": len(self.consumers),
            "requirements": requirements,
            "openGaps": open_gaps,
            "pins": pins,
            "reviews": len(self.reviews),
            "selections": len(self.selections),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "repository": self.repository,
            "counts": self.summary_counts(),
            "concepts": {
                "nodes": [asdict(c) for c in self.concepts.concepts],
                "edges": [asdict(e) for e in self.concepts.edges],
            },
            "assets": [asdict(a) for a in self.assets],
            "consumers": [asdict(c) for c in self.consumers],
            "reviews": [asdict(r) for r in self.reviews],
            "selections": [asdict(s) for s in self.selections],
        }
