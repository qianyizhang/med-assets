# Dental condition → procedure: native Image 2.6 experiment

Five original illustrative stories, 16 retained native GIF shots and frozen
narration rebuild five short films and a combined explainer. This is a separate
generative-media experiment. It uses
no repository anatomical assets and adds nothing to the maintained asset catalogue.

Read [the complete movie scripts and prompts](SCRIPTS.md). The executable shot
list is [stories.json](stories.json); the script document is derived from it.

## Local brief

- **Accept:** Five detailed, variable-length stories; API-returned animated GIFs;
  captioned/narrated individual and combined MP4s; technical and sampled visual review.
- **Sources:** [NIDCR decay](https://www.nidcr.nih.gov/health-info/tooth-decay),
  [NIDCR gum disease](https://www.nidcr.nih.gov/health-info/gum-disease),
  [AAE root canal](https://www.aae.org/patients/root-canal-treatment/what-is-a-root-canal/),
  [FDA implants](https://www.fda.gov/medical-devices/dental-devices/dental-implants-what-you-should-know).
- **Delivery.** Local main retains the process, scripts and transcript. The
  original branch ended at `06bfb80`. The 16 native GIFs and frozen FLAC stay in
  the local input ZIP. The [teaching backup](../../sites/body-systems-survey/README.md#restore-the-media)
  holds the six rendered MP4s and subtitles under `results/`.
- **Checks:** Decode all frames and MP4s; check motion, timing and captions;
  inspect shot contact sheets; run local failure checks and repository offline gate.
  New generation invalidates pixel review. Clinical approval remains separate.

## Restore frozen inputs

From the repository root, use
`.artifacts/dental-image26/dental-image26-inputs-06bfb80.zip`.
This **36,488,692-byte** local archive restores 17 files to their original
repository-relative paths. The files carry the same byte identities as the
original branch's LFS inputs. [Input hashes](input-sha256.txt).

```sh
zip=.artifacts/dental-image26/dental-image26-inputs-06bfb80.zip
printf '%s  %s\n' ffca11fb6520963db292433187e4383fa8d27d777d0a35a18a5327bed6c48c3e "$zip" |
  shasum -a 256 -c &&
  unzip -n "$zip" &&
  shasum -a 256 -c experiments/dental-image26/input-sha256.txt
```

The shared DejaVu fonts are existing repository assets and are covered by
Git LFS. Hydrate them separately when needed:

```sh
git lfs pull --include="sources/fonts/dejavu/*" --exclude=""
```

## Replay

Rebuild needs Python 3.11+, Pillow, FFmpeg/ffprobe with H.264/AAC support, the
restored inputs, and the sibling experiment's retained DejaVu fonts and license at
`../../sources/fonts/dejavu/`. It does not need macOS speech services.
Optional new GIF generation needs network/API access and an authorized key.
The native GIF API is called directly because the installed imagegen CLI rejects
GIF output. No shared skill/helper files are changed.

```sh
# Run from this directory after restoring the input ZIP and fonts.
uv venv --python python3.12 .work/venv
uv pip install --python .work/venv/bin/python -r requirements.txt
.work/venv/bin/python generate.py --check .
.work/venv/bin/python -m unittest test_replay.py
.work/venv/bin/python render.py --output results
.work/venv/bin/python generate.py --self-test

# Optional paid generation into a NEW ignored experiment directory, not an
# overwrite of the retained inputs. Supply an explicitly authorized key file.
.work/venv/bin/python generate.py --key-file /path/to/authorized.env --output .work/new-generation
```

Generation defaults: `gpt-image-2.6-sunburst`, medium quality, high complexity,
512 × 512, 16 frames × 400 ms = 6.4 seconds per shot, one animation per request.
At most two requests run concurrently. Existing valid shots are reused; invalid
existing files stop the run. No automatic API retries. A failed response is never
saved as a GIF. Request options and prompts are retained in `stories.json`.
GIF looping is a container behavior; the films play each treatment once and hold
its final frame. Treatment is never reversed to make a seamless loop.
Each film build uses a fresh ignored `.artifacts/dental-image26-2026-11-06/edit-*`
directory for plates and encoded segments. `.work/venv` contains only
the disposable local Python environment.

## Narration and timing

The original voice was macOS `say`, Samantha, 148 words/minute, synthesized for
each scene and normalized by FFmpeg to -18 LUFS / -2 dBTP before mixing. There is
no music, sound effect, cloned voice or paid speech API. Original temporary AIFF
stems were retired after the first delivery.

`audio/narration.flac` freezes the decoded audio of that delivered master from
source revision `f52d080`. It is lossless storage of the already AAC-compressed
sound, with silence filling the original AAC timestamp gaps and the final tail
trimmed to the 5,035-frame edit; it does not recover the original pre-AAC stems.
The first plain extraction lost 0.217 seconds of timestamp gaps, which the
duration preflight rejected; timestamp-aware extraction fixed this before retention.
Retain the audio because speech
regeneration is platform-dependent. `audio/narration.srt` binds the 28 spoken
passages to the original edit: speech starts 300 ms after each scene starts, and
each cue ends 200 ms before the next cut. The renderer derives 30 fps scene
lengths from those cues and rejects a changed script, discontinuous cuts or an
audio-length mismatch. It preserves 5,035 video frames / 167.833 seconds and muxes
the frozen sound once; encoded file bytes may differ by FFmpeg version.

Titles and captions are drawn by Pillow; only the dental illustrations come from
the Image API. Each native GIF plays once, followed by a final-frame hold.

## Verification and findings

The first delivery at `f52d080` passed all 16 GIF decodes, all six full MP4 decodes,
28 subtitle cues and sampled visual checks. One floating implant healing cap was
rejected and repaired with one additional API call (17 calls total, 16 retained).
Historical review images and routine receipts are derived output, not retained
source evidence. These historical results do not claim fresh clinical approval.

Cleanup verification passed a fresh build from staged sources, 17 size/hash-checked
owned LFS inputs and the three shared font/license files (two fonts also in LFS).
All six rebuilt movies fully decoded; all 5,035 decoded master-video frames matched
the original delivery. The frozen FLAC fully decoded. Five replay tests passed,
including transcript/timing drift failures; native GIF response-failure checks
passed. The staged repository offline gate passed 432 tests and 706 LFS identities.
No API requests, dependency installation or speech synthesis were needed for this
rebuild. No hosted CI or remote LFS availability check is claimed.

During local consolidation, a fresh extraction passed all 17 input hashes.
The offline replay rebuilt and decoded all six films. The master had 5,035
frames, and its subtitle file matched the archived result byte-for-byte. The
five timing tests and native GIF response checks also passed.

## Boundaries and retention

These are simplified, AI-generated explanatory illustrations, not validated
anatomy or a procedural training guide. Assessment, anesthesia, isolation, imaging,
consent and many clinical substeps are omitted or summarized. The first story is
noncavitated decay; fluoride does not refill a hole. Root-canal filling does not
regenerate pulp. Deep cleaning does not instantly regrow lost bone. Implant
integration is shown as a time jump over months and is not guaranteed.
Independent shots share a style and root-count constraints, but exact tooth and
gum geometry varies between shots. Cuts separate these illustrative states;
they do not establish matched anatomical identity or measured healing.

Retain the scripts, native GIFs, frozen narration and timed transcript as one
experiment. Keep generated films locally for viewing, excluded from Git. Review
temporary working files by 2026-12-06; no automatic deletion.
No credentials, source meshes, model weights or installed dependencies belong here.

## Documentation mismatches

- The installed [imagegen skill](https://github.com/openai/skills/tree/main/skills/.curated/imagegen)
  and its local CLI cover older still-image behavior; the local CLI's
  `_normalize_output_format` rejects GIF. Current
  [official generation docs](https://developers.openai.com/api/docs/guides/image-generation#generate-animated-gif-output)
  support Image 2.6 and native GIF fields. Proposed shared-owner fix: update the
  skill and CLI for these models, formats and animation parameters. This experiment
  uses the user-requested direct API and does not change the shared owner.
- The guide limits `frame_duration_ms` to 20–2000 ms; the
  [API reference](https://developers.openai.com/api/reference/resources/images/methods/generate)
  describes an encoded ceiling of 655,350 ms. Proposed docs fix: distinguish request
  validation limits from container encoding limits. This experiment uses 400 ms,
  within both descriptions, and does not test the conflicting extremes.
