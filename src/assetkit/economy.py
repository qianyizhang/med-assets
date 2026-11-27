"""Delivery economy analysis, merge/split/overlay recommendations, impact, and resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .model import Asset, AssetKitError, Catalog, Consumer, Export, Revision


@dataclass(frozen=True)
class BudgetPolicy:
    """Soft and hard caps governing delivery economy."""

    export_bytes_soft: int = 1_500_000  # 1.5 MB
    export_bytes_hard: int = 4_000_000  # 4.0 MB
    export_tris_soft: int = 50_000
    export_tris_hard: int = 150_000
    consumer_bytes_soft: int = 5_000_000  # 5.0 MB
    consumer_bytes_hard: int = 12_000_000  # 12.0 MB
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
    action: str  # split-export | merge-bundle | over-budget | underutilized | unused-export
    target: str
    severity: str  # info | warn | hard
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


def _export_index(catalog: Catalog) -> dict[tuple[str, str, str], tuple[Asset, Revision, Export]]:
    index: dict[tuple[str, str, str], tuple[Asset, Revision, Export]] = {}
    for asset in catalog.assets:
        for rev in asset.revisions:
            for exp in rev.exports:
                index[(asset.id, rev.id, exp.id)] = (asset, rev, exp)
    return index


def analyze_economy(catalog: Catalog, policy: BudgetPolicy | None = None) -> EconomyReport:
    """Compute per-consumer load/utilization metrics, asset reuse, and merge/split advice."""
    policy = policy or BudgetPolicy()
    index = _export_index(catalog)
    asset_reuse: dict[str, set[str]] = {a.id: set() for a in catalog.assets}
    export_reuse: dict[str, set[str]] = {
        f"{a.id}@{r.id}:{e.id}": set()
        for a in catalog.assets
        for r in a.revisions
        for e in r.exports
    }

    metrics: list[UseCaseMetrics] = []
    recs: list[Recommendation] = []

    # Check individual runtime delivery export budgets (skip editable-master source files)
    for (aid, rid, eid), (_, _, exp) in sorted(index.items()):
        if exp.role == "editable-master":
            continue
        key = f"{aid}@{rid}:{eid}"
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
                        metrics={"triangles": exp.triangles, "hardCap": policy.export_tris_hard},
                    )
                )
            elif exp.triangles > policy.export_tris_soft:
                recs.append(
                    Recommendation(
                        action="over-budget",
                        target=key,
                        severity="warn",
                        reason=f"Export exceeds soft triangle cap ({exp.triangles} > {policy.export_tris_soft})",
                        metrics={"triangles": exp.triangles, "softCap": policy.export_tris_soft},
                    )
                )

    for consumer in catalog.consumers:
        loaded_keys: dict[tuple[str, str, str], set[str]] = {}
        for pin in consumer.pins:
            key = (pin.asset_id, pin.revision_id, pin.export_id)
            used = loaded_keys.setdefault(key, set())
            used.update(pin.parts)
            asset_reuse.setdefault(pin.asset_id, set()).add(consumer.id)
            export_reuse.setdefault(f"{pin.asset_id}@{pin.revision_id}:{pin.export_id}", set()).add(
                consumer.id
            )

        total_bytes = 0
        total_tris = 0
        used_parts_count = 0
        total_parts_count = 0
        used_part_bytes = 0
        measurable_part_bytes = 0

        for key, used_parts in loaded_keys.items():
            entry = index.get(key)
            if entry is None:
                continue
            _, _, exp = entry
            if exp.bytes is not None:
                total_bytes += exp.bytes
            if exp.triangles is not None:
                total_tris += exp.triangles
            if exp.parts:
                total_parts_count += len(exp.parts)
                if not used_parts:
                    # Pinning the whole export without part filter means all parts are used.
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
            round(used_part_bytes / measurable_part_bytes, 4) if measurable_part_bytes > 0 else None
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

        if part_util is not None and total_parts_count > 1 and part_util < policy.min_utilization:
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


def impact(catalog: Catalog, target: str) -> dict[str, Any]:
    """Trace every Consumer, Review, and Selection affected by an asset id, export key, or path."""
    matched_assets: set[str] = set()
    matched_paths: set[str] = set()

    for asset in catalog.assets:
        if target in {asset.id, asset.owner_dir}:
            matched_assets.add(asset.id)
        for rev in asset.revisions:
            for exp in rev.exports:
                export_key = f"{asset.id}@{rev.id}:{exp.id}"
                if target in {asset.id, asset.owner_dir, export_key, exp.path}:
                    matched_assets.add(asset.id)
                    matched_paths.add(exp.path)

    if not matched_assets and not matched_paths:
        # Still allow tracing raw export paths referenced by reviews/selections
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
        for c in catalog.consumers
        if any(
            p.asset_id in matched_assets or f"{p.asset_id}@{p.revision_id}:{p.export_id}" == target
            for p in c.pins
        )
    ]

    affected_reviews = [
        asdict(r)
        for r in catalog.reviews
        if r.export_path in matched_paths or (r.asset_id in matched_assets if r.asset_id else False)
    ]
    affected_selections = [
        asdict(s)
        for s in catalog.selections
        if s.export_path in matched_paths or (s.asset_id in matched_assets if s.asset_id else False)
    ]

    return {
        "target": target,
        "matchedAssets": sorted(matched_assets),
        "matchedExportPaths": sorted(matched_paths),
        "consumers": affected_consumers,
        "reviews": affected_reviews,
        "selections": affected_selections,
    }


def resolve(
    catalog: Catalog,
    consumer_id: str,
    requirement_id: str | None = None,
) -> dict[str, Any]:
    """Resolve candidate Assets/Exports/Parts for a Consumer's requirements.

    Never promotes a candidate to 'qualified' without explicit Review evidence.
    """
    consumer: Consumer | None = next((c for c in catalog.consumers if c.id == consumer_id), None)
    if consumer is None:
        raise AssetKitError(f"Unknown consumer: {consumer_id}")

    reqs = (
        [r for r in consumer.requirements if r.id == requirement_id]
        if requirement_id is not None
        else list(consumer.requirements)
    )
    if requirement_id is not None and not reqs:
        raise AssetKitError(f"Unknown requirement '{requirement_id}' on '{consumer_id}'")

    reviews_by_path: dict[str, list[str]] = {}
    for review in catalog.reviews:
        reviews_by_path.setdefault(review.export_path, []).append(review.status)

    results = []
    for req in reqs:
        # Expand concept targets via hierarchical descendants so e.g. 'vertebral-column'
        # can surface 'L3-vertebra' candidates while labeling the match basis honestly.
        expanded_concepts = set(req.concepts)
        for cid in req.concepts:
            expanded_concepts.update(catalog.concepts.descendants(cid))

        exact_candidates = []
        concept_candidates = []
        incompatible_subject = []

        for asset in catalog.assets:
            for rev in asset.revisions:
                for exp in rev.exports:
                    if req.variant and exp.variant != req.variant:
                        continue
                    # Check part-level selector/concept matches
                    for part in exp.parts:
                        prov = part.provenance or rev.provenance
                        tokens = {part.id, *part.selectors}
                        selector_hit = bool(req.parts and (set(req.parts) & tokens))
                        concept_hit = bool(
                            expanded_concepts and (set(part.concepts) & expanded_concepts)
                        )
                        if not selector_hit and not concept_hit:
                            continue
                        candidate = {
                            "assetId": asset.id,
                            "revisionId": rev.id,
                            "exportId": exp.id,
                            "exportPath": exp.path,
                            "partId": part.id,
                            "label": part.label,
                            "variant": exp.variant,
                            "subject": prov.subject,
                            "registration": prov.registration,
                            "reviewStatuses": sorted(set(reviews_by_path.get(exp.path, ()))),
                            "qualified": "accepted" in reviews_by_path.get(exp.path, ()),
                        }
                        if req.subject and prov.subject and prov.subject != req.subject:
                            candidate["note"] = (
                                f"Foreign subject '{prov.subject}' != required '{req.subject}'; "
                                "requires explicit registration/illustrative pin if reused."
                            )
                            incompatible_subject.append(candidate)
                        elif selector_hit and (not req.subject or prov.subject == req.subject):
                            candidate["matchBasis"] = "exact-selector"
                            exact_candidates.append(candidate)
                        else:
                            candidate["matchBasis"] = (
                                "concept-hierarchy"
                                if concept_hit
                                else "selector-unverified-subject"
                            )
                            concept_candidates.append(candidate)

                    # Also allow whole-asset concept match when no part matched
                    if expanded_concepts and (set(asset.concepts) & expanded_concepts):
                        prov = rev.provenance
                        candidate = {
                            "assetId": asset.id,
                            "revisionId": rev.id,
                            "exportId": exp.id,
                            "exportPath": exp.path,
                            "partId": None,
                            "label": asset.title,
                            "variant": exp.variant,
                            "subject": prov.subject,
                            "registration": prov.registration,
                            "reviewStatuses": sorted(set(reviews_by_path.get(exp.path, ()))),
                            "qualified": "accepted" in reviews_by_path.get(exp.path, ()),
                            "matchBasis": "asset-concept",
                        }
                        if req.subject and prov.subject and prov.subject != req.subject:
                            candidate["note"] = (
                                f"Foreign subject '{prov.subject}' != required '{req.subject}'."
                            )
                            incompatible_subject.append(candidate)
                        else:
                            concept_candidates.append(candidate)

        status = (
            "exact-candidate"
            if exact_candidates
            else "concept-candidate"
            if concept_candidates
            else "foreign-subject-only"
            if incompatible_subject
            else "unmatched"
        )
        results.append(
            {
                "requirementId": req.id,
                "status": status,
                "exactCandidates": exact_candidates,
                "conceptCandidates": concept_candidates,
                "foreignSubjectCandidates": incompatible_subject,
            }
        )

    return {"consumerId": consumer.id, "requirements": results}
