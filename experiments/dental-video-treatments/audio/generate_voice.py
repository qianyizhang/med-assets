"""Regenerate the six voice segments with a locally installed HyperFrames CLI.
The frozen final-mix.wav is included; this optional step downloads a TTS model.
Install the HyperFrames project dependencies first. Override HYPERFRAMES_BIN if needed.
"""
import os
import subprocess
import json
from pathlib import Path

p = Path(__file__).resolve().parent
project = p.parent
binary = os.environ.get('HYPERFRAMES_BIN', str(project / 'node_modules/.bin/hyperframes'))
env = dict(os.environ, HYPERFRAMES_NO_TELEMETRY='1', DO_NOT_TRACK='1',
           HYPERFRAMES_CACHE_DIR=str(project / '.tts-cache'))
local_runtime = project / '.tts-runtime'
if local_runtime.exists():
    env['PYTHONPATH'] = str(local_runtime)
manifest = json.loads((p / 'cue-manifest.json').read_text())
for i, cue in enumerate(manifest['cues']):
    cmd = [binary, 'tts', cue['narration_text'], '--voice', 'af_heart',
           '--speed', '0.94', '--output', str(p / f'voice-{i+1}.wav'), '--json']
    res = subprocess.run(cmd, env=env, text=True, capture_output=True)
    print(i+1, res.returncode, res.stdout, flush=True)
    if res.returncode:
        print(res.stderr)
        raise SystemExit(res.returncode)
