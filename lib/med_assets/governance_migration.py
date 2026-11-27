"""Reviewed package-record backfill and scoped Git LFS hydration."""
from __future__ import annotations
import hashlib,json,os,subprocess
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from .artifacts import declared_identity, source_path
from .governance import GovernanceError,owner_path
from .governance_ultrasound import build_catalog

def _sha(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _atomic(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(dir=path.parent,prefix=".asset-governance-",delete=False) as stream:
        temp=Path(stream.name)
        try:
            stream.write(data);stream.flush();os.fsync(stream.fileno());os.replace(temp,path)
        finally: temp.unlink(missing_ok=True)

def create_backfill_plan(repo:Path)->dict[str,Any]:
    catalog=build_catalog(repo); proposals=[]
    record_hashes={k:v for k,v in catalog.source_hashes.items() if k.endswith("/asset.record.json")}
    source_hashes={k:v for k,v in catalog.source_hashes.items() if not k.endswith("/asset.record.json")}
    for item in catalog.packages:
        if item.record_path: continue
        export_identities={}
        for export in item.exports:
            digest,size=declared_identity(repo,export)
            export_identities[export]={"sha256":digest,"bytes":size}
        proposals.append({"candidateId":item.candidate_id,"packagePath":item.path,"title":item.title,
          "kind":item.kind,"readmeSha256":item.readme_sha256,"exports":list(item.exports),
          "manifests":list(item.manifests),"artifacts":[asdict(x) for x in item.artifacts],
          "parts":[asdict(x) for x in item.parts],
          "exportIdentities":export_identities,
          "decision":"defer","assetId":None,"owner":item.path,
          "notes":"Package discovery is not proof of an independent asset lineage. Confirm granularity and ownership."})
    return {"schemaVersion":1,"intent":"asset-record-backfill","repository":str(repo.resolve()),
      "sourceHashes":source_hashes,"recordHashes":record_hashes,
      "existingAssetIds":[item.candidate_id for item in catalog.packages if item.record_path],
      "proposals":proposals,
      "consumerCoverage":{"bodySystemsStops":sum(x.domain=="body-systems" for x in catalog.consumers),
        "ultrasoundRequirements":sum(x.domain=="ultrasound-anatomy" for x in catalog.consumers)}}

def write_backfill_plan(repo:Path,destination:Path):
    plan=create_backfill_plan(repo);_atomic(destination,(json.dumps(plan,ensure_ascii=False,indent=2)+"\n").encode());return plan

def _record_document(proposal:dict[str,Any],asset_id:str):
    owner=source_path(proposal["owner"])
    parts=proposal.get("parts",[])
    parts_by_id={}
    for part in parts:
        part_id=part.get("part_id")
        if not isinstance(part_id,str) or not part_id.strip():
            raise GovernanceError("Backfill part requires a stable part_id")
        merged=parts_by_id.setdefault(part_id,{"partId":part_id,"label":part.get("label",part_id),
            "selectors":[],"declarations":[]})
        if part.get("label") and part.get("label")!=merged["label"]:
            merged.setdefault("alternateLabels",[]).append(part["label"])
        for selector in part.get("selectors",[]):
            if selector not in merged["selectors"]: merged["selectors"].append(selector)
        merged["declarations"].append(part)
    sources_by_key={}
    for part in parts:
        if not isinstance(part,dict): raise GovernanceError("Backfill part candidate must be an object")
        declaration=part.get("source_path")
        if not isinstance(declaration,str): continue
        key=(declaration,part.get("source_case"),part.get("source_frame"),
             part.get("license"),part.get("derivation"))
        if key in sources_by_key: continue
        source_id="declaration:"+hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()[:20]
        sources_by_key[key]={"sourceId":source_id,"declarationPath":declaration,
            "subjectCase":part.get("source_case"),"frame":part.get("source_frame"),
            "license":part.get("license"),"derivation":part.get("derivation"),
            "status":"declared-unverified"}
    exports=[{"path":path,"sha256":identity["sha256"],"bytes":identity["bytes"],
        "identityBasis":"git-lfs-pointer-or-local-bytes"}
        for path,identity in sorted(proposal.get("exportIdentities",{}).items())]
    artifacts=proposal.get("artifacts",[])
    unresolved=[]
    if not proposal.get("parts"):
        unresolved.append("No named part declarations were discovered; add reviewed stable part selectors.")
    if not sources_by_key:
        unresolved.append("No package-owned provenance declarations were discovered; identify source subjects, rights and attribution.")
    else:
        unresolved.append("Source/provenance declarations are copied from package metadata and require owner review.")
    unresolved.append("No canonical anatomical concept mappings have been approved.")
    unresolved.append("No explicit revision IDs were declared; do not synthesize revisions from filenames or hashes.")
    unresolved.append("No downstream teaching or consumer bindings have been adopted.")
    unresolved.append("Package-level lineage granularity still requires owner confirmation.")
    for part in parts:
        if not part.get("selectors"):
            unresolved.append(f"Part {part.get('part_id')} has no exact source selector.")
        if part.get("status") in {"illustrative","diagnostic-only","rejected","unknown"}:
            unresolved.append(f"Part {part.get('part_id')} has non-production status {part.get('status')}.")
    for artifact in artifacts:
        if artifact.get("verification") in {"missing","mismatch","invalid-pointer"}:
            unresolved.append(f"Artifact {artifact.get('path')} has verification state {artifact.get('verification')}.")
    return {"schemaVersion":1,"assetId":asset_id,"title":proposal["title"],"kind":proposal["kind"],
      "status":"provisional","owner":owner,"concepts":[],"sources":list(sources_by_key.values()),
      "parts":list(parts_by_id.values()),"revisions":[],"artifacts":artifacts,"exports":exports,"uses":[],
      "retirement":None,"unresolved":list(dict.fromkeys(unresolved))}

def apply_backfill_plan(repo:Path,plan_path:Path):
    repo=repo.resolve();plan=json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schemaVersion")!=1 or plan.get("intent")!="asset-record-backfill": raise GovernanceError("Unsupported backfill plan")
    if Path(plan.get("repository","")).resolve()!=repo: raise GovernanceError("Plan belongs to another checkout")
    catalog=build_catalog(repo)
    current_hashes=catalog.source_hashes
    current_sources={k:v for k,v in current_hashes.items() if not k.endswith("/asset.record.json")}
    current_records={k:v for k,v in current_hashes.items() if k.endswith("/asset.record.json")}
    if current_sources!=plan.get("sourceHashes"): raise GovernanceError("Backfill source inputs changed; regenerate the plan")
    expected_existing=plan.get("recordHashes",{})
    if any(current_records.get(path)!=digest for path,digest in expected_existing.items()):
        raise GovernanceError("An existing package-owned asset record changed after planning")
    accepted=[p for p in plan.get("proposals",[]) if p.get("decision")=="accept"]
    expected_record_paths=set(expected_existing)|{source_path(p["packagePath"])+"/asset.record.json" for p in accepted}
    if set(current_records)-expected_record_paths:
        raise GovernanceError("An unplanned asset record was added after planning")
    packages_by_path={item.path:item for item in catalog.packages}
    applied=[];ids=set(plan.get("existingAssetIds",[]))
    for proposal in plan.get("proposals",[]):
        if proposal.get("decision")!="accept": continue
        asset_id=proposal.get("assetId")
        if not isinstance(asset_id,str) or not asset_id.strip() or asset_id in ids:
            raise GovernanceError("Accepted proposal needs a unique explicit assetId")
        ids.add(asset_id)
        package_path=source_path(proposal["packagePath"])
        candidate=packages_by_path.get(package_path)
        if candidate is None: raise GovernanceError(f"Package disappeared after planning: {package_path}")
        if candidate.candidate_id!=proposal.get("candidateId"):
            existing_record=json.loads((repo/package_path/"asset.record.json").read_text(encoding="utf-8")) if candidate.record_path else {}
            if existing_record.get("assetId")!=proposal.get("assetId"):
                raise GovernanceError(f"Package candidate identity changed: {package_path}")
        if list(candidate.exports)!=proposal.get("exports") or list(candidate.manifests)!=proposal.get("manifests"):
            raise GovernanceError(f"Package export or manifest inventory changed: {package_path}")
        if [asdict(x) for x in candidate.artifacts]!=proposal.get("artifacts"):
            raise GovernanceError(f"Package artifact declarations or verification changed: {package_path}")
        current_identities={}
        for export in candidate.exports:
            digest,size=declared_identity(repo,export)
            current_identities[export]={"sha256":digest,"bytes":size}
        if current_identities!=proposal.get("exportIdentities"):
            raise GovernanceError(f"Package export content identities changed: {package_path}")
        if candidate.readme_sha256 is None or candidate.readme_sha256!=proposal.get("readmeSha256"):
            raise GovernanceError(f"Package README is missing or changed: {package_path}")
        owner=source_path(proposal["owner"])
        if owner!=package_path: raise GovernanceError("Record must be written by its owning package")
        package=owner_path(repo,owner);destination=package/"asset.record.json"
        record=_record_document(proposal,asset_id)
        encoded=(json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode()
        if destination.exists():
            if destination.read_bytes()!=encoded:
                raise GovernanceError(f"Conflicting existing asset record: {destination}")
            continue
        _atomic(destination,encoded)
        applied.append(destination.relative_to(repo).as_posix())
    return applied

def hydrate_lfs(repo:Path,paths:list[str],apply:bool=False):
    repo=repo.resolve();normalized=sorted(set(source_path(x) for x in paths))
    if not normalized: raise GovernanceError("Specify repository-relative paths to hydrate")
    command=["git","lfs","pull","--include",",".join(normalized)]
    if not apply: return {"status":"planned","command":command,"paths":normalized}
    if not (repo/".git").exists(): raise GovernanceError("Hydration requires a Git checkout")
    result=subprocess.run(command,cwd=repo,text=True,capture_output=True,check=False)
    if result.returncode: raise GovernanceError(f"Git LFS failed: {result.stderr.strip()}")
    unresolved=[]
    for value in normalized:
        path=owner_path(repo,value)
        with path.open("rb") as stream: prefix=stream.read(80)
        if prefix.startswith(b"version https://git-lfs.github.com/spec/"): unresolved.append(value)
    if unresolved: raise GovernanceError("Unresolved LFS pointers: "+", ".join(unresolved))
    return {"status":"hydrated","paths":normalized,"stdout":result.stdout}
