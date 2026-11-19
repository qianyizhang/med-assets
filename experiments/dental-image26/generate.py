"""Request native GIF shots; never synthesize their animation locally."""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent


def specification():
    return json.loads((ROOT / 'stories.json').read_text())


def prompt(spec, shot):
    return f"{spec['visual_direction']}\nStarting state: {shot['start']}\nAnimate: {shot['action']}"


def validate_gif(content, settings):
    if content[:6] not in (b'GIF87a', b'GIF89a'):
        raise ValueError('Response is not GIF bytes')
    with Image.open(io.BytesIO(content)) as animation:
        expected = tuple(map(int, settings['size'].split('x')))
        if animation.size != expected or animation.n_frames != settings['frame_count']:
            raise ValueError('Unexpected GIF dimensions or frame count')
        frames = []
        duration = 0
        for index in range(animation.n_frames):
            animation.seek(index)
            delay = animation.info.get('duration', 0)
            if delay != settings['frame_duration_ms']:
                raise ValueError('Unexpected frame duration')
            duration += delay
            frames.append(animation.convert('RGB').copy())
        changed = sum(ImageChops.difference(a, b).getbbox() is not None
                      for a, b in zip(frames, frames[1:]))
        if changed < 2:
            raise ValueError('GIF has insufficient changing frames')
        return {'frames': len(frames), 'seconds': duration / 1000,
                'changed_transitions': changed, 'size': expected}


def decode_response(result, settings):
    if not isinstance(result, dict):
        raise ValueError('API result is not an object')
    data = result.get('data')
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError('API result must contain one image')
    encoded = data[0].get('b64_json')
    if not isinstance(encoded, str):
        raise ValueError('API result has no base64 image')
    content = base64.b64decode(encoded, validate=True)
    validate_gif(content, settings)
    return content


def read_key(path):
    if path:
        for line in path.read_text().splitlines():
            match = re.fullmatch(r'\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.*?)\s*', line)
            if match:
                value = match[1].strip().strip('\"\'')
                if value:
                    return value
        raise ValueError('Authorized env file has no OPENAI_API_KEY')
    value = os.environ.get('OPENAI_API_KEY')
    if not value:
        raise ValueError('OPENAI_API_KEY is not configured')
    return value


def write_scripts(spec):
    lines = ['# Five dental movie scripts', '',
             'Original generated illustration experiment; explanatory, not a clinical protocol.', '',
             'Each GIF is 16 frames × 400 ms = 6.4 s. The edit plays it once, then holds',
             'the final frame if needed for narration. Each story adds a title and takeaway.', '',
             '## Shared production prompt', '', spec['visual_direction'], '',
             'All shot prompts below are appended to this shared prompt verbatim.', '']
    for story in spec['stories']:
        lines += [f"## {story['title']}", '',
                  f"**Condition → procedure:** {story['condition']} → {story['procedure']}.", '',
                  story['premise'], '', f"**Source:** {story['source']}", '',
                  f"**Chunks:** {len(story['shots'])}. **Takeaway:** {story['takeaway']}", '']
        for shot in story['shots']:
            lines += [f"### {shot['id']} — {shot['title']}", '',
                      f"**Caption:** {shot['caption']}", '',
                      f"**Narration:** {shot['narration']}", '',
                      '**GIF prompt continuation:**', '',
                      f"Starting state: {shot['start']}", '',
                      f"Animate: {shot['action']}", '',
                      f"**Visual acceptance checks:** {shot['review']}", '']
    (ROOT / 'SCRIPTS.md').write_text('\n'.join(lines))


def request_shot(spec, shot, key, output):
    target = output / 'gifs' / f"{shot['id']}.gif"
    if target.exists():
        summary = validate_gif(target.read_bytes(), spec['request'])
        print(json.dumps({'shot': shot['id'], 'reused': True, **summary}), flush=True)
        return
    payload = dict(spec['request'], model=spec['model'], prompt=prompt(spec, shot))
    req = urllib.request.Request('https://api.openai.com/v1/images/generations',
                                 data=json.dumps(payload).encode(),
                                 headers={'Authorization': f'Bearer {key}',
                                          'Content-Type': 'application/json'})
    print(f"Requesting {shot['id']}; no automatic retries", flush=True)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=420) as response:
            result = json.load(response)
        content = decode_response(result, spec['request'])
    except urllib.error.HTTPError as error:
        # Do not persist response bodies or headers: they may contain private data.
        raise RuntimeError(f"{shot['id']}: API HTTP {error.code}") from None
    except urllib.error.URLError:
        raise RuntimeError(f"{shot['id']}: API connection failed") from None
    target.write_bytes(content)
    print(json.dumps({'shot': shot['id'], 'bytes': len(content),
                      'elapsed_seconds': round(time.monotonic() - start, 1),
                      **validate_gif(content, spec['request'])}), flush=True)


def self_test():
    spec = specification()
    settings = dict(spec['request'], size='16x16', frame_count=3)
    frames = [Image.new('RGB', (16, 16), color) for color in ['red', 'green', 'blue']]
    buffer = io.BytesIO()
    frames[0].save(buffer, format='GIF', save_all=True, append_images=frames[1:],
                   duration=400, loop=0)
    content = buffer.getvalue()
    validate_gif(content, settings)
    decode_response({'data': [{'b64_json': base64.b64encode(content).decode()}]}, settings)
    invalid = [None, {}, {'data': []}, {'data': [{'b64_json': '!invalid!'}]},
               {'data': [{'b64_json': base64.b64encode(b'not a gif').decode()}]}]
    for case in invalid:
        try:
            decode_response(case, settings)
        except (ValueError, TypeError):
            continue
        raise AssertionError('Malformed API result was accepted')
    for modified in [dict(settings, frame_count=4), dict(settings, size='32x32'),
                     dict(settings, frame_duration_ms=300)]:
        try:
            validate_gif(content, modified)
        except ValueError:
            continue
        raise AssertionError('Invalid GIF properties were accepted')
    still = io.BytesIO()
    frames[0].save(still, format='GIF', duration=400)
    try:
        validate_gif(still.getvalue(), dict(settings, frame_count=1))
    except ValueError:
        pass
    else:
        raise AssertionError('Still image was accepted as animation')
    print('PASS: native GIF response, malformed responses, dimensions, timing and motion')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--shot', action='append', help='Generate only named shot(s)')
    parser.add_argument('--scripts-only', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    spec = specification()
    shots = [shot for story in spec['stories'] for shot in story['shots']]
    if args.shot:
        unknown = set(args.shot) - {shot['id'] for shot in shots}
        if unknown:
            parser.error('Unknown shot ID')
        shots = [shot for shot in shots if shot['id'] in args.shot]
    if args.check:
        for shot in shots:
            print(shot['id'], validate_gif((args.check / 'gifs' / f"{shot['id']}.gif").read_bytes(), spec['request']))
        return
    write_scripts(spec)
    if args.scripts_only:
        return
    key = read_key(args.key_file)
    (args.output / 'gifs').mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request_shot, spec, shot, key, args.output) for shot in shots]
        failures = []
        for future in futures:
            try:
                future.result()
            except Exception as error:
                failures.append(str(error).replace(key, '[REDACTED]'))
        if failures:
            raise RuntimeError('; '.join(failures))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
