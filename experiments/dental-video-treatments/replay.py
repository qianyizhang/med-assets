#!/usr/bin/env python3
"""Prepare isolated renderer inputs and verify frozen delivery; no downloads/uploads."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
ENGINES = ('hyperframes', 'remotion', 'manimgl')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(root=ROOT):
    return json.loads((root / 'results/manifest.json').read_text())

def check_sources(root=ROOT):
    data = manifest(root)
    for name, expected in data['originalSourceHashes'].items():
        if name == 'hyperframes/index.html':
            continue  # Generated and verified separately, not duplicated in Git.
        if digest(root / name) != expected:
            raise ValueError('Source identity mismatch: ' + name)
    cues = json.loads((root / 'audio/narration-manifest.json').read_text())['cues']
    if [(c['start'], c['end']) for c in cues] != [(0,6),(6,14),(14,23),(23,31),(31,40),(40,48)]:
        raise ValueError('Unexpected shared narration timing')
    code = (root / 'remotion/src/index.tsx').read_text()
    m = re.search(r'const captions=(\[.*?\]);\nfunction Shot', code, re.S)
    if not m:
        raise ValueError('Missing Remotion captions')
    captions = ast.literal_eval(m.group(1))
    if len(captions) != len(cues) or any(' '.join(a) != b['narration_text'] for a,b in zip(captions,cues)):
        raise ValueError('Captions differ from shared narration')
    return data

def check_payloads(root=ROOT):
    data = check_sources(root)
    for row in data['artifacts']:
        path = root / row['file']
        if not path.is_file() or path.stat().st_size != row['bytes'] or digest(path) != row['sha256']:
            raise ValueError('Missing or altered payload (fetch scoped LFS): ' + row['file'])
    return data

def prepare(engine, output, root=ROOT):
    if engine not in ENGINES:
        raise ValueError('Unknown renderer')
    output = Path(output).resolve()
    if output.is_relative_to((root/engine).resolve()):
        raise ValueError('Output must not be inside canonical engine source')
    if output.exists():
        raise ValueError('Use a new output directory; existing output is never overwritten')
    # Validate the only required media input, not unrelated retained result movies.
    data = check_sources(root)
    master = next(r for r in data['artifacts'] if r['file'] == 'audio/final-mix.wav')
    if digest(root/master['file']) != master['sha256']:
        raise ValueError('Audio master missing or altered; fetch its LFS payload')
    for name in ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf'):
        row = next(r for r in data['artifacts'] if r['file'] == 'fonts/'+name)
        if digest(root/row['file']) != row['sha256']:
            raise ValueError('Font payload missing or altered')
    shutil.copytree(root/engine, output)
    audio = output/({'hyperframes':'assets','remotion':'public','manimgl':'audio'}[engine])
    audio.mkdir(exist_ok=True)
    shutil.copy2(root/'audio/final-mix.wav', audio/'final-mix.wav')
    for name in ('narration-manifest.json','narration.srt'):
        shutil.copy2(root/'audio'/name, audio/name)
    if engine == 'hyperframes':
        for name in ('DejaVuSans.ttf','DejaVuSans-Bold.ttf'):
            shutil.copy2(root/'fonts'/name, output/'assets'/name)
        subprocess.run(['python3', str(output/'build_story.py')], check=True)
        if digest(output/'index.html') != data['originalSourceHashes']['hyperframes/index.html']:
            raise ValueError('Generated HTML differs from the reviewed original')
    return output

def check_movies(root=ROOT):
    data = check_payloads(root)
    observations=[]
    for row in data['artifacts']:
        if not row['file'].endswith('.mp4'):
            continue
        path = root / row['file']
        info = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        v = next(s for s in info['streams'] if s['codec_type']=='video')
        a = next(s for s in info['streams'] if s['codec_type']=='audio')
        if [v['width'],v['height']] != row['resolution'] or v['r_frame_rate']!='30/1' or int(v['nb_frames'])!=1440:
            raise ValueError('Unexpected video stream: '+row['file'])
        if abs(float(info['format']['duration'])-48)>.05 or a['sample_rate']!='48000' or a['channels']!=2:
            raise ValueError('Unexpected duration/audio: '+row['file'])
        result = subprocess.run(['ffmpeg','-threads','2','-v','error','-i',str(path),'-f','null','-'],capture_output=True)
        if result.returncode or result.stderr:
            raise ValueError('Video decode failed: '+row['file'])
        observations.append({'file':row['file'],'decode':'passed','frames':1440,'durationSeconds':48})
    return observations

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('engine',choices=ENGINES);p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('check');p.add_argument('--payloads',action='store_true');p.add_argument('--movies',action='store_true')
    args=parser.parse_args()
    if args.command=='prepare': print(prepare(args.engine,args.output))
    elif args.movies: print(json.dumps(check_movies(),indent=2))
    else:
        check_payloads() if args.payloads else check_sources()
        print('PASS: '+('source and frozen payload identities' if args.payloads else 'source identities, timing and caption consistency'))
if __name__=='__main__': main()
