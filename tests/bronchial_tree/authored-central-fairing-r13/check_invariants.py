import argparse,pathlib,json,hashlib,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);a=ap.parse_args();P=pathlib.Path(__file__).resolve().parent;W=pathlib.Path(a.work);z=np.load(W/'vertex-invariants.npz');b=z['baseline'];c=z['candidate'];w=z['weights'];rows=[]
for row in json.loads((P/'terminal-witnesses.json').read_text()):
 mask=np.linalg.norm(b-np.array(row['authored_recipe_position']),axis=1)<.006;rows.append({'name':row['name'],'vertices_within6mm':int(mask.sum()),'exact':bool(np.array_equal(b[mask],c[mask]))})
r={'terminal_neighborhoods':rows,'all16_terminal_neighborhoods_exact':len(rows)==16 and all(x['exact'] for x in rows),'outside_support_exact':bool(np.array_equal(b[w==0],c[w==0])),'protected_regions':[]}
for name,center in [('accepted_left',[.042,.008,.068]),('unmodified_right',[-.042,.008,.033])]:
 mask=np.linalg.norm(b-np.array(center),axis=1)<.012;r['protected_regions'].append({'name':name,'vertices':int(mask.sum()),'exact':bool(np.array_equal(b[mask],c[mask]))})
assert r['all16_terminal_neighborhoods_exact'] and r['outside_support_exact'] and all(x['exact'] for x in r['protected_regions']);print(json.dumps(r,indent=2))
