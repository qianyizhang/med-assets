"""Reviewed package-record backfill and scoped Git LFS hydration."""
from __future__ import annotations
import hashlib,json,os,subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from .artifacts import source_path
from .governance import GovernanceError,build_catalog,owner_path

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
    for item in catalog.packages:
        if item.record_path: continue
        proposals.append({"candidateId":item.candidate_id,"packagePath":item.path,"title":item.title,
          "kind":item.kind,"readmeSha256":item.readme_sha256,"exports":list(item.exports),
          "decision":"defer","assetId":None,"owner":item.path,
          "notes":"Package discovery is not proof of an independent asset lineage. Confirm granularity and ownership."})
    return {"schemaVersion":1,"intent":"asset-record-backfill","repository":str(repo.resolve()),
      "sourceHashes":catalog.source_hashes,
      "existingAssetIds":[item.candidate_id for item in catalog.packages if item.record_path],
      "proposals":proposals,
      "consumerCoverage":{"bodySystemsStops":sum(x.domain=="body-systems" for x in catalog.consumers),
        "ultrasoundRequirements":sum(x.domain=="ultrasound-anatomy" for x in catalog.consumers)}}

def write_backfill_plan(repo:Path,destination:Path):
    plan=create_backfill_plan(repo);_atomic(destination,(json.dumps(plan,ensure_ascii=False,indent=2)+"\n").encode());return plan

def apply_backfill_plan(repo:Path,plan_path:Path):
    repo=repo.resolve();plan=json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schemaVersion")!=1 or plan.get("intent")!="asset-record-backfill": raise GovernanceError("Unsupported backfill plan")
    if Path(plan.get("repository","")).resolve()!=repo: raise GovernanceError("Plan belongs to another checkout")
    if build_catalog(repo).source_hashes!=plan.get("sourceHashes"): raise GovernanceError("Backfill inputs changed; regenerate the plan")
    applied=[];ids=set(plan.get("existingAssetIds",[]))
    current_packages={item.candidate_id:item for item in build_catalog(repo).packages}
    for proposal in plan.get("proposals",[]):
        if proposal.get("decision")!="accept": continue
        asset_id=proposal.get("assetId")
        if not isinstance(asset_id,str) or not asset_id.strip() or asset_id in ids: raise GovernanceError("Accepted proposal needs a unique explicit assetId")
        ids.add(asset_id)
        candidate=current_packages.get(proposal.get("candidateId"))
        if candidate is None or candidate.path!=proposal.get("packagePath") or list(candidate.exports)!=proposal.get("exports"):
            raise GovernanceError("Package export inventory changed after planning")
        owner=source_path(proposal["owner"])
        if owner!=proposal["packagePath"]: raise GovernanceError("Record must be written by its owning package")
        package=owner_path(repo,owner);destination=package/"asset.record.json"
        if _sha(package/"README.md")!=proposal.get("readmeSha256"): raise GovernanceError(f"Package changed: {owner}")
        record={"schemaVersion":1,"assetId":asset_id,"title":proposal["title"],"kind":proposal["kind"],
          "status":"provisional","owner":owner,"concepts":[],"sources":[],"parts":[],"revisions":[],"uses":[],
          "unresolved":["Confirm independent maintenance lineage and editable source.",
            "Declare source provenance, rights, subject, units, axes and laterality.",
            "Map stable concepts and named parts to exact source selectors.",
            "Bind revisions, exports, recipes and artifact identities.",
            "Reconcile downstream consumers before qualification or retirement."]}
        encoded=(json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode()
        if destination.exists():
            if destination.read_bytes()!=encoded: raise GovernanceError(f"Conflicting existing asset record: {destination}")
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
