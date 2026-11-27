"""Repository-native governance read model and consumer adapters."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json, re
from pathlib import Path, PurePosixPath
from typing import Any
from .artifacts import source_path, unique_keys

SCHEMA_VERSION=1
ROOTS=("models","assemblies","body","heart","diagrams","lessons")
RECORD="asset.record.json"
BODY_STOPS="lessons/body-systems/reviewed-stops.json"
US_BRIEF="docs/gallery/use-cases/ultrasound-anatomy.md"
US_REVIEWS="experiments/ultrasound-sweep/development/asset-reviews"
SCENARIO=re.compile(r"^\| \[([^]]+)\]\(#([^)]*)\) \| (.*?) \|$")

class GovernanceError(ValueError): pass

def sha(data: bytes)->str: return hashlib.sha256(data).hexdigest()
def read_json(path: Path):
    try: return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (OSError,json.JSONDecodeError) as exc: raise GovernanceError(f"Invalid JSON {path}: {exc}") from exc
def rel(repo: Path,path: Path)->str:
    try: return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError as exc: raise GovernanceError(f"Path escapes repository: {path}") from exc
def owner_path(repo: Path,value: str)->Path:
    value=source_path(value); path=repo.resolve()/PurePosixPath(value)
    if path.resolve()!=path: raise GovernanceError(f"Linked path is not an owner record: {value}")
    return path
def readme_title(path: Path,fallback: str)->str:
    if path.is_file():
        for line in path.read_text(encoding="utf-8",errors="replace").splitlines()[:30]:
            if line.startswith("# "): return line[2:].strip()
    return fallback.replace("-"," ").replace("_"," ").title()

@dataclass(frozen=True)
class Package:
    candidate_id:str; path:str; title:str; kind:str; readme_sha256:str|None
    exports:tuple[str,...]; record_path:str|None; record_status:str; unresolved:tuple[str,...]

@dataclass(frozen=True)
class Consumer:
    consumer_id:str; domain:str; kind:str; title:str; action:str; status:str
    source_path:str; evidence:dict[str,Any]

@dataclass(frozen=True)
class Catalog:
    repository:str; packages:tuple[Package,...]; consumers:tuple[Consumer,...]; source_hashes:dict[str,str]
    def to_dict(self):
        return {"schemaVersion":1,"repository":self.repository,
          "packages":[asdict(x) for x in self.packages],"consumers":[asdict(x) for x in self.consumers],
          "sourceHashes":dict(sorted(self.source_hashes.items())),
          "counts":{"packageCandidates":len(self.packages),
            "confirmedRecords":sum(x.record_status=="confirmed" for x in self.packages),
            "provisionalRecords":sum(x.record_status=="provisional" for x in self.packages),
            "consumerRequirements":len(self.consumers)}}

def _record_status(repo:Path,package:Path):
    path=package/RECORD
    if not path.exists(): return "unregistered",("No package-owned asset.record.json",)
    data=read_json(path)
    required={"schemaVersion","assetId","title","kind","status","owner","concepts","sources","parts","revisions","uses","unresolved"}
    if set(data)!=required or data.get("schemaVersion")!=1: raise GovernanceError(f"Invalid asset record: {rel(repo,path)}")
    if data["status"] not in {"provisional","active","deprecated","retired"}: raise GovernanceError(f"Invalid lifecycle status: {rel(repo,path)}")
    if data["owner"]!=rel(repo,package): raise GovernanceError(f"Asset record owner mismatch: {rel(repo,path)}")
    for field in ("concepts","sources","parts","revisions","uses","unresolved"):
        if not isinstance(data[field],list): raise GovernanceError(f"Expected array {field}: {rel(repo,path)}")
    return ("confirmed" if data["status"]=="active" else "provisional"),tuple(data["unresolved"])

def scan_packages(repo:Path):
    result=[]; seen=set()
    for root_name in ROOTS:
        root=repo/root_name
        if not root.is_dir(): continue
        for package in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            path=rel(repo,package); readme=package/"README.md"
            readme_hash=sha(readme.read_bytes()) if readme.is_file() else None
            exports=tuple(rel(repo,p) for p in sorted(package.rglob("*"))
                if p.is_file() and p.suffix.lower() in {".glb",".blend",".svg"}
                and ".artifacts" not in p.parts and ".git" not in p.parts)
            record=package/RECORD; status,unresolved=_record_status(repo,package)
            candidate="package:"+path
            if record.is_file(): candidate=read_json(record)["assetId"]
            if candidate in seen: raise GovernanceError(f"Duplicate asset identity: {candidate}")
            seen.add(candidate)
            kind={"models":"model-package","assemblies":"assembly-package","body":"body-package",
                  "heart":"heart-package","diagrams":"diagram-package","lessons":"lesson-package"}[root_name]
            result.append(Package(candidate,path,readme_title(readme,package.name),kind,readme_hash,exports,
                rel(repo,record) if record.is_file() else None,status,unresolved))
    return tuple(result)

def body_system_consumers(repo:Path):
    path=owner_path(repo,BODY_STOPS)
    if not path.is_file(): return ()
    data=read_json(path); stops=data.get("stops")
    if not isinstance(stops,list): raise GovernanceError(f"Invalid Body Systems stops: {BODY_STOPS}")
    result=[]; seen=set()
    for row in stops:
        system,detail,action,observation,status=(row.get(k) for k in ("system","detail","action","observation","status"))
        if not all(isinstance(v,str) and v.strip() for v in (system,detail,action,observation,status)):
            raise GovernanceError(f"Incomplete Body Systems stop: {BODY_STOPS}")
        identity=f"body-systems:{system}:{detail}"
        if identity in seen: raise GovernanceError(f"Duplicate consumer: {identity}")
        seen.add(identity)
        result.append(Consumer(identity,"body-systems","reviewed-stop",f"{system.title()} · {detail}",action,
            "reviewed-"+status,BODY_STOPS,{"observation":observation,"reviewer":data.get("reviewer"),"date":data.get("date")}))
    return tuple(result)

def ultrasound_consumers(repo:Path):
    result=[]; brief=owner_path(repo,US_BRIEF)
    if brief.is_file():
        for line in brief.read_text(encoding="utf-8").splitlines():
            match=SCENARIO.match(line)
            if match:
                label,anchor,action=match.groups()
                result.append(Consumer("ultrasound:scenario:"+anchor,"ultrasound-anatomy","scenario-brief",
                    label,action.strip(),"briefed-not-qualified",US_BRIEF,{"anchor":anchor}))
    root=owner_path(repo,US_REVIEWS)
    if root.is_dir():
        for path in sorted(root.glob("*/reviews.json")):
            doc=read_json(path)
            for row in doc.get("records",[]):
                case,part,task=(row.get(k) for k in ("case","part","task"))
                if not all(isinstance(v,str) and v.strip() for v in (case,part,task)):
                    raise GovernanceError(f"Incomplete ultrasound review: {rel(repo,path)}")
                revision=row.get("revision","unknown"); chapter=row.get("chapter","")
                identity=f"ultrasound:assessment:{case}:{part}:{chapter}:{sha(task.encode())[:10]}"
                result.append(Consumer(identity,"ultrasound-anatomy","part-assessment",f"{case} · {part}",task,
                    "assessed-provisional",rel(repo,path),{"chapter":chapter,"reviewedOn":row.get("reviewedOn"),
                    "scores":row.get("scores",{}),"revision":revision,"source":row.get("source")}))
    ids=[x.consumer_id for x in result]
    if len(ids)!=len(set(ids)): raise GovernanceError("Duplicate ultrasound consumer identity")
    return tuple(result)

def build_catalog(repo:Path):
    repo=repo.resolve(); packages=scan_packages(repo)
    consumers=body_system_consumers(repo)+ultrasound_consumers(repo); hashes={}
    for item in consumers:
        path=owner_path(repo,item.source_path); hashes[item.source_path]=sha(path.read_bytes())
    for item in packages:
        if item.readme_sha256: hashes[item.path+"/README.md"]=item.readme_sha256
        if item.record_path:
            path=owner_path(repo,item.record_path); hashes[item.record_path]=sha(path.read_bytes())
    return Catalog(str(repo),packages,consumers,hashes)

def find(catalog:Catalog,query:str,domain:str|None=None):
    terms=tuple(x.casefold() for x in query.split() if x); packages=[]; consumers=[]
    for item in catalog.packages:
        hay=" ".join((item.candidate_id,item.path,item.title,*item.exports)).casefold()
        if all(term in hay for term in terms): packages.append(asdict(item))
    for item in catalog.consumers:
        if domain and item.domain!=domain: continue
        hay=" ".join((item.consumer_id,item.domain,item.title,item.action,item.source_path)).casefold()
        if all(term in hay for term in terms): consumers.append(asdict(item))
    return {"query":query,"packages":packages,"consumers":consumers}

def show(catalog:Catalog,identity:str):
    for item in catalog.packages:
        if identity in {item.candidate_id,item.path}: return {"type":"package-candidate",**asdict(item)}
    for item in catalog.consumers:
        if identity==item.consumer_id: return {"type":"consumer-requirement",**asdict(item)}
    raise GovernanceError(f"Unknown identity: {identity}")

def impact(catalog:Catalog,identity:str):
    target=show(catalog,identity)
    if target["type"]=="consumer-requirement": return {"target":target,"knownConsumers":[target]}
    return {"target":target,"knownConsumers":[],"limitations":[
      "Package discovery does not prove an independent asset lineage.",
      "Consumer-to-asset bindings are not inferred from names or anatomical similarity.",
      "Unknown external readers cannot be inferred from this checkout."]}
