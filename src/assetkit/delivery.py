"""Demand & packaging context: Consumers, RuntimeBundles, Resolution, Economy, and Impact."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .curation import CurationStore
from .errors import AssetKitError
from .registry import REGISTRATION_STATES, SKIP_DIRS, AssetRegistry
from .vocab import ConceptGraph

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


@dataclass(frozen=True)
class Requirement:
    """Machine-readable statement of what a Consumer needs."""

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
    """Explicit Consumer dependency on an exact Asset Export / Parts."""

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
class BudgetPolicy:
    """Soft and hard caps governing delivery economy."""

    export_bytes_soft: int = 1_500_000
    export_bytes_hard: int = 4_000_000
    export_tris_soft: int = 50_000
    export_tris_hard: int = 150_000
    consumer_bytes_soft: int = 5_000_000
    consumer_bytes_hard: int = 12_000_000
    consumer_loads_soft: int = 5
    consumer_loads_hard: int = 12
    min_utilization: float = 0.35


@dataclass(frozen=True)
class UseCaseMetrics:
    consumer_id: str
    title: str
    loads: int
    total_bytes: int
    total_triangles: int
    part_utilization: float | None
    byte_utilization: float | None
    open_gaps: int
    budget_flags: tuple[str, ...]


@dataclass(frozen=True)
class Recommendation:
    action: str  # split-export | merge-bundle | over-budget
    target: str
    severity: str  # warn | hard
    reason: str
    metrics: dict[str, Any]


@dataclass(frozen=True)
class EconomyReport:
    policy: BudgetPolicy
    consumer_metrics: tuple[UseCaseMetrics, ...]
    asset_reuse: dict[str, int]
    export_reuse: dict[str, int]
    recommendations: tuple[Recommendation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": asdict(self.policy),
            "summary": {
                "consumersEvaluated": len(self.consumer_metrics),
                "assetsReused": sum(1 for v in self.asset_reuse.values() if v > 1),
                "recommendations": len(self.recommendations),
                "hardViolations": sum(1 for r in self.recommendations if r.severity == "hard"),
            },
            "consumerMetrics": [asdict(m) for m in self.consumer_metrics],
            "assetReuse": dict(sorted(self.asset_reuse.items())),
            "exportReuse": dict(sorted(self.export_reuse.items())),
            "recommendations": [asdict(r) for r in self.recommendations],
        }


@dataclass(frozen=True)
class RuntimeBundle:
    """Resolved load list for a Consumer (exact files, parts, provenance, and limits)."""

    consumer_id: str
    title: str
    items: tuple[dict[str, Any], ...]
    total_bytes: int
    total_triangles: int
    open_gaps: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeliveryGraph:
    """Owns all Consumers, their Requirements/Pins, and delivery analysis."""

    consumers: tuple[Consumer, ...] = ()

    @classmethod
    def load(cls, repo: Path, *, include_legacy_adapters: bool = True) -> DeliveryGraph:
        root = repo.resolve()
        consumers = _load_native_consumers(root)
        if include_legacy_adapters:
            existing_ids = {c.id for c in consumers}
            consumers.extend(_project_legacy_consumers(root, existing_ids))
        return cls(tuple(consumers))

    def get(self, consumer_id: str) -> Consumer | None:
        return next((c for c in self.consumers if c.id == consumer_id), None)

    def validate(self, registry: AssetRegistry) -> list[str]:
        warnings: list[str] = []
        seen: set[str] = set()
        for consumer in self.consumers:
            if consumer.id in seen:
                raise AssetKitError(f"Duplicate consumer id '{consumer.id}'")
            seen.add(consumer.id)
            consumer.validate()
            for pin in consumer.pins:
                resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
                if resolved is None:
                    warnings.append(
                        f"Consumer '{consumer.id}' pin references unknown export "
                        f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                    )
                    continue
                _, _, exp = resolved
                if pin.sha256 and exp.sha256 and pin.sha256 != exp.sha256:
                    raise AssetKitError(
                        f"Pin sha256 mismatch for {consumer.id} -> "
                        f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}: "
                        f"{pin.sha256} != {exp.sha256}"
                    )
                if pin.parts:
                    known = {p.id for p in exp.parts}
                    if known:
                        missing = [p for p in pin.parts if p not in known]
                        if missing:
                            warnings.append(
                                f"Consumer '{consumer.id}' pin requests unknown parts "
                                f"{missing} on {pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                            )
        return warnings

    def bundle_for(self, consumer_id: str, registry: AssetRegistry) -> RuntimeBundle:
        consumer = self.get(consumer_id)
        if consumer is None:
            raise AssetKitError(f"Unknown consumer '{consumer_id}'")
        items: list[dict[str, Any]] = []
        total_bytes = 0
        total_tris = 0
        for pin in consumer.pins:
            resolved = registry.resolve_export(pin.asset_id, pin.revision_id, pin.export_id)
            if resolved is None:
                raise AssetKitError(
                    f"Consumer '{consumer_id}' references missing export "
                    f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}"
                )
            asset, rev, exp = resolved
            if exp.bytes is not None:
                total_bytes += exp.bytes
            if exp.triangles is not None:
                total_tris += exp.triangles
            selected_parts = [asdict(p) for p in exp.parts if not pin.parts or p.id in pin.parts]
            items.append(
                {
                    "assetId": asset.id,
                    "revisionId": rev.id,
                    "exportId": exp.id,
                    "path": exp.path,
                    "format": exp.format,
                    "variant": exp.variant,
                    "sha256": exp.sha256,
                    "bytes": exp.bytes,
                    "triangles": exp.triangles,
                    "storageStatus": exp.storage_status,
                    "registration": pin.registration,
                    "transform": list(pin.transform) if pin.transform else None,
                    "license": rev.provenance.license,
                    "subject": rev.provenance.subject,
                    "limits": list(pin.limits or rev.provenance.limits),
                    "parts": selected_parts,
                }
            )
        gaps = tuple(
            {
                "id": r.id,
                "description": r.description,
                "status": r.status,
                "concepts": list(r.concepts),
            }
            for r in consumer.requirements
            if r.status in {"open-gap", "rebuild-required"}
        )
        return RuntimeBundle(
            consumer_id=consumer.id,
            title=consumer.title,
            items=tuple(items),
            total_bytes=total_bytes,
            total_triangles=total_tris,
            open_gaps=gaps,
        )

    def open_gaps(self, prefix: str | None = None) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        for consumer in self.consumers:
            if prefix and not consumer.id.startswith(prefix):
                continue
            for req in consumer.requirements:
                if req.status in {"open-gap", "rebuild-required"}:
                    gaps.append(
                        {
                            "consumerId": consumer.id,
                            "consumerTitle": consumer.title,
                            "requirementId": req.id,
                            "status": req.status,
                            "description": req.description,
                            "concepts": list(req.concepts),
                            "parts": list(req.parts),
                            "subject": req.subject,
                        }
                    )
        return gaps

    def economy(self, registry: AssetRegistry, policy: BudgetPolicy | None = None) -> EconomyReport:
        policy = policy or BudgetPolicy()
        asset_reuse: dict[str, set[str]] = {a.id: set() for a in registry.assets}
        export_reuse: dict[str, set[str]] = {
            f"{a.id}@{r.id}:{e.id}": set() for a, r, e in registry.iter_exports()
        }
        metrics: list[UseCaseMetrics] = []
        recs: list[Recommendation] = []

        for asset, rev, exp in registry.iter_exports():
            if exp.role == "editable-master":
                continue
            key = f"{asset.id}@{rev.id}:{exp.id}"
            if exp.bytes is not None:
                if exp.bytes > policy.export_bytes_hard:
                    recs.append(
                        Recommendation(
                            action="split-export",
                            target=key,
                            severity="hard",
                            reason=f"Export exceeds hard byte cap ({exp.bytes} > {policy.export_bytes_hard})",
                            metrics={"bytes": exp.bytes, "hardCap": policy.export_bytes_hard},
                        )
                    )
                elif exp.bytes > policy.export_bytes_soft:
                    recs.append(
                        Recommendation(
                            action="split-export",
                            target=key,
                            severity="warn",
                            reason=f"Export exceeds soft byte cap ({exp.bytes} > {policy.export_bytes_soft})",
                            metrics={"bytes": exp.bytes, "softCap": policy.export_bytes_soft},
                        )
                    )
            if exp.triangles is not None:
                if exp.triangles > policy.export_tris_hard:
                    recs.append(
                        Recommendation(
                            action="over-budget",
                            target=key,
                            severity="hard",
                            reason=f"Export exceeds hard triangle cap ({exp.triangles} > {policy.export_tris_hard})",
                            metrics={
                                "triangles": exp.triangles,
                                "hardCap": policy.export_tris_hard,
                            },
                        )
                    )
                elif exp.triangles > policy.export_tris_soft:
                    recs.append(
                        Recommendation(
                            action="over-budget",
                            target=key,
                            severity="warn",
                            reason=f"Export exceeds soft triangle cap ({exp.triangles} > {policy.export_tris_soft})",
                            metrics={
                                "triangles": exp.triangles,
                                "softCap": policy.export_tris_soft,
                            },
                        )
                    )

        for consumer in self.consumers:
            loaded_keys: dict[tuple[str, str, str], set[str]] = {}
            for pin in consumer.pins:
                key = (pin.asset_id, pin.revision_id, pin.export_id)
                loaded_keys.setdefault(key, set()).update(pin.parts)
                asset_reuse.setdefault(pin.asset_id, set()).add(consumer.id)
                export_reuse.setdefault(
                    f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}", set()
                ).add(consumer.id)

            total_bytes = 0
            total_tris = 0
            used_parts_count = 0
            total_parts_count = 0
            used_part_bytes = 0
            measurable_part_bytes = 0

            for (aid, rid, eid), used_parts in loaded_keys.items():
                resolved = registry.resolve_export(aid, rid, eid)
                if resolved is None:
                    continue
                _, _, exp = resolved
                if exp.bytes is not None:
                    total_bytes += exp.bytes
                if exp.triangles is not None:
                    total_tris += exp.triangles
                if exp.parts:
                    total_parts_count += len(exp.parts)
                    if not used_parts:
                        used_parts_count += len(exp.parts)
                    else:
                        matched = [p for p in exp.parts if p.id in used_parts]
                        used_parts_count += len(matched)
                        if all(p.bytes is not None for p in exp.parts):
                            measurable_part_bytes += sum(p.bytes or 0 for p in exp.parts)
                            used_part_bytes += sum(p.bytes or 0 for p in matched)

            loads = len(loaded_keys)
            part_util = (
                round(used_parts_count / total_parts_count, 4) if total_parts_count > 0 else None
            )
            byte_util = (
                round(used_part_bytes / measurable_part_bytes, 4)
                if measurable_part_bytes > 0
                else None
            )
            open_gaps = sum(
                1 for r in consumer.requirements if r.status in {"open-gap", "rebuild-required"}
            )
            flags: list[str] = []
            if loads > policy.consumer_loads_hard:
                flags.append("loads-over-hard-cap")
                recs.append(
                    Recommendation(
                        action="merge-bundle",
                        target=consumer.id,
                        severity="hard",
                        reason=f"Consumer loads {loads} exports (hard cap {policy.consumer_loads_hard})",
                        metrics={"loads": loads, "hardCap": policy.consumer_loads_hard},
                    )
                )
            elif loads > policy.consumer_loads_soft:
                flags.append("loads-over-soft-cap")
                recs.append(
                    Recommendation(
                        action="merge-bundle",
                        target=consumer.id,
                        severity="warn",
                        reason=f"Consumer loads {loads} exports (soft cap {policy.consumer_loads_soft})",
                        metrics={"loads": loads, "softCap": policy.consumer_loads_soft},
                    )
                )
            if total_bytes > policy.consumer_bytes_hard:
                flags.append("bytes-over-hard-cap")
                recs.append(
                    Recommendation(
                        action="over-budget",
                        target=consumer.id,
                        severity="hard",
                        reason=f"Consumer loads {total_bytes} bytes (hard cap {policy.consumer_bytes_hard})",
                        metrics={"bytes": total_bytes, "hardCap": policy.consumer_bytes_hard},
                    )
                )
            elif total_bytes > policy.consumer_bytes_soft:
                flags.append("bytes-over-soft-cap")
            if (
                part_util is not None
                and total_parts_count > 1
                and part_util < policy.min_utilization
            ):
                flags.append("low-part-utilization")
                recs.append(
                    Recommendation(
                        action="split-export",
                        target=consumer.id,
                        severity="warn",
                        reason=(
                            f"Consumer uses only {part_util:.0%} of loaded parts "
                            f"({used_parts_count}/{total_parts_count}); consider a lighter base export + overlay"
                        ),
                        metrics={
                            "partUtilization": part_util,
                            "usedParts": used_parts_count,
                            "totalParts": total_parts_count,
                        },
                    )
                )
            if byte_util is not None and byte_util < policy.min_utilization:
                flags.append("low-byte-utilization")

            metrics.append(
                UseCaseMetrics(
                    consumer_id=consumer.id,
                    title=consumer.title,
                    loads=loads,
                    total_bytes=total_bytes,
                    total_triangles=total_tris,
                    part_utilization=part_util,
                    byte_utilization=byte_util,
                    open_gaps=open_gaps,
                    budget_flags=tuple(flags),
                )
            )

        return EconomyReport(
            policy=policy,
            consumer_metrics=tuple(metrics),
            asset_reuse={k: len(v) for k, v in asset_reuse.items()},
            export_reuse={k: len(v) for k, v in export_reuse.items()},
            recommendations=tuple(recs),
        )

    def impact(
        self, target: str, registry: AssetRegistry, curation: CurationStore
    ) -> dict[str, Any]:
        matched_assets, matched_paths = registry.match_target(target)
        if not matched_assets and not matched_paths:
            matched_paths.add(target)

        affected_consumers = [
            {
                "consumerId": c.id,
                "title": c.title,
                "kind": c.kind,
                "pins": [
                    asdict(p)
                    for p in c.pins
                    if p.asset_id in matched_assets
                    or f"{p.asset_id}@{p.revision_id}:{p.export_id}" == target
                ],
            }
            for c in self.consumers
            if any(
                p.asset_id in matched_assets
                or f"{p.asset_id}@{p.revision_id}:{p.export_id}" == target
                for p in c.pins
            )
        ]
        return {
            "target": target,
            "matchedAssets": sorted(matched_assets),
            "matchedExportPaths": sorted(matched_paths),
            "consumers": affected_consumers,
            "reviews": [asdict(r) for r in curation.reviews_for(matched_paths, matched_assets)],
            "selections": [
                asdict(s) for s in curation.selections_for(matched_paths, matched_assets)
            ],
        }

    def resolve(
        self,
        consumer_id: str,
        registry: AssetRegistry,
        vocab: ConceptGraph,
        curation: CurationStore,
        requirement_id: str | None = None,
    ) -> dict[str, Any]:
        consumer = self.get(consumer_id)
        if consumer is None:
            raise AssetKitError(f"Unknown consumer: {consumer_id}")
        reqs = (
            [r for r in consumer.requirements if r.id == requirement_id]
            if requirement_id is not None
            else list(consumer.requirements)
        )
        if requirement_id is not None and not reqs:
            raise AssetKitError(f"Unknown requirement '{requirement_id}' on '{consumer_id}'")

        results = []
        for req in reqs:
            expanded = vocab.expand(req.concepts)
            exact_candidates = []
            concept_candidates = []
            foreign_subject = []

            for asset, rev, exp in registry.iter_exports():
                if req.variant and exp.variant != req.variant:
                    continue
                qual = curation.qualification_for(exp.path, exp.sha256)
                for part in exp.parts:
                    prov = part.provenance or rev.provenance
                    tokens = {part.id, *part.selectors}
                    selector_hit = bool(req.parts and (set(req.parts) & tokens))
                    concept_hit = bool(expanded and (set(part.concepts) & expanded))
                    if not selector_hit and not concept_hit:
                        continue
                    cand = {
                        "assetId": asset.id,
                        "revisionId": rev.id,
                        "exportId": exp.id,
                        "exportPath": exp.path,
                        "partId": part.id,
                        "label": part.label,
                        "variant": exp.variant,
                        "subject": prov.subject,
                        "registration": prov.registration,
                        "reviewStatuses": list(qual.statuses),
                        "qualified": qual.qualified,
                    }
                    if req.subject and prov.subject and prov.subject != req.subject:
                        cand["note"] = (
                            f"Foreign subject '{prov.subject}' != required '{req.subject}'; "
                            "requires explicit registration/illustrative pin if reused."
                        )
                        foreign_subject.append(cand)
                    elif selector_hit and (not req.subject or prov.subject == req.subject):
                        cand["matchBasis"] = "exact-selector"
                        exact_candidates.append(cand)
                    else:
                        cand["matchBasis"] = (
                            "concept-hierarchy" if concept_hit else "selector-unverified-subject"
                        )
                        concept_candidates.append(cand)

                if expanded and (set(asset.concepts) & expanded):
                    prov = rev.provenance
                    cand = {
                        "assetId": asset.id,
                        "revisionId": rev.id,
                        "exportId": exp.id,
                        "exportPath": exp.path,
                        "partId": None,
                        "label": asset.title,
                        "variant": exp.variant,
                        "subject": prov.subject,
                        "registration": prov.registration,
                        "reviewStatuses": list(qual.statuses),
                        "qualified": qual.qualified,
                        "matchBasis": "asset-concept",
                    }
                    if req.subject and prov.subject and prov.subject != req.subject:
                        cand["note"] = (
                            f"Foreign subject '{prov.subject}' != required '{req.subject}'."
                        )
                        foreign_subject.append(cand)
                    else:
                        concept_candidates.append(cand)

            status = (
                "exact-candidate"
                if exact_candidates
                else "concept-candidate"
                if concept_candidates
                else "foreign-subject-only"
                if foreign_subject
                else "unmatched"
            )
            results.append(
                {
                    "requirementId": req.id,
                    "status": status,
                    "exactCandidates": exact_candidates,
                    "conceptCandidates": concept_candidates,
                    "foreignSubjectCandidates": foreign_subject,
                }
            )
        return {"consumerId": consumer.id, "requirements": results}

    def counts(self) -> dict[str, int]:
        return {
            "consumers": len(self.consumers),
            "requirements": sum(len(c.requirements) for c in self.consumers),
            "openGaps": sum(
                1
                for c in self.consumers
                for r in c.requirements
                if r.status in {"open-gap", "rebuild-required"}
            ),
            "pins": sum(len(c.pins) for c in self.consumers),
        }

    def to_dict(self) -> list[dict[str, Any]]:
        return [asdict(c) for c in self.consumers]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetKitError(f"Invalid JSON in {path}: {exc}") from exc


def _load_native_consumers(repo: Path) -> list[Consumer]:
    consumers: list[Consumer] = []
    for manifest in sorted(repo.rglob("consumer.json")):
        if any(part in SKIP_DIRS for part in manifest.relative_to(repo).parts):
            continue
        owner_path = manifest.resolve().relative_to(repo).as_posix()
        doc = _read_json(manifest)
        for row in doc.get("consumers", []):
            reqs = tuple(
                Requirement(
                    id=r["id"],
                    description=r.get("description", r["id"]),
                    status=r.get("status", "open-gap"),
                    concepts=tuple(r.get("concepts", (r["concept"],) if r.get("concept") else ())),
                    parts=tuple(r.get("parts", ())),
                    variant=r.get("variant"),
                    subject=r.get("subject"),
                    capabilities=tuple(r.get("capabilities", ())),
                )
                for r in row.get("requirements", [])
            )
            pins = tuple(
                Pin(
                    asset_id=p["asset"],
                    revision_id=p["revision"],
                    export_id=p["export"],
                    requirement_id=p.get("requirement"),
                    parts=tuple(p.get("parts", ())),
                    sha256=p.get("sha256"),
                    registration=p.get("registration", "unknown"),
                    transform=tuple(float(v) for v in p["transform"])
                    if p.get("transform") is not None
                    else None,
                    limits=tuple(p.get("limits", ())),
                )
                for p in row.get("pins", [])
            )
            consumers.append(
                Consumer(
                    id=row["id"],
                    title=row.get("title", row["id"]),
                    kind=row.get("kind", "other"),
                    owner_path=owner_path,
                    requirements=reqs,
                    pins=pins,
                    local_files=tuple(row.get("localFiles", ())),
                )
            )
    return consumers


def _project_legacy_consumers(repo: Path, existing_ids: set[str]) -> list[Consumer]:
    consumers: list[Consumer] = []
    stops_path = repo / "lessons/body-systems/reviewed-stops.json"
    if stops_path.is_file():
        doc = _read_json(stops_path)
        owner = stops_path.resolve().relative_to(repo).as_posix()
        for row in doc.get("stops", []):
            cid = f"body-systems:{row['system']}:{row['detail']}"
            if cid in existing_ids:
                continue
            existing_ids.add(cid)
            consumers.append(
                Consumer(
                    id=cid,
                    title=f"{str(row['system']).title()} · {row['detail']}",
                    kind="lesson-stop",
                    owner_path=owner,
                    requirements=(
                        Requirement(
                            id=row["detail"],
                            description=row["action"],
                            status="satisfied" if row.get("status") == "passed" else "provisional",
                        ),
                    ),
                )
            )

    us_dir = repo / "experiments/ultrasound-sweep"
    if us_dir.is_dir():
        for track_file in sorted(us_dir.glob("*-track*.json")):
            doc = _read_json(track_file)
            common = doc.get("common", {})
            owner = track_file.resolve().relative_to(repo).as_posix()
            for sweep in doc.get("sweeps", []):
                if not isinstance(sweep, dict) or not sweep.get("id"):
                    continue
                cid = f"ultrasound:sweep:{track_file.stem}:{sweep['id']}"
                if cid in existing_ids:
                    continue
                existing_ids.add(cid)
                case = sweep.get("case", common.get("case"))
                parts = tuple(
                    p for p in sweep.get("parts", common.get("parts", [])) if isinstance(p, str)
                )
                reqs = tuple(
                    Requirement(
                        id=f"part:{p}",
                        description=f"Ultrasound sweep anatomy part '{p}'",
                        status="provisional",
                        parts=(p,),
                        subject=case,
                    )
                    for p in parts
                )
                consumers.append(
                    Consumer(
                        id=cid,
                        title=sweep.get("title", sweep["id"]),
                        kind="ultrasound-sweep",
                        owner_path=owner,
                        requirements=reqs,
                    )
                )
    return consumers
