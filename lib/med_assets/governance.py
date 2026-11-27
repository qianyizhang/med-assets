"""Repository-native governance read model and consumer adapters."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json, re
from pathlib import Path, PurePosixPath
from typing import Any
from .artifacts import HEX64, parse_pointer, source_path, unique_keys

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
class ArtifactDeclaration:
    artifact_id:str
    path:str
    declaration_path:str
    sha256:str
    bytes:int
    verification:str

@dataclass(frozen=True)
class Package:
    candidate_id:str; path:str; title:str; kind:str; readme_sha256:str|None
    exports:tuple[str,...]; manifests:tuple[str,...]; artifacts:tuple[ArtifactDeclaration,...]
    record_path:str|None; record_status:str; unresolved:tuple[str,...]

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
            "artifactDeclarations":sum(len(x.artifacts) for x in self.packages),
            "artifactVerifiedBytes":sum(a.verification=="verified" for x in self.packages for a in x.artifacts),
            "artifactLfsPointers":sum(a.verification=="pointer-match" for x in self.packages for a in x.artifacts),
            "artifactMissing":sum(a.verification=="missing" for x in self.packages for a in x.artifacts),
            "artifactMismatches":sum(a.verification=="mismatch" for x in self.packages for a in x.artifacts),
            "consumerRequirements":len(self.consumers),
            "ultrasoundCases":sum(x.kind=="modeled-case" for x in self.consumers),
            "ultrasoundCaseViews":sum(x.kind=="acquisition-chapter" for x in self.consumers),
            "ultrasoundSweeps":sum(x.kind=="standalone-sweep" for x in self.consumers),
            "bodySystemStops":sum(x.domain=="body-systems" for x in self.consumers)}}

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

def _manifest_artifacts(repo:Path,package:Path):
    artifacts=[]; manifests=sorted(package.rglob("package-manifest.json"))
    for manifest in manifests:
        manifest_path=rel(repo,manifest)
        if manifest.is_symlink() or manifest.resolve()!=manifest:
            raise GovernanceError(f"Linked package manifest: {manifest_path}")
        document=read_json(manifest)
        if not isinstance(document,list):
            raise GovernanceError(f"Unsupported package manifest shape: {manifest_path}")
        seen=set()
        for row in document:
            if not isinstance(row,dict): raise GovernanceError(f"Invalid artifact row: {manifest_path}")
            name=row.get("file"); digest=row.get("sha256"); size=row.get("bytes")
            if not isinstance(name,str): raise GovernanceError(f"Missing artifact path: {manifest_path}")
            relative_name=source_path(name)
            if relative_name in seen: raise GovernanceError(f"Duplicate artifact path in {manifest_path}: {relative_name}")
            seen.add(relative_name)
            if not isinstance(digest,str) or not HEX64.fullmatch(digest) or type(size) is not int or size<0:
                raise GovernanceError(f"Invalid artifact identity in {manifest_path}: {relative_name}")
            target=manifest.parent/PurePosixPath(relative_name)
            target_name=rel(repo,target)
            if target.resolve()!=target: raise GovernanceError(f"Linked manifest artifact: {target_name}")
            if not target.is_file(): verification="missing"
            else:
                with target.open("rb") as stream:
                    prefix=stream.read(1025)
                    if prefix.startswith(b"version https://git-lfs.github.com/spec/"):
                        actual_digest,actual_size=parse_pointer(prefix)
                        verification="pointer-match" if (actual_digest,actual_size)==(digest,size) else "mismatch"
                    else:
                        stream.seek(0); actual_size=target.stat().st_size
                        actual_digest=hashlib.file_digest(stream,"sha256").hexdigest()
                        verification="verified" if (actual_digest,actual_size)==(digest,size) else "mismatch"
            identity=sha((manifest_path+"\\0"+target_name).encode())
            artifacts.append(ArtifactDeclaration(identity,target_name,manifest_path,digest,size,verification))
    return tuple(artifacts),tuple(rel(repo,p) for p in manifests)

def scan_packages(repo:Path):
    result=[]; seen=set()
    for root_name in ROOTS:
        root=repo/root_name
        if not root.is_dir(): continue
        for package in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            path=rel(repo,package); readme=package/"README.md"
            readme_hash=sha(readme.read_bytes()) if readme.is_file() else None
            exports=tuple(rel(repo,p) for p in sorted(package.rglob("*"))
                if p.is_file() and p.suffix.lower() in {".glb",".gltf",".blend",".svg",".obj",".stl",".ply",".fbx"}
                and ".artifacts" not in p.parts and ".git" not in p.parts)
            artifacts,manifests=_manifest_artifacts(repo,package)
            record=package/RECORD; status,unresolved=_record_status(repo,package)
            candidate="package:"+path
            if record.is_file(): candidate=read_json(record)["assetId"]
            if candidate in seen: raise GovernanceError(f"Duplicate asset identity: {candidate}")
            seen.add(candidate)
            kind={"models":"model-package","assemblies":"assembly-package","body":"body-package",
                  "heart":"heart-package","diagrams":"diagram-package","lessons":"lesson-package"}[root_name]
            result.append(Package(candidate,path,readme_title(readme,package.name),kind,readme_hash,exports,manifests,artifacts,
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

def _javascript_calls(source:str):
    """Yield function calls with balanced delimiters; ignore strings and comments."""
    pattern=re.compile(r"\b(gap|rebuild|missingPart)\s*\(")
    consumed_end=0
    for match in pattern.finditer(source):
        if match.start()<consumed_end: continue
        start=match.end(); depth=1; quote=None; escaped=False; line_comment=False; block_comment=False; i=start
        while i<len(source) and depth:
            char=source[i]; nxt=source[i+1] if i+1<len(source) else ""
            if line_comment:
                if char=="\n": line_comment=False
            elif block_comment:
                if char=="*" and nxt=="/": block_comment=False;i+=1
            elif quote:
                if escaped: escaped=False
                elif char=="\\": escaped=True
                elif char==quote: quote=None
            elif char in ("'",'"',"`"): quote=char
            elif char=="/" and nxt=="/": line_comment=True;i+=1
            elif char=="/" and nxt=="*": block_comment=True;i+=1
            elif char=="(": depth+=1
            elif char==")": depth-=1
            i+=1
        if depth: raise GovernanceError(f"Unclosed ultrasound requirement call at line {source.count(chr(10),0,match.start())+1}")
        body=source[start:i-1]
        args=[];begin=0;level=0;quote=None;escaped=False
        for pos,char in enumerate(body):
            if quote:
                if escaped: escaped=False
                elif char=="\\": escaped=True
                elif char==quote: quote=None
            elif char in ("'",'"',"`"): quote=char
            elif char in "([{": level+=1
            elif char in ")]}": level-=1
            elif char=="," and level==0:
                args.append(body[begin:pos].strip());begin=pos+1
        args.append(body[begin:].strip())
        def literal(value):
            value=value.strip()
            if len(value)>=2 and value[0] in ("'",'"') and value[-1]==value[0]:
                try: return bytes(value[1:-1],"utf-8").decode("unicode_escape")
                except UnicodeDecodeError: return value[1:-1]
            return None
        strings=[literal(arg) for arg in args]
        consumed_end=i
        yield match.group(1),args,strings,source.count("\n",0,match.start())+1

def ultrasound_gap_requirements(repo:Path):
    result=[]
    files=("experiments/ultrasound-sweep/development/assets-abdomen.js",
           "experiments/ultrasound-sweep/development/assets-exams.js")
    for filename in files:
        path=owner_path(repo,filename)
        if not path.is_file(): continue
        source=path.read_text(encoding="utf-8")
        for call_index,(function,args,strings,line) in enumerate(_javascript_calls(source),1):
            if function in ("gap","rebuild"):
                if len(args)<4: raise GovernanceError(f"Malformed {function} requirement at {filename}:{line}")
                part=next((strings[i] for i in range(1,len(strings)) if strings[i]),None)
                # The semantic part and label are the last direct string arguments
                # before any legacy alias array.
                direct=[value for value in strings if value]
                if len(direct)<3:
                    # Shared resolvers may construct requirements from runtime identities.
                    continue
                offset=1 if args and (args[0].strip().startswith("'") or args[0].strip().startswith('"')) else 0
                if len(direct)<offset+3: continue
                part,label,reason=direct[offset],direct[offset+1],direct[offset+2]
                status="rebuild-required" if function=="rebuild" else "missing-required"
            else:
                if len(args)<5: raise GovernanceError(f"Malformed missingPart requirement at {filename}:{line}")
                direct=[value for value in strings if value]
                if len(direct)<5: raise GovernanceError(f"Incomplete missingPart requirement at {filename}:{line}")
                part,label,reason=direct[2],direct[3],direct[4]
                status="missing-required"
            identity=f"ultrasound:geometry-gap:{Path(filename).stem}:{line}:{call_index}:{part}"
            result.append(Consumer(identity,"ultrasound-anatomy","geometry-requirement",
                label,reason,status,filename,{"part":part,"declaration":function,"line":line}))
    return result

def _ultrasound_case_consumers(repo:Path):
    result=[]
    files=("experiments/ultrasound-sweep/cases/organs/cases.json",
      "experiments/ultrasound-sweep/cases/pregnancy/cases.json",
      "experiments/ultrasound-sweep/cases/vascular/cases.json",
      "experiments/ultrasound-sweep/cases/echo/cases.json")
    for filename in files:
        path=owner_path(repo,filename)
        if not path.is_file(): continue
        cases=read_json(path)
        if not isinstance(cases,list): raise GovernanceError(f"Expected case array: {filename}")
        family_source=Path(filename).parent.name
        for case in cases:
            if not isinstance(case,dict): raise GovernanceError(f"Invalid ultrasound case row: {filename}")
            case_id,family,title=(case.get(k) for k in ("id","family","title"))
            if not all(isinstance(v,str) and v.strip() for v in (case_id,family,title)):
                raise GovernanceError(f"Incomplete ultrasound case: {filename}")
            result.append(Consumer(f"ultrasound:case:{family_source}:{case_id}","ultrasound-anatomy",
                "modeled-case",title,case.get("summary",case.get("indication","")),
                "case-authored-provisional",filename,{"family":family,"kind":case.get("kind"),
                "indication":case.get("indication"),"limitations":case.get("limitations"),
                "impression":case.get("impression")}))
            views=case.get("views",[])
            if not isinstance(views,list): raise GovernanceError(f"Invalid views for case {case_id}")
            for index,view in enumerate(views):
                if not isinstance(view,dict): raise GovernanceError(f"Invalid case view: {case_id} in {filename}")
                view_title=view.get("title")
                if not isinstance(view_title,str) or not view_title.strip():
                    raise GovernanceError(f"Incomplete case view: {case_id} in {filename}")
                result.append(Consumer(f"ultrasound:case-view:{family_source}:{case_id}:{index+1}",
                    "ultrasound-anatomy","acquisition-chapter",f"{title} · {view_title}",
                    view.get("caption",""),"case-view-provisional",filename,
                    {"caseId":case_id,"family":family,"index":index,"image":view.get("image"),
                     "measurement":view.get("measurement"),"referenceIds":view.get("referenceIds",[])}))
    return result

def _ultrasound_track_consumers(repo:Path):
    result=[]
    files=("abdomen-tracks.json","aortic-screening-track.json","thyroid-tracks.json",
      "carotid-tracks.json","breast-track.json","axilla-track.json",
      "early-pregnancy-track.json","pregnancy-tracks.json","gestational-tracks.json")
    for filename in files:
        owner="experiments/ultrasound-sweep/"+filename
        path=owner_path(repo,owner)
        if not path.is_file(): continue
        document=read_json(path); common=document.get("common",{})
        sweeps=document.get("sweeps",[])
        if not isinstance(sweeps,list): raise GovernanceError(f"Invalid sweep array: {owner}")
        for sweep in sweeps:
            if not isinstance(sweep,dict): raise GovernanceError(f"Invalid sweep row: {owner}")
            sweep_id=sweep.get("id"); title=sweep.get("title",sweep_id)
            if not isinstance(sweep_id,str) or not sweep_id.strip():
                raise GovernanceError(f"Invalid sweep identity: {owner}")
            result.append(Consumer(f"ultrasound:sweep:{Path(filename).stem}:{sweep_id}",
                "ultrasound-anatomy","standalone-sweep",title or sweep_id,
                sweep.get("sourceNote",common.get("sourceNote","")),
                "sweep-authored-provisional",owner,
                {"region":sweep.get("region",common.get("bodyRegion")),
                 "case":sweep.get("case",common.get("case")),
                 "parts":sweep.get("parts",common.get("parts",[])),
                 "overlayParts":sweep.get("overlayParts",common.get("overlayParts",[])),
                 "landmarks":sweep.get("landmarks",common.get("landmarks",[])),
                 "keyframeLabels":sweep.get("keyframeLabels",common.get("keyframeLabels",[])),
                 "phaseLabels":sweep.get("phaseLabels",common.get("phaseLabels",[])),
                 "probeType":sweep.get("probeType",common.get("probeType")),
                 "fieldShape":sweep.get("fieldShape",common.get("fieldShape")),
                 "routeGroup":sweep.get("routeGroup",common.get("routeGroup")),
                 "routeLabel":sweep.get("routeLabel")}))
    return result

def ultrasound_consumers(repo:Path):
    result=[]; brief=owner_path(repo,US_BRIEF)
    if brief.is_file():
        for line in brief.read_text(encoding="utf-8").splitlines():
            match=SCENARIO.match(line)
            if match:
                label,anchor,action=match.groups()
                result.append(Consumer("ultrasound:scenario:"+anchor+":"+sha(label.casefold().encode())[:10],
                    "ultrasound-anatomy","scenario-brief",label,action.strip(),
                    "briefed-not-qualified",US_BRIEF,{"anchor":anchor}))
    result.extend(_ultrasound_case_consumers(repo))
    result.extend(_ultrasound_track_consumers(repo))
    result.extend(ultrasound_gap_requirements(repo))
    root=owner_path(repo,US_REVIEWS)
    if root.is_dir():
        for path in sorted(root.glob("*/reviews.json")):
            doc=read_json(path)
            records=doc.get("records",[])
            if not isinstance(records,list): raise GovernanceError(f"Invalid ultrasound review records: {rel(repo,path)}")
            for index,row in enumerate(records):
                if not isinstance(row,dict): raise GovernanceError(f"Invalid ultrasound review row: {rel(repo,path)}")
                case,part,task=(row.get(k) for k in ("case","part","task"))
                if not all(isinstance(v,str) and v.strip() for v in (case,part,task)):
                    raise GovernanceError(f"Incomplete ultrasound review: {rel(repo,path)}")
                revision=row.get("revision","unknown"); chapter=row.get("chapter","")
                identity=f"ultrasound:assessment:{Path(rel(repo,path)).parent.name}:{case}:{part}:{chapter}:{index+1}:{sha(task.encode())[:10]}"
                result.append(Consumer(identity,"ultrasound-anatomy","part-assessment",f"{case} · {part}",task,
                    "assessed-provisional",rel(repo,path),{"chapter":chapter,"reviewedOn":row.get("reviewedOn"),
                    "scores":row.get("scores",{}),"revision":revision,"source":row.get("source"),
                    "beforeScores":row.get("beforeScores")}))
    ids=[x.consumer_id for x in result]
    if len(ids)!=len(set(ids)):
        seen=set(); duplicates=[]
        for identity in ids:
            if identity in seen: duplicates.append(identity)
            seen.add(identity)
        raise GovernanceError("Duplicate ultrasound consumer identity: "+", ".join(duplicates[:20]))
    return tuple(result)

def build_catalog(repo:Path):
    repo=repo.resolve(); packages=scan_packages(repo)
    consumers=body_system_consumers(repo)+ultrasound_consumers(repo); hashes={}
    for item in consumers:
        path=owner_path(repo,item.source_path); hashes[item.source_path]=sha(path.read_bytes())
    for item in packages:
        if item.readme_sha256: hashes[item.path+"/README.md"]=item.readme_sha256
        for manifest_name in item.manifests:
            manifest=owner_path(repo,manifest_name)
            hashes[manifest_name]=sha(manifest.read_bytes())
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
