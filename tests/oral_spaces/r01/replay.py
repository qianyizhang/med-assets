import argparse,pathlib,json,hashlib,subprocess,xml.etree.ElementTree as E
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[3];T=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();O=pathlib.Path(a.out)
for f,h in json.loads((T/'input-hashes.json').read_text()).items():
 p=P/f;assert hashlib.sha256(p.read_bytes()).hexdigest()==h, f+' input hash mismatch'
# Probe local dependency before creating output. No installations or network actions.
version=subprocess.run(['inkscape','--version'],check=True,capture_output=True,text=True).stdout.strip();O.mkdir(exist_ok=False)
rows=[]
for lang in ['en','zh']:
 src=P/f'diagrams/oral_spaces/exports/r01/oral-spaces-{lang}.svg';root=E.parse(src).getroot();assert not root.findall('.//{http://www.w3.org/2000/svg}text')
 for el in root.iter():
  assert el.tag.rsplit('}',1)[-1] not in ['script','foreignObject','image']
  assert not any(k.rsplit('}',1)[-1]=='href' for k in el.attrib)
 out=O/f'oral-spaces-{lang}.png';subprocess.run(['inkscape',str(src),'--export-type=png','--export-filename='+str(out)],check=True,capture_output=True)
 im=Image.open(out).convert('RGBA');im.save(out);expected=Image.open(src.with_suffix('.png')).convert('RGBA');exact=im.size==expected.size and im.tobytes()==expected.tobytes();assert exact,'Rendered pixel mismatch'
 rows.append({'language':lang,'size':list(im.size),'decoded_pixels_exact':exact,'svg_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(O/'receipt.json').write_text(json.dumps({'inkscape':version,'rows':rows,'scope':'Actual outlined SVG rendering replay; not clinical or browser validation.'},indent=2))
