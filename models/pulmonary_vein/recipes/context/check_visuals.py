"""Check native SVG/PNG image bindings and unchanged pixels outside editorial cues."""
import argparse
import base64
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageOps

if __package__:
    from .build import crop_box, inputs
    from .source import require, sha
else:
    from build import crop_box, inputs
    from source import require, sha

NS = {'s': 'http://www.w3.org/2000/svg'}
HREF = '{http://www.w3.org/1999/xlink}href'


def check(root, renders, output):
    record, _ = inputs(root, renders)
    build = json.loads((output / 'build.json').read_text())
    require(build['renderReceiptSha256'] == sha((renders / 'render.json').read_bytes()), 'Stale build receipt')
    expected = {v['view'] + '-' + v['state']: v for v in record['views']}
    reports = []
    for row in build['outputs']:
        svg = output / row['file']
        raw = svg.read_bytes()
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'SVG identity mismatch')
        doc = ET.fromstring(raw)
        require(not doc.findall('.//s:script', NS) and not doc.findall('.//s:foreignObject', NS), 'Unexpected active content')
        for image in doc.findall('./s:defs/s:image', NS):
            key = image.attrib['id'].removeprefix('image-')
            require(image.attrib['width'] == '900' and image.attrib['height'] == '700', 'Embedded image rescaled')
            href = image.attrib[HREF]
            require(href.startswith('data:image/png;base64,'), 'External or invalid image reference')
            payload = base64.b64decode(href.split(',', 1)[1], validate=True)
            require(sha(payload) == expected[key]['sha256'], 'Embedded PNG identity mismatch')
        png = svg.with_suffix('.png')
        actual = Image.open(png).convert('RGB')
        require(actual.size == (int(doc.attrib['width']), int(doc.attrib['height'])), 'Native export size differs')
        panels = []
        for panel in doc.findall('.//s:g[@data-view]', NS):
            view, state = panel.attrib['data-view'], panel.attrib['data-state']
            transform = panel.attrib['transform']
            require(transform.startswith('translate(') and transform.endswith(')'), 'Unexpected panel transform')
            x,y = map(int, transform[10:-1].split())
            use = panel.find('./s:use', NS)
            require(use.attrib[HREF] == '#image-' + view + '-' + state, 'Panel references the wrong visibility image')
            source = Image.open(renders / expected[view + '-' + state]['file']).convert('RGB')
            rendered = actual.crop((x, y, x+900, y+700))
            difference = ImageChops.difference(rendered, source)
            keep = Image.new('L', (900,700), 255)
            draw = ImageDraw.Draw(keep)
            # Side labels are editorial; compare all remaining source pixels.
            draw.rectangle((0,0,900,44), fill=0)
            if panel.find('./s:rect[@data-editorial="detail-crop"]', NS) is not None:
                a,b,w,h = crop_box()
                draw.rectangle((int(a)-3,int(b)-3,int(a+w)+3,int(b+h)+3), outline=0, width=8)
                draw.rectangle((int(a)-2,int(b)-36,int(a)+300,int(b)), fill=0)
            masked = Image.composite(difference, Image.new('RGB', source.size), keep)
            require(masked.getbbox() is None, 'Native export altered source pixels outside editorial cues')
            panels.append({'view':view,'state':state,'x':x,'y':y,'nonEditorialPixelsUnchanged':True})
        expected_panels = 4 if svg.name == 'pulmonary-vein-context.svg' else 2
        require(len(panels) == expected_panels, 'Missing comparison panel')
        reports.append({'svg':svg.name,'svgSha256':sha(raw),'png':png.name,
                        'pngSha256':sha(png.read_bytes()),'pngBytes':png.stat().st_size,'panels':panels})
    teaching = output / 'pulmonary-vein-context.png'
    gray = output / 'pulmonary-vein-context-grayscale.png'
    ImageOps.grayscale(Image.open(teaching)).save(gray)
    result = {'sourceSha256':record['source']['sha256'],'nativeRasterizer':'Inkscape 1.4',
              'checked':reports,'grayscale':{'file':gray.name,'sha256':sha(gray.read_bytes()),'bytes':gray.stat().st_size},
              'scope':'Exact embedded PNG bindings, native export dimensions and unchanged pixels outside editorial labels/crop cue. Grayscale created for visual inspection; not browser or anatomy validation.'}
    (output / 'visual-binding.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--renders',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(check(args.root,args.renders,args.output),indent=2))
