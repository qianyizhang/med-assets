# Shared voice and score

`final-mix.wav` is the canonical 48-second stereo 48 kHz PCM input for all three films (SHA-256 in `../results/manifest.json`). `narration-manifest.json` contains exact spoken text and voice cue times; `narration.srt` is scene-level, not word-aligned.

Voice: locally synthesized Kokoro-82M v1.0 `af_heart`, speed 0.94, via HyperFrames 0.9.8 and kokoro-onnx 0.6.1 / soundfile 0.14.0. It is not a cloned person or clinician recording. Each passage starts 0.3 seconds after its scene begins. No passage needed time stretching in the retained master. The underscore is original procedural composition, with no third-party samples.

The mix targets -18 LUFS and -2 dBTP. Timing and encoding were checked programmatically. Direct listening review remains outstanding. Code and model sources: https://github.com/hexgrad/kokoro and https://huggingface.co/hexgrad/Kokoro-82M . Preserve upstream notices if separately downloading model/runtime files.

## Optional regeneration

This is production context, not a promise of bit-identical voice regeneration. Render replay needs only the frozen master. Work in a new temporary directory so these scripts never overwrite canonical audio or timing evidence:

```sh
mkdir /tmp/dental-audio-new
cp experiments/dental-video-treatments/audio/*.py experiments/dental-video-treatments/audio/cue-manifest.json /tmp/dental-audio-new/
cd /tmp/dental-audio-new
python3 compose_score.py
ffmpeg -hide_banner -loglevel error -y -i score-raw.wav -af 'loudnorm=I=-24:TP=-6:LRA=7' -ar 48000 -c:a pcm_s16le -t 48 score.wav
HYPERFRAMES_BIN=/absolute/path/to/prepared/hyperframes/node_modules/.bin/hyperframes python3 generate_voice.py
python3 mix_audio.py
```

Python 3.12 / NumPy 2.3.5, FFmpeg/ffprobe with loudnorm, atempo and libmp3lame, and the separately installed local Kokoro runtime/model are required. Model/runtime downloads were about 510 MB in the original run and are deliberately not bundled. `HYPERFRAMES_NO_TELEMETRY=1` and `DO_NOT_TRACK=1` are set by the generation script.

`score-raw.wav`, `score.wav`, `voice-*`, `narration.wav`, `mix-raw.wav`, `final-mix.mp3` and other stems are generated-only outputs, not omitted delivery dependencies. New generated text/timing metadata must be reviewed separately before replacing an established comparison.
