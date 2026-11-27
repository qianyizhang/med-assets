"""Controlled, optimistic-concurrency lifecycle operations for package-owned assets."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from .governance import GovernanceError, impact, owner_path
from .governance_ultrasound import build_catalog
from .governance_migration import _atomic

ACTIONS = {"refine", "assess", "qualify", "adopt", "promote", "deprecate", "retire", "archive"}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"Invalid lifecycle JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceError("Lifecycle payload must be an object")
    return value

def _append(rows: list, row: dict, key: str, label: str) -> None:
    identity = row.get(key)
    if not isinstance(identity, str) or not identity.strip():
        raise GovernanceError(f"{label} requires stable {key}")
    old = next((x for x in rows if isinstance(x, dict) and x.get(key) == identity), None)
    if old == row:
        return
    if old is not None:
        raise GovernanceError(f"Conflicting {label} identity: {identity}")
    rows.append(row)

def _revision(record: dict, revision_id: str) -> dict:
    rows = [x for x in record["revisions"] if x.get("revisionId") == revision_id]
    if len(rows) != 1:
        raise GovernanceError(f"Expected exactly one revision {revision_id}")
    return rows[0]

def _verify_evidence(repo: Path, rows: list) -> None:
    if not isinstance(rows, list) or not rows:
        raise GovernanceError("Evidence must be a non-empty list of path/digest records")
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) or len(row.get("sha256", "")) != 64:
            raise GovernanceError("Evidence entries require repository path and SHA-256")
        path = owner_path(repo, row["path"])
        data = path.read_bytes()
        if data.startswith(b"version https://git-lfs.github.com/spec/"):
            raise GovernanceError(f"Evidence is not hydrated: {row['path']}")
        if _sha(data) != row["sha256"]:
            raise GovernanceError(f"Evidence digest mismatch: {row['path']}")

def _validate(record: dict) -> None:
    required = {"schemaVersion","assetId","title","kind","status","owner","concepts","sources","parts","revisions","artifacts","exports","uses","retirement","unresolved"}
    if set(record) != required or record.get("schemaVersion") != 1:
        raise GovernanceError("Invalid asset.record.json schema v1")
    if record["status"] not in {"provisional","active","deprecated","retired"}:
        raise GovernanceError("Invalid asset status")
    for field in ("concepts","sources","parts","revisions","artifacts","exports","uses","unresolved"):
        if not isinstance(record[field], list):
            raise GovernanceError(f"Record field {field} must be an array")
    parts = [x.get("partId") for x in record["parts"]]
    if len(parts) != len(set(parts)) or any(not x for x in parts):
        raise GovernanceError("Named part IDs must be unique and non-empty")
    revisions = [x.get("revisionId") for x in record["revisions"]]
    if len(revisions) != len(set(revisions)) or any(not x for x in revisions):
        raise GovernanceError("Revision IDs must be unique and non-empty")
    for rev in record["revisions"]:
        if not set(rev.get("partIds", [])) <= set(parts):
            raise GovernanceError(f"Revision {rev.get('revisionId')} references unknown parts")
        for export in rev.get("exports", []):
            if not isinstance(export.get("path"), str) or len(export.get("sha256", "")) != 64 or type(export.get("bytes")) is not int or export["bytes"] < 0:
                raise GovernanceError("Revision export requires path, SHA-256 and non-negative size")
    uses = [x.get("useId") for x in record["uses"]]
    if len(uses) != len(set(uses)):
        raise GovernanceError("Teaching-use IDs must be unique")

def _affected_consumers(catalog, record: dict) -> list:
    package_path = record["owner"]
    by_id = {}
    for consumer in catalog.consumers:
        evidence = consumer.evidence
        paths = list(evidence.get("sourcePaths", [])) + list(evidence.get("framePaths", [])) + list(evidence.get("artifactPaths", []))
        paths += [row.get("path") for row in evidence.get("assetPins", []) if isinstance(row, dict)]
        paths += [row.get("exportPath") for row in evidence.get("assetBindings", {}).values() if isinstance(row, dict)]
        paths += [row.get("path") for row in evidence.get("artifactPins", []) if isinstance(row, dict)]
        if isinstance(evidence.get("export"), dict):
            paths.append(evidence["export"].get("path"))
        matched = [path for path in paths if isinstance(path, str) and (path == package_path or path.startswith(package_path + "/"))]
        if matched:
            by_id[consumer.consumer_id] = {"consumerId":consumer.consumer_id,"domain":consumer.domain,
                "kind":consumer.kind,"title":consumer.title,"matchedPaths":list(dict.fromkeys(matched)),"matchedParts":[]}
    for use in record.get("uses", []):
        consumer_id = use.get("consumerId")
        if consumer_id:
            row = by_id.setdefault(consumer_id, {"consumerId":consumer_id,"domain":"governance-use",
                "kind":"revision-pinned-adoption","title":consumer_id,"matchedPaths":[],"matchedParts":[]})
            if use.get("exportPath"):
                row["matchedPaths"] = list(dict.fromkeys([*row["matchedPaths"], use["exportPath"]]))
            row["matchedParts"] = list(dict.fromkeys([*row["matchedParts"], *use.get("partIds", [])]))
    return sorted(by_id.values(), key=lambda row: row["consumerId"])

def _mutate(repo: Path, record: dict, action: str, payload: dict, catalog) -> dict:
    out = json.loads(json.dumps(record))
    if action == "refine":
        fields = {"concepts":"conceptId", "sources":"sourceId", "parts":"partId", "revisions":"revisionId"}
        changes = payload.get("set", {})
        if not isinstance(changes, dict) or set(changes)-set(fields):
            raise GovernanceError("refine set accepts concepts/sources/parts/revisions arrays")
        for field, key in fields.items():
            if field in changes:
                if not isinstance(changes[field], list): raise GovernanceError(f"{field} must be an array")
                for row in changes[field]: _append(out[field], row, key, field)
        resolved = payload.get("resolveUnresolved", [])
        added = payload.get("addUnresolved", [])
        if not isinstance(resolved, list) or not isinstance(added, list):
            raise GovernanceError("resolveUnresolved and addUnresolved must be arrays")
        for issue in resolved:
            if issue not in out["unresolved"]:
                raise GovernanceError(f"Cannot resolve an issue not present in the record: {issue}")
            out["unresolved"].remove(issue)
        for issue in added:
            if not isinstance(issue, str) or not issue.strip():
                raise GovernanceError("New unresolved issues must be non-empty strings")
            if issue not in out["unresolved"]:
                out["unresolved"].append(issue)
        if not changes and not resolved and not added:
            raise GovernanceError("refine requires a metadata change or an explicit unresolved disposition")
    elif action in {"assess", "qualify"}:
        key = "assessment" if action == "assess" else "qualification"
        row = payload.get(key)
        if not isinstance(row, dict): raise GovernanceError(f"{action} requires {key} object")
        required = ("assessmentId" if action == "assess" else "qualificationId", "scope", "reviewer", "assessedAt", "evidence")
        if any(not row.get(k) for k in required):
            raise GovernanceError(f"{action} requires scope, reviewer, date, identity and evidence")
        _verify_evidence(repo, row["evidence"])
        if action == "qualify":
            if row.get("decision") != "qualified":
                raise GovernanceError("Qualification decision must be qualified")
            use_id = payload.get("useId")
            if use_id:
                use = next((x for x in out["uses"] if x.get("useId") == use_id), None)
                if use is None: raise GovernanceError(f"Unknown teaching use: {use_id}")
                _append(use.setdefault("qualifications", []), row, "qualificationId", "qualification")
                use["status"] = "qualified"
            else:
                rev = _revision(out, payload.get("revisionId", ""))
                _append(rev.setdefault("qualifications", []), row, "qualificationId", "qualification")
        else:
            rev = _revision(out, payload.get("revisionId", ""))
            _append(rev.setdefault("assessments", []), row, "assessmentId", "assessment")
    elif action == "adopt":
        use = payload.get("use")
        if not isinstance(use, dict): raise GovernanceError("adopt requires use object")
        required = ("useId","consumerId","revisionId","exportPath","sha256","bytes","partIds","requirementIds")
        if any(k not in use for k in required): raise GovernanceError("Adoption must pin consumer, revision, export, digest, size, parts and requirements")
        rev = _revision(out, use["revisionId"])
        export = next((x for x in rev.get("exports", []) if x.get("path") == use["exportPath"]), None)
        if not export or export.get("sha256") != use["sha256"] or export.get("bytes") != use["bytes"]:
            raise GovernanceError("Adoption export does not match pinned revision identity")
        if not use["partIds"] or not use["requirementIds"] or not set(use["partIds"]) <= set(rev.get("partIds", [])):
            raise GovernanceError("Adoption requires exact revision parts and requirements")
        if not any(x.consumer_id == use["consumerId"] for x in catalog.consumers):
            raise GovernanceError(f"Unknown consumer: {use['consumerId']}")
        _append(out["uses"], {**use, "status":"provisional"}, "useId", "teaching use")
    elif action == "promote":
        rev = _revision(out, payload.get("revisionId", ""))
        if not rev.get("qualifications") or out["unresolved"] or not out["concepts"] or not out["sources"] or not rev.get("partIds") or not rev.get("exports"):
            raise GovernanceError("Promotion requires resolved governance, concepts, sources, parts, exports and qualification")
        for export in rev["exports"]:
            path = owner_path(repo, export["path"])
            data = path.read_bytes()
            if _sha(data) != export["sha256"] or len(data) != export["bytes"]:
                raise GovernanceError(f"Export bytes do not match revision pin: {export['path']}")
        rev["status"] = "active"
        out["status"] = "active"
    elif action == "deprecate":
        out["status"] = "deprecated"
    elif action == "retire":
        readers = {x["consumerId"] for x in _affected_consumers(catalog, out)}
        dispositions = payload.get("readerDisposition")
        if not payload.get("reason") or not payload.get("recordedAt") or not isinstance(dispositions, dict) or set(dispositions) != readers:
            raise GovernanceError("Retirement requires reason, date and disposition for every indexed reader")
        if any(v not in {"migrated","frozen","withdrawn"} for v in dispositions.values()):
            raise GovernanceError("Reader disposition must be migrated, frozen or withdrawn")
        out["status"] = "retired"
        out["retirement"] = {"reason":payload["reason"],"recordedAt":payload["recordedAt"],"readerDisposition":dispositions,"physicalDeletion":False}
    elif action == "archive":
        retirement = out.get("retirement")
        if out["status"] != "retired" or not isinstance(retirement, dict):
            raise GovernanceError("Only retired assets can be archived")
        if "frozen" in retirement.get("readerDisposition", {}).values():
            raise GovernanceError("Frozen readers block archival")
        if not payload.get("archivedAt") or not payload.get("archiveLocation"):
            raise GovernanceError("Archive requires date and location metadata")
        retirement["archive"] = {"archivedAt":payload["archivedAt"],"location":payload["archiveLocation"]}
    _validate(out)
    return out

def create_lifecycle_plan(repo: Path, asset_id: str, action: str, payload_path: Path) -> dict:
    if action not in ACTIONS: raise GovernanceError(f"Unsupported lifecycle action: {action}")
    repo = repo.resolve()
    catalog = build_catalog(repo)
    package = next((x for x in catalog.packages if x.candidate_id == asset_id), None)
    if package is None or not package.record_path: raise GovernanceError(f"No package-owned asset record: {asset_id}")
    path = owner_path(repo, package.record_path)
    before_bytes = path.read_bytes()
    before = json.loads(before_bytes)
    payload = _read(payload_path)
    after = _mutate(repo, before, action, payload, catalog)
    after_bytes = (json.dumps(after, ensure_ascii=False, indent=2) + "\n").encode()
    return {"schemaVersion":1,"intent":"asset-lifecycle","action":action,"repository":str(repo),
        "assetId":asset_id,"recordPath":package.record_path,"sourceHashes":catalog.source_hashes,
        "expectedRecordSha256":_sha(before_bytes),"afterRecordSha256":_sha(after_bytes),
        "before":before,"after":after,"payload":payload,
        "affectedConsumers":_affected_consumers(catalog, before),
        "requiredChecks":["record-schema","source-preconditions","consumer-impact","idempotent-apply"],
        "physicalDeletion":False,"publication":False}

def apply_lifecycle_plan(repo: Path, plan_path: Path) -> dict:
    repo = repo.resolve()
    plan = _read(plan_path)
    if plan.get("schemaVersion") != 1 or plan.get("intent") != "asset-lifecycle" or plan.get("action") not in ACTIONS:
        raise GovernanceError("Unsupported lifecycle plan")
    if Path(plan.get("repository","")).resolve() != repo: raise GovernanceError("Plan belongs to another checkout")
    path = owner_path(repo, plan.get("recordPath",""))
    current = path.read_bytes()
    if _sha(current) == plan.get("afterRecordSha256"):
        return {"status":"already-applied","recordPath":plan["recordPath"]}
    if _sha(current) != plan.get("expectedRecordSha256"): raise GovernanceError("Lifecycle target changed; regenerate plan")
    catalog = build_catalog(repo)
    if catalog.source_hashes != plan.get("sourceHashes"): raise GovernanceError("Lifecycle inputs changed; regenerate plan")
    before = json.loads(current)
    if before.get("assetId") != plan.get("assetId"): raise GovernanceError("Asset identity changed")
    expected = _mutate(repo, before, plan["action"], plan.get("payload",{}), catalog)
    if expected != plan.get("after"): raise GovernanceError("Plan after-state does not match action and payload")
    _validate(expected)
    encoded = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode()
    if _sha(encoded) != plan.get("afterRecordSha256"): raise GovernanceError("Plan after-state digest mismatch")
    _atomic(path, encoded)
    return {"status":"applied","recordPath":plan["recordPath"],"sha256":plan["afterRecordSha256"]}
