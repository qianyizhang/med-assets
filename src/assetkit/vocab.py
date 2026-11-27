"""Semantic context: polyhierarchical anatomical and clinical ConceptGraph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import AssetKitError
from .models import AssetModel

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


class Concept(AssetModel):
    id: str
    label: str
    aliases: tuple[str, ...] = ()


class ConceptEdge(AssetModel):
    subject: str
    predicate: str
    object: str
    evidence: str | None = None


@dataclass(frozen=True)
class ConceptGraph:
    """Polyhierarchical DAG of anatomical/clinical concepts decoupled from assets."""

    concepts: tuple[Concept, ...] = ()
    edges: tuple[ConceptEdge, ...] = ()

    @classmethod
    def load(cls, repo: Path) -> ConceptGraph:
        root = repo.resolve()
        concepts: list[Concept] = []
        edges: list[ConceptEdge] = []
        for candidate in (root / "concepts.json", root / "sources" / "concepts.json"):
            if not candidate.is_file():
                continue
            try:
                doc = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise AssetKitError(f"Invalid concepts file {candidate}: {exc}") from exc
            for row in doc.get("concepts", doc.get("nodes", [])):
                concepts.append(
                    Concept(
                        id=row["id"],
                        label=row.get("label", row["id"]),
                        aliases=tuple(row.get("aliases", ())),
                    )
                )
            for row in doc.get("edges", []):
                edges.append(
                    ConceptEdge(
                        subject=row["subject"],
                        predicate=row["predicate"],
                        object=row["object"],
                        evidence=row.get("evidence"),
                    )
                )
        return cls(concepts=tuple(concepts), edges=tuple(edges))

    @property
    def ids(self) -> set[str]:
        return {c.id for c in self.concepts}

    def validate(self) -> None:
        seen_ids: set[str] = set()
        for concept in self.concepts:
            if not concept.id.strip() or not concept.label.strip():
                raise AssetKitError(f"Concept requires non-empty id and label: {concept}")
            if concept.id in seen_ids:
                raise AssetKitError(f"Duplicate concept id '{concept.id}'")
            seen_ids.add(concept.id)

        seen_edges: set[tuple[str, str, str]] = set()
        parents: dict[str, list[str]] = {}
        for edge in self.edges:
            if edge.predicate not in EDGE_TYPES:
                raise AssetKitError(f"Unsupported concept edge predicate: {edge.predicate}")
            if edge.subject not in seen_ids or edge.object not in seen_ids:
                raise AssetKitError(f"Concept edge references unknown concept: {edge}")
            key = (edge.subject, edge.predicate, edge.object)
            if key in seen_edges:
                raise AssetKitError(f"Duplicate concept edge: {key}")
            seen_edges.add(key)
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

        for node in seen_ids:
            visit(node)

    def ancestors(self, concept_id: str) -> set[str]:
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

    def expand(
        self, concept_ids: tuple[str, ...] | set[str], include_descendants: bool = True
    ) -> set[str]:
        expanded = set(concept_ids)
        if include_descendants:
            for cid in list(expanded):
                expanded.update(self.descendants(cid))
        return expanded

    def related(self, concept_id: str, predicate: str | None = None) -> tuple[ConceptEdge, ...]:
        return tuple(
            e
            for e in self.edges
            if (e.subject == concept_id or e.object == concept_id)
            and (predicate is None or e.predicate == predicate)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [c.to_dict() for c in self.concepts],
            "edges": [e.to_dict() for e in self.edges],
        }
