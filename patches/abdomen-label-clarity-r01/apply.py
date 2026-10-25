from pathlib import Path
import argparse,hashlib
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();src=Path(a.input);dst=Path(a.output)
b=src.read_bytes();assert hashlib.sha256(b).hexdigest()=='ac84480b9db8d0ce1306d6dd5462821ce15a2786be9a51c2538e4664b5c5040a', 'Baseline hash mismatch'
s=b.decode();s=s.replace('M381 405H360L342 416','M381 382H347L327 398')
# Exact label-only replacement guarded by output hash.
import re
s=re.sub(r'(<text[^>]*\by=")408("[^>]*>Stomach</text>)',r'\g<1>385\2',s)
b=s.encode();assert hashlib.sha256(b).hexdigest()=='e2d9ab4705a216c7d427eca8cfaf8f0064360d8eaa1a5661a208ecc4970fe656', 'Output hash mismatch'
with dst.open('xb') as f:f.write(b)
