"""Enrich selector/path resolution with package-owned revision and qualification evidence."""
from __future__ import annotations
from pathlib import Path
from .governance import GovernanceError, resolve as resolve_candidates, owner_path, read_json

def _package(catalog, package_id):
    return next((x for x in catalog.packages if x.candidate_id == package_id), None)

def _details(catalog, package_id, part_id=None, export_path=None, consumer_id=None):
    package = _package(catalog, package_id)
    if package is None or not package.record_path:
        return {"recordStatus":"missing","revisionCandidates":[],"adoptions":[]}
    repo = Path(catalog.repository)
    record = read_json(owner_path(repo, package.record_path))
    parts = [x for x in record["parts"] if part_id is None or x.get("partId") == part_id]
    sources = record.get("sources", [])
    revisions = []
    for revision in record.get("revisions", []):
        revision_parts = set(revision.get("partIds", []))
        for part in parts:
            if part.get("partId") not in revision_parts:
                continue
            for export in revision.get("exports", []):
                if export_path and export.get("path") != export_path:
                    continue
                revisions.append({
                    "revisionId":revision.get("revisionId"),
                    "revisionStatus":revision.get("status"),
                    "partId":part.get("partId"),
                    "partSelectors":part.get("selectors", []),
                    "export":export,
                    "geometryDigest":export.get("sha256"),
                    "geometryBytes":export.get("bytes"),
                    "sourceIds":revision.get("sourceIds", []),
                    "sources":[x for x in sources if x.get("sourceId") in revision.get("sourceIds", record.get("sourceIds", []))],
                    "frameEvidence":{k:part.get(k) for k in ("frame","sourceFrame","transformId","registration","registrationEvidence") if k in part},
                    "qualificationStatus":"qualified" if revision.get("qualifications") else "unqualified",
                    "qualifications":revision.get("qualifications", []),
                })
    adoptions=[]
    for use in record.get("uses", []):
        if consumer_id and use.get("consumerId") != consumer_id:
            continue
        if part_id and part_id not in use.get("partIds", []):
            continue
        if export_path and use.get("exportPath") != export_path:
            continue
        adoptions.append({
            "useId":use.get("useId"),"consumerId":use.get("consumerId"),
            "revisionId":use.get("revisionId"),"exportPath":use.get("exportPath"),
            "sha256":use.get("sha256"),"bytes":use.get("bytes"),
            "partIds":use.get("partIds",[]),"requirementIds":use.get("requirementIds",[]),
            "status":use.get("status","provisional"),"qualifications":use.get("qualifications",[]),
        })
    return {"recordStatus":record.get("status"),"assetId":record.get("assetId"),
        "owner":record.get("owner"),"sourceDeclarations":sources,
        "revisionCandidates":revisions,"adoptions":adoptions}

def resolve_detailed(catalog, identity: str, part_id: str | None = None):
    result = resolve_candidates(catalog, identity, part_id)
    consumer = result.get("consumer", {})
    consumer_id = consumer.get("consumer_id")
    if result.get("parts"):
        for requested in result["parts"]:
            for group in ("exactCandidates","nearMatches","incompatibleCandidates"):
                for candidate in requested.get(group, []):
                    details = _details(catalog,candidate.get("packageId"),candidate.get("partId"),consumer_id=consumer_id)
                    candidate["maintenance"] = details
                    candidate["registrationStatus"] = candidate.get("registrationStatus","not-established")
                    candidate["qualificationStatus"] = "qualified" if any(
                        x.get("qualificationStatus") == "qualified" for x in details["revisionCandidates"]) else "not-qualified"
    for key in ("exactExportCandidates","nearMatches"):
        for candidate in result.get(key, []):
            details = _details(catalog,candidate.get("packageId"),export_path=candidate.get("exportPath"),consumer_id=consumer_id)
            candidate["maintenance"] = details
    if result.get("bindings"):
        for binding in result["bindings"]:
            details = _details(catalog,binding.get("assetId"),export_path=(binding.get("export") or {}).get("path"),
                consumer_id=consumer_id)
            binding["maintenance"] = details
    result["resolutionSemantics"] = {
        "exactPathOrSelector":"candidate identity only",
        "revisionPin":"only established by a matching package-owned revision export",
        "qualification":"scoped evidence attached to the exact revision or consumer adoption",
        "registration":"reported only when package-owned frame/transform evidence exists",
        "rights":"source declarations are exposed; compatibility still requires consumer review",
    }
    return result
