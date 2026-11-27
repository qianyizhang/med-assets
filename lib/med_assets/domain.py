"""Typed semantic graph and lifecycle records for asset governance.

This module validates relationships without assuming a fixed anatomical depth
or equating a selectable part with an independently maintained asset.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable

class RelationType(StrEnum):
    PART_OF="part_of"
    IS_A="is_a"
    ARTICULATES_WITH="articulates_with"
    ATTACHES_TO="attaches_to"
    LOCATED_IN="located_in"
    INNERVATES="innervates"
    SUPPLIED_BY="supplied_by"
    DRAINS_TO="drains_to"
    PRODUCES="produces"
    PARTICIPATES_IN="participates_in"
    CONNECTED_TO="connected_to"
    REGISTERED_TO="registered_to"
    DERIVED_FROM="derived_from"
    COMPOSED_FROM="composed_from"
    SUPERSEDES="supersedes"

HIERARCHICAL={RelationType.PART_OF,RelationType.IS_A}
ASSET_STATES={"provisional","active","deprecated","retired"}
FRAME_STATES={"native","registered","rigidly_placed","fitted","illustrative","unregistered","unknown"}

@dataclass(frozen=True)
class Concept:
    concept_id:str
    label:str
    aliases:tuple[str,...]=()

@dataclass(frozen=True)
class ConceptRelation:
    subject:str
    predicate:RelationType
    object:str
    evidence:str|None=None

@dataclass(frozen=True)
class SourceSubject:
    subject_id:str
    source_id:str
    description:str
    frame_id:str|None=None

@dataclass(frozen=True)
class SpatialFrame:
    frame_id:str
    units:str
    axes:tuple[str,str,str]
    laterality:str
    subject_id:str|None=None

@dataclass(frozen=True)
class FrameTransform:
    transform_id:str
    source_frame:str
    target_frame:str
    relationship:str
    matrix:tuple[float,...]|None=None
    evidence:str|None=None
    limitations:tuple[str,...]=()

@dataclass(frozen=True)
class Source:
    source_id:str
    title:str
    source_type:str
    locator:str|None=None
    revision:str|None=None
    license_id:str|None=None
    attribution:str|None=None

@dataclass(frozen=True)
class NamedPart:
    part_id:str
    label:str
    concept_ids:tuple[str,...]
    selectors:tuple[str,...]=()
    selectable:bool=True
    context_only:bool=False

@dataclass(frozen=True)
class GeometryVariant:
    variant_id:str
    part_id:str
    subject_id:str|None
    frame_id:str
    physical_scale:str
    pose_id:str|None=None
    geometry_digest:str|None=None
    status:str="provisional"

@dataclass(frozen=True)
class Export:
    export_id:str
    path:str
    sha256:str|None
    bytes:int|None
    format:str
    part_ids:tuple[str,...]=()

@dataclass(frozen=True)
class Revision:
    revision_id:str
    status:str
    source_ids:tuple[str,...]
    exports:tuple[Export,...]
    recipe_path:str|None=None

@dataclass(frozen=True)
class Asset:
    asset_id:str
    title:str
    kind:str
    owner:str
    status:str
    concept_ids:tuple[str,...]
    source_ids:tuple[str,...]
    parts:tuple[NamedPart,...]
    revisions:tuple[Revision,...]

@dataclass(frozen=True)
class CompositionMember:
    asset_id:str
    revision_id:str
    part_ids:tuple[str,...]=()
    transform_id:str|None=None
    role:str="content"

@dataclass(frozen=True)
class Composition:
    composition_id:str
    title:str
    owner:str
    members:tuple[CompositionMember,...]
    reusable:bool=False

@dataclass(frozen=True)
class Requirement:
    requirement_id:str
    use_case_id:str
    kind:str
    description:str
    concept_ids:tuple[str,...]=()
    required_capabilities:tuple[str,...]=()
    status:str="open"

@dataclass(frozen=True)
class TeachingUse:
    use_id:str
    consumer_id:str
    asset_id:str
    revision_id:str
    export_id:str
    part_ids:tuple[str,...]
    requirement_ids:tuple[str,...]
    status:str="provisional"

@dataclass(frozen=True)
class GovernanceGraph:
    concepts:tuple[Concept,...]
    relations:tuple[ConceptRelation,...]
    sources:tuple[Source,...]=()
    subjects:tuple[SourceSubject,...]=()
    frames:tuple[SpatialFrame,...]=()
    transforms:tuple[FrameTransform,...]=()

    def validate(self)->None:
        concepts={x.concept_id for x in self.concepts}
        if len(concepts)!=len(self.concepts): raise ValueError("Duplicate concept identity")
        sources={x.source_id for x in self.sources}
        if len(sources)!=len(self.sources): raise ValueError("Duplicate source identity")
        subjects={x.subject_id for x in self.subjects}
        frames={x.frame_id for x in self.frames}
        if len(subjects)!=len(self.subjects) or len(frames)!=len(self.frames):
            raise ValueError("Duplicate subject or frame identity")
        if any(x.source_id not in sources for x in self.subjects):
            raise ValueError("Source subject references an unknown source")
        if any(x.frame_id is not None and x.frame_id not in frames for x in self.subjects):
            raise ValueError("Source subject references an unknown frame")
        if any(x.subject_id is not None and x.subject_id not in subjects for x in self.frames):
            raise ValueError("Spatial frame references an unknown subject")
        transform_ids={x.transform_id for x in self.transforms}
        if len(transform_ids)!=len(self.transforms): raise ValueError("Duplicate transform identity")
        for transform in self.transforms:
            if transform.source_frame not in frames or transform.target_frame not in frames:
                raise ValueError("Transform references an unknown frame")
            if transform.matrix is not None and len(transform.matrix)!=16:
                raise ValueError("A frame transform matrix must contain 16 values")
        seen=set(); parents={}
        for edge in self.relations:
            if edge.subject not in concepts or edge.object not in concepts:
                raise ValueError(f"Concept relation references unknown concept: {edge}")
            key=(edge.subject,edge.predicate,edge.object)
            if key in seen: raise ValueError(f"Duplicate concept relation: {key}")
            seen.add(key)
            if edge.predicate in HIERARCHICAL:
                parents.setdefault(edge.subject,[]).append(edge.object)
        visiting=set();visited=set()
        def visit(node):
            if node in visiting: raise ValueError(f"Cycle in hierarchical concept graph at {node}")
            if node in visited: return
            visiting.add(node)
            for parent in parents.get(node,[]): visit(parent)
            visiting.remove(node);visited.add(node)
        for node in concepts: visit(node)

def validate_asset(asset:Asset, graph:GovernanceGraph)->None:
    if asset.status not in ASSET_STATES: raise ValueError(f"Invalid asset status: {asset.status}")
    if not asset.asset_id or not asset.owner: raise ValueError("Asset identity and owner are required")
    concept_ids={x.concept_id for x in graph.concepts}
    source_ids={x.source_id for x in graph.sources}
    if not set(asset.concept_ids)<=concept_ids: raise ValueError("Asset references unknown anatomical concepts")
    if not set(asset.source_ids)<=source_ids: raise ValueError("Asset references unknown provenance sources")
    part_ids={x.part_id for x in asset.parts}
    if len(part_ids)!=len(asset.parts): raise ValueError("Duplicate named part identity")
    for part in asset.parts:
        if not set(part.concept_ids)<=concept_ids: raise ValueError(f"Part references unknown concept: {part.part_id}")
        if part.selectable and part.context_only: raise ValueError("A context-only part cannot be marked selectable")
    revision_ids={x.revision_id for x in asset.revisions}
    if len(revision_ids)!=len(asset.revisions): raise ValueError("Duplicate revision identity")
    for revision in asset.revisions:
        if revision.status not in ASSET_STATES: raise ValueError("Invalid revision status")
        if not set(revision.source_ids)<=source_ids: raise ValueError("Revision references unknown source")
        export_ids={x.export_id for x in revision.exports}
        if len(export_ids)!=len(revision.exports): raise ValueError("Duplicate export identity")
        for export in revision.exports:
            if not set(export.part_ids)<=part_ids: raise ValueError("Export references unknown named part")
            if export.bytes is not None and export.bytes<0: raise ValueError("Negative export size")

def validate_composition(composition:Composition,assets:Iterable[Asset],transforms:Iterable[FrameTransform])->None:
    by_id={x.asset_id:x for x in assets}; transform_ids={x.transform_id for x in transforms}
    if not composition.members: raise ValueError("Composition requires at least one member")
    for member in composition.members:
        asset=by_id.get(member.asset_id)
        if asset is None: raise ValueError(f"Unknown composition asset: {member.asset_id}")
        revision=next((x for x in asset.revisions if x.revision_id==member.revision_id),None)
        if revision is None: raise ValueError(f"Unknown composition revision: {member.revision_id}")
        available={part for export in revision.exports for part in export.part_ids}
        if member.part_ids and not set(member.part_ids)<=available:
            raise ValueError(f"Composition requests parts unavailable in pinned revision: {member.asset_id}")
        if member.transform_id is not None and member.transform_id not in transform_ids:
            raise ValueError(f"Composition references unknown transform: {member.transform_id}")
