"""Repository-native governance read model and consumer adapters."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json, re
from pathlib import Path, PurePosixPath
from typing import Any
from .artifacts import HEX64, declared_identity, parse_pointer, source_path, unique_keys
from .teaching import CurrentTeaching

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
class PackagePart:
    part_id:str
    label:str
    selectors:tuple[str,...]
    source_path:str
    geometry_type:str
    status:str
    source_case:str|None=None
    source_frame:str|None=None
    parent_part_id:str|None=None
    aliases:tuple[str,...]=()
    license:str|None=None
    derivation:str|None=None
    attributes:dict[str,Any]|None=None

@dataclass(frozen=True)
class Package:
    candidate_id:str; path:str; title:str; kind:str; readme_sha256:str|None
    exports:tuple[str,...]; manifests:tuple[str,...]; artifacts:tuple[ArtifactDeclaration,...]
    parts:tuple[PackagePart,...]
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
            "artifactInvalidPointers":sum(a.verification=="invalid-pointer" for x in self.packages for a in x.artifacts),
            "partCandidates":sum(len(x.parts) for x in self.packages),
            "consumerRequirements":len(self.consumers),
            "ultrasoundCases":sum(x.kind=="modeled-case" for x in self.consumers),
            "ultrasoundCaseViews":sum(x.kind=="acquisition-chapter" for x in self.consumers),
            "ultrasoundSweeps":sum(x.kind=="standalone-sweep" for x in self.consumers),
            "bodySystemStops":sum(x.domain=="body-systems" and x.kind=="reviewed-stop" for x in self.consumers),
            "bodySystemAssemblies":sum(x.domain=="body-systems" and x.kind=="system-assembly" for x in self.consumers),
            "bodySystemPlates":sum(x.domain=="body-systems" and x.kind=="display-plate" for x in self.consumers),
            "ultrasoundGeometryRequirements":sum(x.domain=="ultrasound-anatomy" and x.kind=="geometry-requirement" for x in self.consumers),
            "teachingAssessments":sum(x.domain=="teaching-assessments" for x in self.consumers)}}

def _record_status(repo:Path,package:Path):
    path=package/RECORD
    if not path.exists(): return "unregistered",("No package-owned asset.record.json",)
    data=read_json(path)
    required={"schemaVersion","assetId","title","kind","status","owner","concepts","sources",
      "parts","revisions","artifacts","exports","uses","unresolved"}
    if set(data)!=required or data.get("schemaVersion")!=1:
        raise GovernanceError(f"Invalid asset record: {rel(repo,path)}")
    if data["status"] not in {"provisional","active","deprecated","retired"}:
        raise GovernanceError(f"Invalid lifecycle status: {rel(repo,path)}")
    if data["owner"]!=rel(repo,package):
        raise GovernanceError(f"Asset record owner mismatch: {rel(repo,path)}")
    for field in ("concepts","sources","parts","revisions","artifacts","exports","uses","unresolved"):
        if not isinstance(data[field],list):
            raise GovernanceError(f"Expected array {field}: {rel(repo,path)}")
    part_ids=[row.get("partId") for row in data["parts"] if isinstance(row,dict)]
    if len(part_ids)!=len(data["parts"]) or len(part_ids)!=len(set(part_ids)):
        raise GovernanceError(f"Invalid or duplicate part IDs: {rel(repo,path)}")
    for row in data["exports"]:
        if not isinstance(row,dict) or not isinstance(row.get("path"),str):
            raise GovernanceError(f"Invalid export record: {rel(repo,path)}")
        if not isinstance(row.get("sha256"),str) or not HEX64.fullmatch(row["sha256"]):
            raise GovernanceError(f"Invalid export digest: {rel(repo,path)}")
        if type(row.get("bytes")) is not int or row["bytes"]<0:
            raise GovernanceError(f"Invalid export size: {rel(repo,path)}")
    return ("confirmed" if data["status"]=="active" else "provisional"),tuple(data["unresolved"])

def _manifest_artifacts(repo:Path,package:Path):
    artifacts=[]; manifests=[]
    candidates=sorted(package.rglob("package-manifest.json"))+sorted(package.rglob("manifest.json"))
    for manifest in candidates:
        if manifest.is_symlink() or manifest.resolve()!=manifest:
            raise GovernanceError(f"Linked package manifest: {rel(repo,manifest)}")
        document=read_json(manifest)
        rows=[]
        if manifest.name=="package-manifest.json":
            if not isinstance(document,list):
                raise GovernanceError(f"Unsupported package manifest shape: {rel(repo,manifest)}")
            rows=document
        elif isinstance(document,dict) and isinstance(document.get("assets"),list):
            # Delivery manifests own exact file hashes on each asset row.
            rows=[row for row in document["assets"] if isinstance(row,dict)
                and isinstance(row.get("file"),str) and isinstance(row.get("sha256"),str)
                and type(row.get("bytes")) is int]
        else:
            continue
        manifest_path=rel(repo,manifest); manifests.append(manifest_path); seen=set()
        for row in rows:
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
                        try: actual_digest,actual_size=parse_pointer(prefix)
                        except ValueError: verification="invalid-pointer"
                        else: verification="pointer-match" if (actual_digest,actual_size)==(digest,size) else "mismatch"
                    else:
                        stream.seek(0); actual_size=target.stat().st_size
                        actual_digest=hashlib.file_digest(stream,"sha256").hexdigest()
                        verification="verified" if (actual_digest,actual_size)==(digest,size) else "mismatch"
            identity=sha((manifest_path+"\0"+target_name).encode())
            artifacts.append(ArtifactDeclaration(identity,target_name,manifest_path,digest,size,verification))
    return tuple(artifacts),tuple(manifests)

def _package_parts(repo:Path,package:Path):
    parts=[]
    def add(part_id,label,selectors,source,geometry_type,status,**kwargs):
        if not isinstance(part_id,str) or not part_id.strip(): return
        if not isinstance(label,str) or not label.strip(): label=str(part_id)
        normalized=[]
        for selector in selectors:
            if not isinstance(selector,str) or not selector.strip(): continue
            selected=selector
            try:
                candidate_path=source.parent/PurePosixPath(selector)
                if candidate_path.exists() and candidate_path.resolve()==candidate_path:
                    selected=rel(repo,candidate_path)
            except (OSError,ValueError):
                pass
            if selected not in normalized: normalized.append(selected)
        parts.append(PackagePart(part_id,label,tuple(normalized),rel(repo,source),geometry_type,status,
            kwargs.get("source_case"),kwargs.get("source_frame"),kwargs.get("parent_part_id"),
            tuple(kwargs.get("aliases",())),kwargs.get("license"),kwargs.get("derivation"),
            kwargs.get("attributes",{})))

    for manifest in sorted(package.rglob("manifest.json")):
        if manifest.is_symlink() or manifest.resolve()!=manifest: continue
        try: doc=read_json(manifest)
        except GovernanceError: continue
        if isinstance(doc,dict) and doc.get("format")=="whole-body-anatomy-parts":
            canonical=doc.get("canonical_to_assets",{})
            for concept_id in doc.get("canonical_ids",[]):
                row=canonical.get(concept_id,{})
                variants=row.get("variants",[])
                selectors=[row.get("primary"),row.get("overlay"),*(x.get("file") for x in variants)]
                label=concept_id.replace("-"," ").title()
                add(concept_id,label,selectors,manifest,"svg-schematic","illustrative",
                    source_frame=f"svg:{row.get('primary_view','unknown')}",aliases=(concept_id,),
                    derivation=doc.get("anatomy_state","normal-schematic"),
                    attributes={"primaryView":row.get("primary_view"),"variants":variants,
                      "overlay":row.get("overlay"),"geometryType":doc.get("geometry_type"),
                      "coordinateUnits":doc.get("coordinate_units")})
        elif isinstance(doc,dict) and isinstance(doc.get("assets"),list) and isinstance(doc.get("coordinates"),dict):
            coordinates=doc["coordinates"]
            for asset in doc["assets"]:
                if not isinstance(asset,dict): continue
                asset_id=asset.get("id"); name=asset.get("name",{})
                label=name.get("en",asset_id) if isinstance(name,dict) else str(name)
                case=asset.get("sourceCase")
                add(asset_id,label,(asset.get("file"),asset_id),manifest,"glb-component",
                    asset.get("status","declared"),source_case=case,
                    source_frame=f"{case}:scene" if case else None,aliases=tuple(asset.get("organIds",[])),
                    license=asset.get("license"),derivation=asset.get("provenance"),
                    attributes={"group":asset.get("group"),"sourceKind":asset.get("sourceKind"),
                      "coordinates":coordinates,"cutawaySupport":asset.get("cutawaySupport"),
                      "defaultVisible":asset.get("defaultVisible")})
                for node in asset.get("nodes",[]):
                    if not isinstance(node,dict): continue
                    node_id=node.get("anatomy_id"); node_name=node.get("name",node_id)
                    derivation=node.get("derivation","")
                    status="source-derived" if derivation=="source-derived" else "illustrative"
                    add(node_id,node_name,(node.get("name"),node_id,asset.get("file")),manifest,
                        "glb-node",status,source_case=case,
                        source_frame=f"{case}:scene" if case else None,parent_part_id=asset_id,
                        license=asset.get("license"),derivation=derivation,
                        attributes={"viewRole":node.get("view_role"),"cutawaySupport":asset.get("cutawaySupport")})

    for manifest in sorted(package.rglob("anatomy_manifest.json")):
        if manifest.is_symlink() or manifest.resolve()!=manifest: continue
        doc=read_json(manifest)
        if not isinstance(doc,list): continue
        for row in doc:
            if not isinstance(row,dict): continue
            part_id=row.get("anatomy_id")
            add(part_id,row.get("object",part_id),(row.get("object"),part_id),manifest,
                "blender-object","declared-component",
                attributes={"vertices":row.get("vertices"),"faces":row.get("faces"),
                  "shapeKeys":row.get("shape_keys",[]),"segmentationLabel":row.get("segmentation_label")})

    for key_file in sorted(package.rglob("explicit-region-key.json")):
        if key_file.is_symlink() or key_file.resolve()!=key_file: continue
        doc=read_json(key_file)
        for row in doc.get("rows",[]):
            if not isinstance(row,dict): continue
            node_id=row.get("source_atlas_node_id")
            mesh=row.get("source_mesh_name")
            role=row.get("illustrative_display_role")
            add(f"source-node:{node_id}",row.get("source_label") if row.get("source_label") not in (None,"-") else role,
                (mesh,str(node_id) if node_id is not None else None),key_file,"source-node-mapping",
                "illustrative",license=None,derivation=doc.get("role_mapping_method"),
                attributes={"sourceLabel":row.get("source_label"),"displayRole":role,
                  "sourceNodeType":row.get("source_node_type"),"materials":row.get("materials",[]),
                  "mappingId":doc.get("id"),"sourceAtlasSha256":doc.get("source_atlas_sha256"),
                  "legendScope":doc.get("legend_scope")})

    for key_file in sorted(package.rglob("layer-key.json")):
        if key_file.is_symlink() or key_file.resolve()!=key_file: continue
        doc=read_json(key_file); modes=doc.get("modes",{})
        supported={part for mode in doc.get("supportedModes",[]) for part in modes.get(mode,[])}
        diagnostic={part for mode in doc.get("diagnosticOnlyModes",[]) for part in modes.get(mode,[])}
        rejected={part for mode in doc.get("rejectedModes",[]) for part in modes.get(mode,[])}
        for layer,selectors in doc.get("layers",{}).items():
            status=("supported" if layer in supported else "diagnostic-only" if layer in diagnostic
                    else "rejected" if layer in rejected else "declared")
            add(f"layer:{layer}",layer.replace("_"," ").title(),selectors,key_file,
                "glb-node-set",status,aliases=(layer,),
                attributes={"supportedModes":[m for m,v in modes.items() if layer in v],
                  "diagnosticOnly":layer in diagnostic,"rejected":layer in rejected,
                  "supportedModesDeclared":doc.get("supportedModes",[]),
                  "diagnosticOnlyModesDeclared":doc.get("diagnosticOnlyModes",[]),
                  "rejectedModesDeclared":doc.get("rejectedModes",[]),"note":doc.get("note")})

    for inventory in sorted(package.rglob("source-inventory.json")):
        if inventory.is_symlink() or inventory.resolve()!=inventory: continue
        doc=read_json(inventory)
        if not isinstance(doc,list): continue
        for row in doc:
            if not isinstance(row,dict): continue
            name=row.get("name"); source_file=row.get("source_file")
            add(f"source-mesh:{name}",name,(source_file,name),inventory,
                Path(source_file or "").suffix.lstrip(".") or "source-mesh","source-input",
                attributes={"sourceSha256":row.get("source_sha256"),"vertices":row.get("vertices"),
                  "triangles":row.get("triangles"),"nativeBounds":row.get("native_bounds")})

    for build in sorted(package.rglob("ovary-tubal-context.build.json")):
        if build.is_symlink() or build.resolve()!=build: continue
        doc=read_json(build); checks=doc.get("checks",{})
        for name in checks.get("sourceNames",[]):
            add(f"source-mesh:{name}",name,(name,),build,"glb-source-node","source-derived",
                attributes={"sourceCommit":doc.get("sourceCommit"),"artifact":doc.get("artifact")})
    return tuple(parts)

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
            parts=_package_parts(repo,package)
            record=package/RECORD; status,unresolved=_record_status(repo,package)
            candidate="package:"+path
            if record.is_file(): candidate=read_json(record)["assetId"]
            if candidate in seen: raise GovernanceError(f"Duplicate asset identity: {candidate}")
            seen.add(candidate)
            kind={"models":"model-package","assemblies":"assembly-package","body":"body-package",
                  "heart":"heart-package","diagrams":"diagram-package","lessons":"lesson-package"}[root_name]
            result.append(Package(candidate,path,readme_title(readme,package.name),kind,readme_hash,exports,manifests,artifacts,parts,
                rel(repo,record) if record.is_file() else None,status,unresolved))
    return tuple(result)

def body_system_consumers(repo:Path):
    stop_path=owner_path(repo,BODY_STOPS)
    if not stop_path.is_file(): return ()
    stop_document=read_json(stop_path)
    stops=stop_document.get("stops")
    if not isinstance(stops,list): raise GovernanceError(f"Invalid Body Systems stops: {BODY_STOPS}")
    display_path=owner_path(repo,"lessons/body-systems/display/index.json")
    systems=read_json(display_path) if display_path.is_file() else []
    if not isinstance(systems,list): raise GovernanceError("Invalid Body Systems display index")
    by_system={}
    for system in systems:
        if not isinstance(system,dict): raise GovernanceError("Invalid Body Systems display system")
        system_id=system.get("id")
        if not isinstance(system_id,str) or not system_id.strip() or system_id in by_system:
            raise GovernanceError(f"Invalid or duplicate Body Systems display identity: {system_id}")
        by_system[system_id]=system
    result=[]; seen=set(); plates={}
    def paths_from_sources(rows):
        paths=[]
        for row in rows if isinstance(rows,list) else []:
            if not isinstance(row,list): continue
            for candidate in row[1:]:
                if isinstance(candidate,str) and not candidate.startswith(("https://","http://")):
                    try: normalized=source_path(candidate)
                    except ValueError: continue
                    paths.append(normalized)
        return list(dict.fromkeys(paths))
    def frame_records(plate,owner):
        frames=plate.get("frames",[])
        if not isinstance(frames,list): raise GovernanceError(f"Invalid display frames: {owner}")
        result=[]
        for frame in frames:
            if not isinstance(frame,dict): raise GovernanceError(f"Invalid display frame: {owner}")
            frame_path=frame.get("path")
            if not isinstance(frame_path,str): raise GovernanceError(f"Display frame has no path: {owner}")
            frame_path=source_path(frame_path)
            digest=frame.get("sourceSha256")
            if digest is not None and (not isinstance(digest,str) or not HEX64.fullmatch(digest)):
                raise GovernanceError(f"Invalid display source digest: {frame_path}")
            result.append({"path":frame_path,"angle":frame.get("angle"),
                "sourceSha256":digest,"available":owner_path(repo,frame_path).is_file()})
        return result
    for system_id,system in by_system.items():
        plates_for_system=system.get("plates",[])
        if not isinstance(plates_for_system,list): raise GovernanceError(f"Invalid plate list: {system_id}")
        plate_map={}
        for plate in plates_for_system:
            if not isinstance(plate,dict): raise GovernanceError(f"Invalid plate in {system_id}")
            plate_id,plate_kind=plate.get("id"),plate.get("kind")
            if not isinstance(plate_id,str) or not plate_id.strip() or not isinstance(plate_kind,str) or not plate_kind.strip():
                raise GovernanceError(f"Invalid plate identity in {system_id}: {plate_id}")
            key=(plate_kind,plate_id)
            if key in plate_map: raise GovernanceError(f"Duplicate plate identity in {system_id}: {key}")
            plate_map[key]=plate
        plates[system_id]=plate_map
        source_paths=paths_from_sources(system.get("sources",[]))
        assembly=next((p for p in plates_for_system if p.get("kind")=="assembly"),None)
        if assembly:
            frames=frame_records(assembly,system_id)
            result.append(Consumer(f"body-systems:assembly:{system_id}","body-systems","system-assembly",
                assembly.get("title",system.get("name",system_id)),
                system.get("function",system.get("detail","")),
                "assembly-described", "lessons/body-systems/display/index.json",
                {"systemId":system_id,"function":system.get("function"),"detail":system.get("detail"),
                 "limits":system.get("limit"),"status":system.get("status"),"overview":system.get("overview"),
                 "frames":frames,"framePaths":[x["path"] for x in frames],
                 "sourcePaths":source_paths,"legend":assembly.get("legend",[]),"scale":assembly.get("scale")}))
        for plate in plates_for_system:
            if plate.get("kind")=="assembly": continue
            frames=frame_records(plate,system_id)
            plate_id=plate["id"]
            result.append(Consumer(f"body-systems:plate:{system_id}:{plate_id}","body-systems","display-plate",
                f"{system.get('name',system_id)} · {plate.get('title',plate_id)}",
                system.get("detail",system.get("function","")),"plate-described",
                "lessons/body-systems/display/index.json",
                {"systemId":system_id,"plateId":plate_id,"plateKind":plate.get("kind"),
                 "frames":frames,"framePaths":[x["path"] for x in frames],
                 "sourcePaths":source_paths,"legend":plate.get("legend",[]),"scale":plate.get("scale"),
                 "limit":system.get("limit")}))
    for row in stops:
        if not isinstance(row,dict): raise GovernanceError(f"Invalid Body Systems stop: {BODY_STOPS}")
        system,detail,action,observation,status=(row.get(k) for k in ("system","detail","action","observation","status"))
        if not all(isinstance(v,str) and v.strip() for v in (system,detail,action,observation,status)):
            raise GovernanceError(f"Incomplete Body Systems stop: {BODY_STOPS}")
        identity=f"body-systems:{system}:{detail}"
        if identity in seen: raise GovernanceError(f"Duplicate consumer: {identity}")
        seen.add(identity)
        plate=plates.get(system,{}).get(("detail",detail))
        display_status="exact-display-detail" if plate else "unmapped-display-detail"
        frames=frame_records(plate,system) if plate else []
        system_row=by_system.get(system,{})
        result.append(Consumer(identity,"body-systems","reviewed-stop",f"{system.title()} · {detail}",action,
            "reviewed-"+status,BODY_STOPS,
            {"observation":observation,"reviewer":stop_document.get("reviewer"),"date":stop_document.get("date"),
             "detailId":detail,"displayStatus":display_status,
             "displayPlate":plate.get("title") if plate else None,
             "displayFrames":frames,"framePaths":[x["path"] for x in frames],
             "sourcePaths":paths_from_sources(system_row.get("sources",[])),
             "scopeLimit":system_row.get("limit")}))
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
            direct=[value for value in strings if value]
            if function in ("gap","rebuild"):
                if len(args)<4: continue
                offset=1 if args[0].strip().startswith(("'",'"')) else 0
                if len(direct)>=offset+3:
                    part,label,reason=direct[offset],direct[offset+1],direct[offset+2]
                    part_expression=None
                elif len(direct)>=2:
                    part_expression=args[1]
                    part="dynamic:"+part_expression
                    label,reason=direct[-2],direct[-1]
                else:
                    continue
                status="rebuild-required" if function=="rebuild" else "missing-required"
                extra={"part":part,"declaration":function,"line":line}
                if part_expression: extra["partExpression"]=part_expression
            else:
                if len(args)<5 or len(direct)<2: continue
                asset_id=direct[0] if len(direct)>=4 else None
                asset_label=direct[1] if len(direct)>=4 else None
                if len(direct)>=5:
                    part,label,reason=direct[2],direct[3],direct[4]
                    part_expression=None
                else:
                    part_expression=args[2]
                    part="dynamic:"+part_expression
                    label,reason=direct[-2],direct[-1]
                status="missing-required"
                extra={"part":part,"declaration":function,"line":line}
                if part_expression: extra["partExpression"]=part_expression
                if asset_id: extra["assetId"]=asset_id
                if asset_label: extra["assetLabel"]=asset_label
            identity=f"ultrasound:geometry-gap:{Path(filename).stem}:{line}:{call_index}:{part}"
            result.append(Consumer(identity,"ultrasound-anatomy","geometry-requirement",
                label,reason,status,filename,extra))
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

def teaching_consumers(repo:Path):
    """Expose exact accepted teaching assessments and maintained selections."""
    if not (repo/"reviews/teaching-assessments").is_dir():
        return ()
    current=CurrentTeaching(repo)
    result=[]
    for assessment in current.gallery():
        row=assessment.row
        export=row["export"]
        path=export["path"]
        selection=current.selections.get(path)
        selected=bool(selection and selection.task_id==assessment.task_id)
        target=row.get("target",{})
        status="selected" if selected else "accepted-alternative"
        if target.get("status")=="blocked": status="blocked-alternative"
        artifact_pins=[dict(claim) for claim in (export,*row.get("views",[]))]
        source_paths=[]
        for source in row.get("sources",[]):
            source_name=source.get("path") if isinstance(source,dict) else None
            if isinstance(source_name,str):
                source_name=source_name.split("#",1)[0]
                if source_name and not source_name.startswith(("https://","http://")):
                    source_paths.append(source_name)
        result.append(Consumer(
            f"teaching-assessment:{path}:{assessment.task_id}:{assessment.sha256[:12]}",
            "teaching-assessments","accepted-assessment",
            f"{Path(path).name} · {assessment.task_id}",row["task"],status,
            rel(repo,assessment.owner),
            {"export":export,"artifactPins":artifact_pins,"taskId":assessment.task_id,
             "assessmentSha256":assessment.sha256,"sources":row.get("sources",[]),
             "sourcePaths":source_paths,"views":row.get("views",[]),
             "teachingView":row.get("teachingView"),"axes":row.get("axes"),
             "target":target,"attribution":assessment.attribution,
             "collectionId":selection.collection_id if selected else None,
             "familyId":selection.family_id if selected else None}
        ))
    return tuple(result)

def build_catalog(repo:Path):
    repo=repo.resolve(); packages=scan_packages(repo)
    consumers=body_system_consumers(repo)+ultrasound_consumers(repo)+teaching_consumers(repo); hashes={}
    for item in consumers:
        path=owner_path(repo,item.source_path)
        hashes[item.source_path]=sha(path.read_bytes()) if path.is_file() else "missing"
        for source_name in (*item.evidence.get("sourcePaths",[]),*item.evidence.get("framePaths",[])):
            source=owner_path(repo,source_name)
            hashes[source_name]=sha(source.read_bytes()) if source.is_file() else "missing"
        for pin in item.evidence.get("artifactPins",[]):
            hashes["artifact:"+pin["path"]]=f"{pin['sha256']}:{pin.get('bytes',0)}"
    for item in packages:
        if item.readme_sha256: hashes[item.path+"/README.md"]=item.readme_sha256
        for manifest_name in item.manifests:
            manifest=owner_path(repo,manifest_name)
            hashes[manifest_name]=sha(manifest.read_bytes())
        for part_source in {part.source_path for part in item.parts}:
            source=owner_path(repo,part_source)
            hashes[part_source]=sha(source.read_bytes())
        if item.record_path:
            path=owner_path(repo,item.record_path); hashes[item.record_path]=sha(path.read_bytes())
    return Catalog(str(repo),packages,consumers,hashes)

def find(catalog:Catalog,query:str,domain:str|None=None):
    terms=tuple(x.casefold() for x in query.split() if x); packages=[]; consumers=[]
    for item in catalog.packages:
        part_terms=tuple(value for part in item.parts for value in (part.part_id,part.label,*part.selectors,*part.aliases))
        hay=" ".join((item.candidate_id,item.path,item.title,*item.exports,*part_terms)).casefold()
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

def resolve(catalog:Catalog,identity:str,part_id:str|None=None):
    """Resolve explicit consumer part tokens without anatomical-name inference."""
    consumer=show(catalog,identity)
    if consumer["type"]!="consumer-requirement":
        raise GovernanceError("Resolve requires a consumer identity, not a package identity")
    evidence=consumer.get("evidence",{})
    declared=evidence.get("parts",[])
    if part_id is not None:
        required=[part_id]
    elif isinstance(declared,list):
        required=list(dict.fromkeys(x for x in declared if isinstance(x,str) and x.strip()))
    else:
        required=[]
    if not required:
        return {"consumer":consumer,"status":"no-exact-part-contract",
          "reason":"This consumer does not declare machine-readable part selectors; no binding is inferred from prose."}
    case=evidence.get("case")
    results=[]
    mesh_types={"glb-component","glb-node","blender-object","stl","glb-source-node","glb-node-set"}
    eligible_states={"ready","source-derived","declared-component","supported","source-input"}
    for requested in required:
        exact=[];near=[];incompatible=[]
        for package in catalog.packages:
            for candidate in package.parts:
                tokens={candidate.part_id,*candidate.aliases,*candidate.selectors}
                if requested not in tokens: continue
                artifact_identities=[]
                for selector in candidate.selectors:
                    if selector not in package.exports: continue
                    try:
                        digest,size=declared_identity(Path(catalog.repository),selector)
                        target=owner_path(Path(catalog.repository),selector)
                        with target.open("rb") as stream: prefix=stream.read(80)
                        basis="lfs-pointer" if prefix.startswith(b"version https://git-lfs.github.com/spec/") else "local-bytes"
                        artifact_identities.append({"path":selector,"sha256":digest,"bytes":size,"identityBasis":basis})
                    except (OSError,ValueError) as error:
                        artifact_identities.append({"path":selector,"verification":"unavailable","reason":str(error)})
                item={"packageId":package.candidate_id,"packagePath":package.path,
                  "partId":candidate.part_id,"label":candidate.label,
                  "selectors":list(candidate.selectors),"sourcePath":candidate.source_path,
                  "geometryType":candidate.geometry_type,"status":candidate.status,
                  "sourceCase":candidate.source_case,"sourceFrame":candidate.source_frame,
                  "derivation":candidate.derivation,"license":candidate.license,
                  "parentPartId":candidate.parent_part_id,"attributes":candidate.attributes,
                  "artifactIdentities":artifact_identities,
                  "rightsStatus":"declared" if candidate.license else "unresolved",
                  "registrationStatus":"not-established",
                  "spatialStatus":"same-source-case-frame-unverified-transform" if case and candidate.source_case==case else "unverified"}
                if case and candidate.source_case and candidate.source_case!=case:
                    item["reason"]="Different source case"
                    incompatible.append(item);continue
                case_match=bool(case and candidate.source_case==case)
                geometry_match=candidate.geometry_type in mesh_types
                state_match=candidate.status in eligible_states
                if geometry_match and state_match and (not case or case_match):
                    item["matchBasis"]=["exact part selector"]
                    if case_match: item["matchBasis"].append("exact source-case identity")
                    exact.append(item)
                else:
                    reasons=[]
                    if not geometry_match: reasons.append("Not a 3D mesh/node delivery")
                    if not state_match: reasons.append("Part declaration is not in an eligible delivery state")
                    if case and not candidate.source_case: reasons.append("Source case is not declared")
                    item["reason"]="; ".join(reasons) or "Insufficient exact identity evidence"
                    near.append(item)
        status=("ambiguous" if len(exact)>1 else "exact-binding-candidate" if len(exact)==1
                else "near-match" if near else "missing")
        results.append({"requiredPart":requested,"status":status,
          "exactCandidates":exact,"nearMatches":near,"incompatibleCandidates":incompatible,
          "qualification":"not-established",
          "note":"An exact selector and source-case match is a candidate binding, not anatomical, registration, rights or teaching qualification."})
    return {"consumer":consumer,"sourceCase":case,"status":"resolved-candidates",
      "parts":results}

def impact(catalog:Catalog,identity:str):
    target=show(catalog,identity)
    if target["type"]=="consumer-requirement": return {"target":target,"knownConsumers":[target]}
    return {"target":target,"knownConsumers":[],"limitations":[
      "Package discovery does not prove an independent asset lineage.",
      "Consumer-to-asset bindings are not inferred from names or anatomical similarity.",
      "Unknown external readers cannot be inferred from this checkout."]}
