from pathlib import Path
import base64,hashlib,json,re,subprocess
if not __debug__:raise SystemExit("FAIL: optimized Python unsupported")
P=Path(__file__).parent
h=(P/'index.html').read_text();b=json.loads((P/'projection-binding.json').read_text());expected={'en':'0f7bc051b5fa7f45c8a393a1b2374dfffd571447e1f51e6fe490c43ad2620b9f','zh':'21d4a691d541ecd7c795aa84abf88fe2a57d3b7597946789a80ede4890378e0a'};assert b['input_plate_sha256']==expected;images=json.loads(re.search(r'const images=(.*?);const reduced=',h,re.S)[1]);assert set(images)=={'en','zh'}
for lang,encoded in images.items():
 assert hashlib.sha256(base64.b64decode(encoded)).hexdigest()==b['input_plate_sha256'][lang]
 assert hashlib.sha256((P/f'comparison-{lang}.png').read_bytes()).hexdigest()==expected[lang]
projection=json.loads((P/'projection.json').read_text())
assert projection['source_sha256']==b['source_scene_sha256']=='5f7947838971b88f2c29e992290086e21169eee2c72bb5394948e72aee4bad25'
assert set(projection['views'])==set(b['selected_projection'])=={'overview','detail'}
for view,y,hgt in [('overview',205,810),('detail',1180,630)]:
 obj=projection['views'][view]['objects'][b['selected_source_name']];vs=obj['vertices'];assert len(vs)==40 and len(obj['triangles'])==76
 centers=[[sum(vs[i+j][k] for j in range(8))/8 for k in range(2)] for i in range(0,40,8)]
 assert centers==b['selected_projection'][view]['ring_centers_normalized']
 assert [[800+x*648,y+z*hgt] for x,z in centers]==b['selected_projection'][view]['panel_points']
assert len(re.findall(r'<path mask="url\(#cap-safe\)" class="flow"',h))==2
assert len(re.findall(r'<circle .*?r="9" fill="black"',h))==4
for view,proof in b['selected_projection'].items():
 pts=proof['panel_points'];d='M '+' L '.join(f'{x:.6f} {y:.6f}' for x,y in pts);assert f'id="{view}-flow" d="{d}"' in h
 assert len(pts)==5 and pts[0][1]>pts[-1][1]
 assert proof['rings']==5 and proof['ring_vertices']==8 and proof['triangles']==76
assert b['source_object_count']==7 and b['total_triangles']==372
assert 'animation-play-state:paused;opacity:0' in h
assert not re.search(r'<script[^>]+src=|<iframe|fetch\(',h)
subprocess.run(['node',str(P/'check_controls.js')],check=True)
print('PASS exact accepted EN/中文 plate hashes, two selected-only five-ring paths, cap-exclusion masks and static fallback; no browser pass')
