#!/usr/bin/env python3
"""Offline integrity/accounting checks only; does not certify anatomy or pixels."""
import hashlib,json,pathlib,collections
R=pathlib.Path(__file__).resolve().parents[2]
B=R/'reviews/accounting/2026-10-23'
def read(name):return json.loads((B/name).read_text())
d=read('baseline-decisions.json')['records'];q=read('metadata-equivalence.json')['records'];s=read('coverage-summary.json')
assert len(d)==28 and len(q)==16
assert len({r['assetId'] for r in d})==28
images={}
for r in d:
 assert r['changedGateNames']==['visual'] and r['candidateCountDelta']==0
 assert r['artifact']['sha256'] and r['artifact']['publicURL'].startswith('https://')
 for e in r['evidence']:
  p=(R/e['file']).resolve();assert p.is_relative_to(R)
  blob=p.read_bytes();assert hashlib.sha256(blob).hexdigest()==e['sha256']
  images[e['sha256']]=len(blob)
for r in q:
 assert r['candidateCountDelta']==0
 assert r['allNonJSONChunksByteIdentical'] and r['allJSONOutsideSceneExtrasDeepEqual']
 assert r['derivative']['pointerVerified'] and len(r['derivative']['remoteRef'])==40
 assert r['visual']['equivalentSourceSha256']==r['baselineSha256']
assert len(images)==32 and sum(images.values())==15764154
assert s['originalBaselines']==62 and sum(s['baselineVisualStates'].values())==62
assert s['separateScopedStudies']==35 and s['newStudies']==0
print(json.dumps({'baselineDecisions':28,'metadataEquivalenceLinks':16,'nativeImages':len(images),'nativeBytes':sum(images.values()),'scope':'Integrity and accounting only; no anatomy/runtime approval'}))
