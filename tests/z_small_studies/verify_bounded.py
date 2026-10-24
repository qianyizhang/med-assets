"""Local declared-file identity checks only. No network, render or quality review.
Default scope is this manifest, not the whole repository. --strict-package is optional.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[2]
RV='reviews/z-small-studies/2026-10-24-bounded-migration'
SR='sources/datasets/z-anatomy/small-static-studies'
MANIFEST=RV+'/FILE-HASHES.json'
args=argparse.ArgumentParser(description=__doc__);args.add_argument('--strict-package',action='store_true');args=args.parse_args()
def blob(name):
 p=PurePosixPath(name)
 assert not p.is_absolute() and '..' not in p.parts,name
 f=R/name;assert f.is_file() and not f.is_symlink(),name
 assert R.resolve() in f.resolve().parents,name
 return f.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def read(name):return json.loads(blob(name))
checks=read(MANIFEST)
for name,rec in checks.items():
 b=blob(name);assert len(b)==rec['bytes'] and sha(b)==rec['sha256'],name
assert MANIFEST not in checks
t=read(RV+'/transport-manifest.json');p=read(RV+'/selected-public-map.json')
assert t['countDelta']==0 and t['gateDelta']==0 and t['remoteAvailabilityChecked'] is False
assert t['sourceGeometryBundled'] is False
assert len(t['studies'])==len(p['studies'])==3
seen={};baselines=set();selected_oids=set();stored_bytes=0;decoded_bytes=0
for s in t['studies']:
 original=next(x for x in p['studies'] if x['variantId']==s['variantId'])
 assert s['transport']==original['candidateTransport'] and s['rawCandidate']==original['rawCandidate']
 assert s['rawCandidate'] is None and s['transport']['encoding']=='gzip'
 assert s['transport']['decodeRequiredBeforeLFSUpload'] is True
 model=blob(s['canonicalPath']);assert sha(model)==s['transport']['decodedSha256'] and len(model)==s['transport']['decodedBytes']
 assert struct.unpack_from('<4sII',model,0)==(b'glTF',2,len(model))
 n,k=struct.unpack_from('<II',model,12);assert k==0x4e4f534a;glbdoc=json.loads(model[20:20+n]);text=model[20:20+n].decode()
 assert not any(x in text for x in ['/workspace/','/home/','/Users/'])
 for block in glbdoc.get('buffers',[])+glbdoc.get('images',[]):
  assert 'uri' not in block or block['uri'].startswith('data:'),'Unbundled GLB URI'
 seen[sha(model)]=len(model);decoded_bytes+=len(model);stored_bytes+=s['transport']['storedBytes']
 record=read(s['recordPath']);assert record['gates']==original['gates'] and record['scope']==original['scope']
 assert record['rebuildClaim'] is False and record['model']['sha256']==sha(model)
 assert record['cameraContractAvailableInReviewData'] is False
 assert len(record['evidence'])==len(s['evidence'])==len(original['selectedEvidence'])
 for e,o,compact in zip(record['evidence'],original['selectedEvidence'],s['evidence']):
  assert all(e[key]==val for key,val in o.items()),o['id']
  assert compact['path']==e['retainedPath'] and compact['assetBinding']==e['assetBinding']
  b=blob(e['retainedPath']);assert sha(b)==e['sha256'] and len(b)==e['bytes']
  assert b[:4]==b'RIFF' and b[8:12]==b'WEBP'
  seen[sha(b)]=len(b);selected_oids.add(sha(b))
  if e['selectionRole']=='before':
   assert e['reviewPhase']=='baseline' and e['assetBinding']!=sha(model);baselines.add(e['assetBinding'])
  else:assert e['reviewPhase']=='candidate' and e['assetBinding']==sha(model)
assert baselines=={'203b1bb112005a9ff5a3e70d00eb91ba225d21772e425b9ad4ae973221d98ea1','7195a11653c274e6cecfc72093579615a5c0fdd5a840a8bd661dd5dfb7c57457'}
assert len(selected_oids)==8 and len(seen)==t['uniqueMediaOids']==11
assert sum(seen.values())==t['uniqueMediaBytes']==2954416
assert decoded_bytes==t['uniqueCandidateDecodedBytes']==2697104
assert sum(seen[x] for x in selected_oids)==t['uniqueSelectedEvidenceBytes']==257312
assert stored_bytes+t['uniqueSelectedEvidenceBytes']==t['uniqueStoredTransportPlusEvidenceBytes']
d=read(SR+'/dependency-manifest.json');source=d['sharedExternalSource']
assert source['includedInDraft'] is False
assert source['archive_commit']=='bb293be456f6d2245191f37752d14ec76894740d'
assert source['archive_sha256']=='e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736'
assert source['member_sha256']=='9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd'
assert all(s['sourceGeometryIncluded'] is False for s in d['studies'])
assert not any(PurePosixPath(n).suffix.lower() in {'.obj','.blend','.zip','.gz'} for n in checks)
if args.strict_package:
 actual={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and str(p.relative_to(R))!=MANIFEST}
 assert actual==set(checks),'Unlisted or missing isolated-package files'
print(json.dumps({'status':'PASS_LOCAL_DECLARED_FILE_IDENTITY_ONLY','mode':'strict-package' if args.strict_package else 'manifest-only','files':len(checks),'models':3,'selectedWebPs':8,'uniqueMediaOids':len(seen),'uniqueMediaBytes':sum(seen.values()),'distinctBaselineBindings':len(baselines),'countDelta':0,'gateDelta':0,'sourceRebuildClosure':False,'freshRemoteAvailabilityChecked':False,'clinicalOrRuntimeValidation':False},indent=2))
