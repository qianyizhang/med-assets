"""Rebuild the phase-matched teaching sheet from a source-verified Commons WebM."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image


def rebuild(record, original, output):
    if hashlib.sha256(original.read_bytes()).hexdigest() != record['sourceSha256']:
        raise ValueError('Unexpected source cine')
    w, h = record['tileWidth'], record['tileHeight']
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(original), '-vf',
                                    f'scale={w}:{h}:flags=lanczos', '-pix_fmt', 'rgb24',
                                    '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'])
    stride = w * h * 3
    frames = record['sourceFrames']
    columns = record['columns']
    sheet = Image.new('RGB', (columns * w, ((len(frames) + columns - 1) // columns) * h))
    for i, frame in enumerate(frames):
        tile = Image.frombytes('RGB', (w, h), data[frame * stride:(frame + 1) * stride])
        sheet.paste(tile, ((i % columns) * w, (i // columns) * h))
    sheet.save(output, format='WebP', quality=88, method=6)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('view')
    p.add_argument('original', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    manifest = json.loads((Path(__file__).parent / 'sources.json').read_text())
    rebuild(manifest['cine'][args.view], args.original, args.output)
