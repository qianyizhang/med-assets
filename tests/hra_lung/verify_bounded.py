"""Verify declared local identities/references only; no fetch, rebuild or runtime test.
Default: manifest subset in a populated repository. --strict-package: isolated closure.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,struct,re,csv,io,math
ROOT=Path(__file__).resolve().parents[2]
REV='reviews/lung_pair/2026-10-24-bounded-migration'
SRC='sources/datasets/hra/lung-female-v1.3/bounded-migration-2026-10-24'
MANIFEST=REV+'/FILE-HASHES.json'
SOURCE_SHA='323d27bb76ba2c5b140ff31ad5190627eeb8d4e37cd220e4b541655d67789c1a'
CANDIDATE_SHA='966a4c225be028e616f6f813e8d4232582995a82b8121a42257c1be53087cb19'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--strict-package',action='store_true');args=parser.parse_args()
def sha(b):return hashlib.sha256(b).hexdigest()
def data(name):
 p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts,name
 f=ROOT/name;assert f.is_file() and not f.is_symlink(),name;assert ROOT.resolve() in f.resolve().parents,name
 if 'manifest' in globals() and name!=MANIFEST:assert name in manifest,('Undeclared dependency',name)
 return f.read_bytes()
def read(n):return json.loads(data(n))
manifest=read(MANIFEST);assert MANIFEST not in manifest
for n,r in manifest.items():b=data(n);assert len(b)==r['bytes'] and sha(b)==r['sha256'],n
transport=read(REV+'/transport-manifest.json');public=read(REV+'/selected-public-map.json');rec=read(REV+'/record.json');source=read(SRC+'/external-source-map.json');frame=read(SRC+'/source-frame.json');deps=read(SRC+'/dependency-manifest.json');hist=read(REV+'/historical-technical-scope.json');bytecheck=read(REV+'/local-byte-identity-check.json');camera=read(REV+'/camera-visibility.json')
assert transport['countDelta']==transport['gateDelta']==rec['countDelta']==rec['gateDelta']==0
assert transport['remoteAvailabilityChecked'] is False and transport['rawSourceBundled'] is False
assert len(transport['studies'])==len(public['studies'])==1
s=transport['studies'][0];p=public['studies'][0];t=s['transport']
assert s['assetId']==p['assetId']==rec['assetId']=='lung_pair'
assert s['variantId']==p['variantId']==rec['variantId']=='lung_pair__hra-female-normals-r02'
assert s['canonicalPath']==p['canonicalFile']==rec['model']['path']
assert s['recordPath']==REV+'/record.json'
assert t==p['candidateTransport'] and s['rawCandidate']==p['rawCandidate']==None
assert t['encoding']=='gzip' and t['decodeRequiredBeforeLFSUpload'] is True
assert t['decodedSha256']==CANDIDATE_SHA and t['decodedBytes']==23253972
assert t['storedSha256']=='a08968362745fa9f28024967e2fc2ed87ca9026ed3156888253cf60289e9b98e' and t['storedBytes']==9241597
b=data(s['canonicalPath']);assert sha(b)==CANDIDATE_SHA and len(b)==23253972
assert rec['model']['sha256']==CANDIDATE_SHA and rec['model']['bytes']==len(b)
assert struct.unpack_from('<4sII',b,0)==(b'glTF',2,len(b));n,k=struct.unpack_from('<II',b,12);assert k==0x4e4f534a;j=json.loads(b[20:20+n]);jsontext=b[20:20+n].decode()
assert not any(v in jsontext for v in ['/workspace/','/home/','/Users/'])
for block in j.get('buffers',[])+j.get('images',[]):assert 'uri' not in block or block['uri'].startswith('data:'),'External GLB URI'
assert len(j['nodes'])==75 and len(j['meshes'])==56 and len(j['accessors'])==172 and not j.get('animations',[])
mesh_names={n['name'] for n in j['nodes'] if 'mesh' in n};assert len(mesh_names)==56
assert rec['modelCount']==camera['modelCount']==1 and rec['gates']==p['gates'] and rec['scope']==p['scope']
assert rec['gates']=={'technical':'pass-with-limitations','visual':'passed','anatomy':'unreviewed','runtime':'unverified'}
assert rec['rebuildClosure'] is False and rec['gatesAreHistoricalUnchanged'] is True
assert rec['cameraContractAvailableInReviewData']==p['cameraContractAvailableInReviewData']==True
for path in [rec['sourceRecords']['manifest'],rec['sourceFrameRecord'],rec['historicalTechnicalScope'],rec['localByteCheck'],rec['cameraRecord'],deps['sourceMap'],deps['sourceFrame'],deps['includedReceiptSubset'],deps['includedCameraRecipe']]:data(path)
assert rec['sourceRecords']['externalRawSource'] is True and set(rec['sourceRecords']['componentNodeNames'])==mesh_names
assert source['sourceId']=='hra-lung-female-v1.3' and source['license']=='CC-BY-4.0'
raw=source['sourceGLB'];assert raw['sha256']==SOURCE_SHA and raw['bytes']==23253972 and raw['includedInDraft'] is False
assert raw['archive']==raw['archiveMember']==None and raw['url']=='https://cdn.humanatlas.io/digital-objects/ref-organ/lung-female/v1.3/assets/3d-vh-f-lung.glb'
assert source['freshSourceAvailabilityChecked'] is False
metadata=read(source['metadataRecord']);assert metadata['was_derived_from']['doi']==source['doi']=='https://doi.org/10.48539/HBM794.PKQV.978'
assert sha(data(source['metadataRecord']))==source['metadataSha256']=='577f1d0ceaaf20ed928472a13698ba4ec53d9cbf7c933690b35445ab2430047d'
assert sha(data(source['crosswalkRecord']))==source['crosswalkSha256']=='913d4edd95c75ae9e558bd64901bab20c0aaedb843964d713d0157a695569e98'
for path in [source['licenseRecord'],source['attributionRecord']]:data(path)
assert len(p['attribution'])==1
attribution=p['attribution'][0];ab=data(source['attributionRecord']);assert sha(ab)==attribution['sha256'] and len(ab)==attribution['bytes']
assert 'creativecommons.org/licenses/by/4.0' in metadata['license']
labels={r['node_name']:r for r in csv.DictReader(io.StringIO(data(source['crosswalkRecord']).decode()))}
components=source['components'];assert len(components)==56 and {c['nodeName'] for c in components}==mesh_names
for c in components:
 node=j['nodes'][c['nodeIndex']];assert node['name']==c['nodeName'] and node['mesh']==c['meshIndex'] and c['providerCrosswalk']==labels[c['nodeName']]
assert frame['exactCandidateSha256']==CANDIDATE_SHA and frame['exactSourceSha256']==SOURCE_SHA
assert frame['extraTranslationRotationScalingOrRegistration'] is False and frame['sourceFramePreserved'] is True
assert frame['nodeHierarchyTransformsPreserved'] is True and frame['animationCount']==0
assert frame['nativeProviderFrame']==camera['sourceFrame']==camera['viewerSubset']['coordinateFrame']
f=frame['nativeProviderFrame'];assert f['gltfUnits']=='metres' and f['gltfUp']=='+Y' and f['BlenderToGltf']=='(x, z, -y)'
assert deps['rawSource']==raw and deps['rawSourceIncluded'] is False and deps['portableRebuildClosure'] is False
assert deps['rawArchivesScenesAndHistoryCopied'] is False
assert hist['exactCandidateSha256']==CANDIDATE_SHA
h=hist['normalOnlyDerivative'];assert h['sourceSha256']==SOURCE_SHA and h['candidateSha256']==CANDIDATE_SHA
assert h['changedNormalRows']==1501 and h['changedBytes']==13746 and h['skippedGroupCount']==87
assert h['allChangedBytesWithinSelectedNormals'] and h['allJsonBytesIdentical'] and h['allNonNormalAccessorsByteIdentical']
assert hist['reportedTotals']=={'meshes':56,'rawVertices':517602,'faces':297097,'rawBoundaryEdges':493599,'diagnosticBoundaryEdges':6337,'diagnosticNonManifoldEdges':6341,'componentsWithOpenBoundaries':56,'extraRightTertiaryCartilageNonBoundaryNonManifoldEdges':4}
assert len(hist['meshStats'])==56 and {x['name'] for x in hist['meshStats']}==mesh_names
assert all(x['diagnosticWeldOnly1e7m']['boundaryEdges']>0 for x in hist['meshStats'])
assert hist['warnings']==rec['limitations']
assert bytecheck['sourceSha256']==SOURCE_SHA and bytecheck['candidateSha256']==CANDIDATE_SHA
assert bytecheck['changedBytes']==13746 and bytecheck['changedNormalRows']==1501
assert bytecheck['allJsonAndChunkHeaderBytesIdentical'] and bytecheck['allNonNormalAccessorsByteIdentical'] and bytecheck['allChangesWithinHistoricalSelectedNormalRows']
assert bytecheck['rawSourceIncluded'] is False and bytecheck['networkRequests']==0
assert camera['exactGLBSHA']==camera['viewerSubset']['exactGLBSHA']==CANDIDATE_SHA
for key,count in [('all_provider_geometry',56),('provider_airways_only',29),('left_source_lung',13),('right_source_lung',14)]:
 sc=camera['scopes'][key];names=set(sc['visibleMeshNames']);assert len(names)==count and names<=mesh_names and sc['hideOtherMeshNodes']
 for cam in sc['cameras']:
  r=cam['sourceImageReference'];assert r['includedInDraft'] is False and r['sha256']==cam['sourceImageSha256']
  assert r['repositoryPath'].endswith('/'+cam['sourceImage'])
  for k in ['gltfYUpCameraPosition','gltfYUpTarget','gltfYUpUp']:assert len(cam[k])==3 and all(math.isfinite(x) for x in cam[k])
  assert cam['orthographicVerticalSpanM']>0
for v in camera['viewerSubset']['views']:
 assert v['sourceEvidenceReference']['sha256']==v['source_evidence_sha256']
 assert set(v['hidden_for_inspection_only'])==mesh_names-set(camera['scopes'][v['mode']]['visibleMeshNames'])
# Every exported reference to a non-bundled artifact remains explicitly external.
def check_external(v):
 if isinstance(v,dict):
  if v.get('includedInDraft') is False:
   assert v.get('repositoryPath') and re.fullmatch('[0-9a-f]{64}',v['sha256']) and v['bytes']>0
   q=PurePosixPath(v['repositoryPath']);assert not q.is_absolute() and '..' not in q.parts
  for val in v.values():check_external(val)
 elif isinstance(v,list):
  for val in v:check_external(val)
for obj in [source,frame,deps,hist,bytecheck,camera,rec]:check_external(obj)
assert len(s['evidence'])==len(p['selectedEvidence'])==len(rec['evidence'])==3
unique={sha(b):len(b)};image_oids=set();comparisons=0
for e,original,compact in zip(rec['evidence'],p['selectedEvidence'],s['evidence']):
 assert all(e[key]==value for key,value in original.items()),original['id']
 assert e['originalNativeImageIncluded'] is False and e['originalNativeImageReference']['sha256']==e['originalSha256']
 assert e['originalNativeImageReference']['repositoryPath']==e['originalFile']
 assert compact['path']==e['retainedPath']
 for k in ['sha256','bytes','publicURL','selectionRole','role','reviewPhase','assetBinding','sourceBindings','originalSha256']:assert compact[k]==e.get(k)
 image=data(e['retainedPath']);assert sha(image)==e['sha256'] and len(image)==e['bytes'];assert image[:4]==b'RIFF' and image[8:12]==b'WEBP'
 unique[sha(image)]=len(image);image_oids.add(sha(image));assert e['sha256']!=e['originalSha256']
 assert e['selectionRole']=='candidate'
 if e['role']=='comparison':
  comparisons+=1;assert e['reviewPhase']=='comparison'
  assert e['assetBinding']=='comparison / historical association; not a single tested mesh'
  assert e['sourceBindings']==[{'role':'before','sha256':SOURCE_SHA},{'role':'after','sha256':CANDIDATE_SHA}]
 else:assert e['role']=='candidate' and e['reviewPhase']=='candidate' and e['assetBinding']==CANDIDATE_SHA and e['sourceBindings']==[]
assert comparisons==1 and len(image_oids)==3
assert len(unique)==transport['uniqueMediaOids']==4 and sum(unique.values())==transport['uniqueMediaBytes']==23422418
assert transport['uniqueCandidateDecodedBytes']==23253972 and transport['uniqueSelectedEvidenceBytes']==168446
assert sum(unique[x] for x in image_oids)==168446 and transport['uniqueStoredTransportPlusEvidenceBytes']==9410043
assert max(unique.values())<=25000000 and sum(unique.values())<=35000000
assert not any(PurePosixPath(n).suffix.lower() in {'.obj','.blend','.zip','.gz','.png'} for n in manifest)
for name in manifest:
 if name.endswith(('.json','.md','.csv','.txt')):
  text=data(name).decode();assert not any(x in text for x in ['/workspace/','/home/','/Users/','${WORKSPACE}']),name
 if name.endswith('.md'):
  for url in re.findall(r'\]\(([^)]+)\)',data(name).decode()):
   if url.startswith(('http:','https:','#')):continue
   target=((ROOT/name).parent/url.split('#')[0]).resolve();assert ROOT.resolve() in target.parents and target.is_file(),(name,url)
   assert str(target.relative_to(ROOT)) in manifest or str(target.relative_to(ROOT))==MANIFEST
if args.strict_package:
 actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and str(p.relative_to(ROOT))!=MANIFEST}
 assert actual==set(manifest),'Unlisted/missing isolated-package files'
print(json.dumps({'status':'PASS_LOCAL_DECLARED_FILE_IDENTITY_ONLY','mode':'strict-package' if args.strict_package else 'manifest-subset','files':len(manifest),'models':1,'selectedWebPs':3,'uniqueMediaOids':len(unique),'uniqueMediaBytes':sum(unique.values()),'comparisonEvidence':comparisons,'countDelta':0,'gateDelta':0,'rebuildClosure':False,'freshRemoteAvailability':False,'newAnatomyOrRuntimeValidation':False},indent=2))
