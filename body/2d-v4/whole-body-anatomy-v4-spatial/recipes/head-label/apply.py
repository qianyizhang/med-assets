from pathlib import Path
import xml.etree.ElementTree as E
import argparse,hashlib
q=argparse.ArgumentParser();q.add_argument('--input',required=True);q.add_argument('--output',required=True);a=q.parse_args();src=Path(a.input);dst=Path(a.output)
b=src.read_bytes();assert hashlib.sha256(b).hexdigest()=='f5f24baa9ae973ebed4a29fb32d7bc084d972c47d2e255cfdc021f28d5ca4d31','Baseline hash mismatch'
s=b.decode()
# Restricted exact replacements, preserving source serialization everywhere else.
changes=[('font-size="11" text-anchor="start" data-en="Parotid"','font-size="15" text-anchor="start" data-en="Parotid"'),('font-size="10.5" text-anchor="start" data-en="Sublingual"','font-size="15" text-anchor="start" data-en="Sublingual"'),('x="552" y="391" fill="#52665e" font-size="11"','x="552" y="417" fill="#52665e" font-size="15"'),('M601 362H620L655 290','M609 362H620L655 290'),('M637 387L687 335','M663 412L691 340'),('x="555" y="437"','x="555" y="453"'),('M696 420L700 342','M708 438L708 344')]
for old,new in changes:
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
# Only annotation-group leader styles. No organ/source geometry touched.
a=s.index('<g id="head-inset-labels"');s=s[:a]+s[a:].replace('stroke="#aab9ae" stroke-width="0.95"','stroke="#71877a" stroke-width="1.2"').replace('stroke="#b6c0b1" stroke-width="0.8"','stroke="#71877a" stroke-width="1.2"')

for en,zh in [('Parotid','腮腺'),('Sublingual','舌下腺'),('Submandibular','颌下腺')]:
 s=s.replace(f'data-en="{en}" data-zh="{zh}" class="view-note"',f'data-en="{en}" data-zh="{zh}" class="anatomy-label"')
b=s.encode();assert hashlib.sha256(b).hexdigest()=='3adf6a2799a5e247f86637695a516084f4beca2d3558668daea07c9c49518699','Output hash mismatch'
with dst.open('xb') as f:f.write(b)
