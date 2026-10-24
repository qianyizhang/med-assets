"""Local declared-file identity/role/source-reference checks; no downloads or rebuild.
Default mode checks only this manifest. --strict-package checks isolated closure.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,struct,re
ROOT=Path(__file__).resolve().parents[2]
REV='reviews/intestines/2026-10-24-bounded-migration'
SOURCE='sources/datasets/bodyparts3d/bowel-studies-4.0'
MANIFEST=REV+'/FILE-HASHES.json'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--strict-package',action='store_true');args=parser.parse_args()
def data(name):
 p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts,name
 f=ROOT/name;assert f.is_file() and not f.is_symlink(),name;assert ROOT.resolve() in f.resolve().parents,name
 return f.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def read(name):return json.loads(data(name))
checks=read(MANIFEST)
for name,rec in checks.items():
 b=data(name);assert len(b)==rec['bytes'] and sha(b)==rec['sha256'],name
assert MANIFEST not in checks
transport=read(REV+'/transport-manifest.json');public=read(REV+'/selected-public-map.json');source=read(SOURCE+'/external-source-map.json');dependencies=read(SOURCE+'/dependency-manifest.json');frame=read(SOURCE+'/source-frame.json');hist=read(REV+'/historical-exterior-checks.json')
assert transport['countDelta']==transport['gateDelta']==0
assert transport['remoteAvailabilityChecked'] is False and transport['rawSourceBundled'] is False
assert len(transport['studies'])==len(public['studies'])==2
assert frame['rawMmToGltfMetres']==[[.001,0,0,0],[0,0,.001,0],[0,-.001,0,0],[0,0,0,1]] and frame['extraTranslationRotationOrFit'] is False
assert source['archive']['sha256']=='9fbc713fffeee924a5a657d9813d84d7eb957bded63adb854931dd5e3eb61c97'
assert source['archive']['includedInDraft'] is False and '/LATEST/' in source['archive']['url']
assert source['license']=='CC-BY-4.0';data(source['licenseRecord'])
members={r['id']:r for r in source['components']};assert len(members)==64
for r in members.values():assert r['includedInDraft'] is False and r['archiveMember'].endswith('/'+r['id']+'.obj') and len(r['sha256'])==64
groups=source['exportComponentIds'];assert len(groups['small-intestine'])==56 and len(groups['large-intestine'])==8
assert set(groups['small-intestine']).isdisjoint(groups['large-intestine'])
assert set(groups['small-intestine'])|set(groups['large-intestine'])==set(members)
assert 'FJ2599' in groups['small-intestine'] and 'FJ2599' not in groups['large-intestine']
assert len(source['referenceOnlyComponents'])==1 and source['referenceOnlyComponents'][0]['id']=='FJ2564'
assert source['referenceOnlyComponents'][0]['exportedInEitherBowel'] is False
data(dependencies['sourceMap']);data(dependencies['sourceFrame'])
for s in dependencies['studies']:
 data(s['sourceRecords']['manifest']);assert s['rawSourceIncluded'] is False
 assert s['historicalSourceFrameExportReceipt']['includedInDraft'] is False
for ref in dependencies['historicalSharedRecipes']:assert ref['includedInDraft'] is False
seen={};image_oids=set();baseline_bindings=set();decoded_bytes=0;stored_bytes=0
for s in transport['studies']:
 p=next(x for x in public['studies'] if x['variantId']==s['variantId']);assert s['transport']==p['candidateTransport'] and s['rawCandidate']==p['rawCandidate']
 assert s['rawCandidate'] is None and s['transport']['encoding']=='gzip' and s['transport']['decodeRequiredBeforeLFSUpload'] is True
 b=data(s['canonicalPath']);assert sha(b)==s['transport']['decodedSha256'] and len(b)==s['transport']['decodedBytes'];seen[sha(b)]=len(b);decoded_bytes+=len(b);stored_bytes+=s['transport']['storedBytes']
 assert struct.unpack_from('<4sII',b,0)==(b'glTF',2,len(b));n,k=struct.unpack_from('<II',b,12);assert k==0x4e4f534a;doc=json.loads(b[20:20+n]);txt=b[20:20+n].decode()
 assert not any(v in txt for v in ['/workspace/','/home/','/Users/'])
 for block in doc.get('buffers',[])+doc.get('images',[]):assert 'uri' not in block or block['uri'].startswith('data:'),'External GLB URI'
 organ=s['canonicalPath'].split('/')[1];animations=[a.get('name') for a in doc.get('animations',[])];assert animations==(['BreathingSupport_4s'] if organ=='small-intestine' else [])
 rec=read(s['recordPath']);assert rec['gates']==p['gates'] and rec['scope']==p['scope'] and rec['rebuildClosure'] is False
 assert rec['model']['sha256']==sha(b) and rec['cameraContractAvailableInReviewData'] is False
 assert rec['sourceRecords']['externalRawSource'] is True and rec['sourceRecords']['componentIds']==groups[organ]
 for name in [rec['sourceRecords']['manifest'],rec['sourceFrameRecord'],rec['historicalExteriorChecks']]:data(name)
 assert rec['priorReviewIdentity']['includedInDraft'] is False and rec['historicalModificationReceipt']['includedInDraft'] is False
 assert hist['studies'][organ]['sha256']==sha(b)
 assert hist['studies'][organ]['reportedConnectedComponents']==(55 if organ=='small-intestine' else 10)
 assert len(rec['evidence'])==len(p['selectedEvidence'])==len(s['evidence'])==3
 for e,original,compact in zip(rec['evidence'],p['selectedEvidence'],s['evidence']):
  assert all(e[key]==value for key,value in original.items()),original['id']
  assert e['originalNativeImageIncluded'] is False
  assert compact['path']==e['retainedPath'] and compact['assetBinding']==e['assetBinding']
  image=data(e['retainedPath']);assert sha(image)==e['sha256'] and len(image)==e['bytes'];assert image[:4]==b'RIFF' and image[8:12]==b'WEBP';seen[sha(image)]=len(image);image_oids.add(sha(image))
  assert e['sha256']!=e['originalSha256']
  if e['selectionRole']=='before':assert e['reviewPhase']=='baseline' and e['assetBinding']!=sha(b);baseline_bindings.add(e['assetBinding'])
  else:assert e['reviewPhase']=='candidate' and e['assetBinding']==sha(b)
assert baseline_bindings=={'b587a571ba7105147e068488b6827634fe2b0f176fed1c4b73665c1958354564','2db0e5193d86f51a83d95df5c3841377aa823d51585a45dbdbd49e6cd92455b0'}
assert len(seen)==transport['uniqueMediaOids']==8 and len(image_oids)==6
assert sum(seen.values())==transport['uniqueMediaBytes']==10712382
assert decoded_bytes==transport['uniqueCandidateDecodedBytes']==10248568
assert sum(seen[x] for x in image_oids)==transport['uniqueSelectedEvidenceBytes']==463814
assert stored_bytes+transport['uniqueSelectedEvidenceBytes']==transport['uniqueStoredTransportPlusEvidenceBytes']
assert not any(PurePosixPath(n).suffix.lower() in {'.obj','.blend','.zip','.gz'} for n in checks)
for name in checks:
 if name.endswith('.md'):
  for url in re.findall(r'\]\(([^)]+)\)',data(name).decode()):
   if url.startswith(('http:','https:','#')):continue
   target=((ROOT/name).parent/url.split('#')[0]).resolve();assert ROOT.resolve() in target.parents and target.is_file(),(name,url)
if args.strict_package:
 actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and str(p.relative_to(ROOT))!=MANIFEST}
 assert actual==set(checks),'Unlisted/missing isolated-package files'
print(json.dumps({'status':'PASS_LOCAL_DECLARED_FILE_IDENTITY_ONLY','mode':'strict-package' if args.strict_package else 'manifest-subset','files':len(checks),'models':2,'selectedWebPs':6,'uniqueMediaOids':len(seen),'uniqueMediaBytes':sum(seen.values()),'distinctBaselineBindings':len(baseline_bindings),'sourceMemberRecords':len(members),'referenceOnlyMembers':1,'countDelta':0,'gateDelta':0,'rebuildClosure':False,'freshRemoteAvailability':False,'newAnatomyOrRuntimeValidation':False},indent=2))
