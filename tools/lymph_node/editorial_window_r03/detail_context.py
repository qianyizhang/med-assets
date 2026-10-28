"""Pair retained lymph-node detail pixels with their whole-organ context."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DETAIL_SHA = '82f379c1c561a855e47a999450a2560e1dc9c868272111262be19e338a1ed74a'
CONTEXT_SHA = '71d38b391d98ee55234070ae009b07b07d72bc0c2cfb4ccb73134b925b053591'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--detail', type=Path, required=True)
    p.add_argument('--context', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    for path, expected in ((a.detail, DETAIL_SHA), (a.context, CONTEXT_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Wrong reviewed image: '+str(path))
    if a.output.exists():
        raise FileExistsError('Refuse to overwrite review evidence')
    detail = Image.open(a.detail).convert('RGB')
    context = Image.open(a.context).convert('RGB')
    if detail.size != (2200,1040) or context.size != (2100,670):
        raise ValueError('Unexpected reviewed image size')
    image = Image.new('RGB', (2200,1900), '#192127')
    d = ImageDraw.Draw(image)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 25)
    d.text((20,15),'Whole-organ orientation: intact source / r02 / r03',font=f,fill='white')
    image.paste(context,(50,55))
    d.text((20,753),'Matched local detail: r02 / r03. Cropped view needs the context above.',font=f,fill='white')
    image.paste(detail,(0,795))
    d.text((20,1850),'Editorial omission only. Source vascular network (identity unresolved); anatomy, clinical and runtime gates remain open.',font=f,fill='#e9d19b')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    image.save(a.output)
    print(json.dumps({'detailSha256':DETAIL_SHA,'contextSha256':CONTEXT_SHA,
        'outputSha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),
        'scope':'Retained image pixels are paired, not modified or interpreted as physiological openings.'}))

if __name__ == '__main__': main()
