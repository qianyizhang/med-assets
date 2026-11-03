"""Guarded #207 delivery; no network and no write until every input/output validates."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
COMBINED=HERE.parents[1]/'comparison-navigation/r01'
BINDING=json.loads((HERE/'binding.json').read_text())
OLD="$('#candidate-choice').onchange=()=>showStudy($('#candidate-choice').value);"
NEW="$('#candidate-choice').onchange=()=>{const id=$('#candidate-choice').value;if(!data.candidates.some(c=>c.id===id))return;history.replaceState(null,'','#candidate-'+encodeURIComponent(id));showStudy(id);};"
def digest(raw):return hashlib.sha256(raw).hexdigest()
def apply(directory, mode='combined'):
 target=Path(directory)
 if mode not in BINDING['inputs']:raise ValueError('Choose combined or v45 explicitly')
 for name,expected in BINDING['inputs'][mode].items():
  if digest((target/name).read_bytes()) != expected:raise ValueError('Exact '+mode+' input required: '+name)
 if mode=='v45' and any((target/name).exists() for name in ('navigation-focus.mjs','comparison-state.mjs')):
  raise ValueError('Use a fresh v45 review directory')
 payload={}
 for name,expected in BINDING['combinedPayload'].items():
  raw=(COMBINED/name).read_bytes()
  if digest(raw)!=expected:raise ValueError('Preserved combined package mismatch: '+name)
  payload[name]=raw
 source=payload['review.js'].decode()
 if source.count(OLD)!=1:raise ValueError('Exact one handler required')
 payload['review.js']=source.replace(OLD,NEW).encode()
 for name,expected in BINDING['outputs'].items():
  if digest(payload[name])!=expected:raise ValueError('Reviewed output mismatch: '+name)
 outputs=payload if mode=='v45' else {'review.js':payload['review.js']}
 for name,raw in outputs.items():(target/name).write_bytes(raw)
 return {name:digest(raw) for name,raw in outputs.items()}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--mode',choices=['combined','v45'],required=True)
 a=p.parse_args();print(json.dumps(apply(a.directory,a.mode),indent=2))
