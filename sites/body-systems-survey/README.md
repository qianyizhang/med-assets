# Body systems in 3D

Seven new teaching setups and four refinements cover eleven adult body
systems. The studies let learners trace a route, isolate an anatomical
junction or compare two poses. [The study brief](study-brief.md) records the
baseline gaps, acceptance criteria and package links. Each package owns its
build and check commands, source attribution, and scope of review.

## Outcome

The original teaching revision was
[`c803735865f4f14d6baf939c13b10f112445fe48`](revision.txt).
It produced twelve editable Blender scenes, twelve GLBs, 56 matched
clean-import view pairs and seven One Breath browser captures. The survey
also retained the baseline plates from 55 render jobs. Two concept plates
record visual direction for skin and lymphatic return.

- **Technical.** Blender 5.2.3 opened all twelve editable scenes with
  auto-execution disabled. Each package records its check and replay results.
  Nine GLBs replayed byte-for-byte. Endocrine, lymphatic and nervous studies
  reproduced their decoded geometry with different GLB serialization.
- **Visual and runtime.** The combined survey passed local Chrome checks for
  image decoding, system links, keyboard disclosure and 390 px reflow. Only
  [One Breath](../../reviews/one-breath/airway-r01/README.md) was exercised in
  live local WebGL. Its 3D views and independent exchange schematic have
  separate checks. Other studies have offline import and render evidence.
- **Anatomy.** Reference screening supports the stated introductory uses.
  Specialist approval remains open. Individual records identify schematic
  structures, authored joins, pose limits and exceptions.
- **Delivery.** The repository carries the recipes, input identities, lesson
  code, report source, review findings and exact media hashes. The existing
  galleries have separate deployment sources. Their comparison is retained
  for the pending gallery decision.

## Gallery presentation audit

**System assembly** shows structures together in the documented anatomical
frame. **Asset detail** shows named parts, junctions, isolated routes and
poses. An anatomical frame defines origin, axes, laterality and units. A
pose is the configuration of articulated parts. A view is the camera direction.

| Status | Systems and remaining work |
| --- | --- |
| Native or shared frame | Skeletal and muscular use their native atlases. Respiratory uses the shared thoracic scene, with the upper airway and enlarged terminal airspaces available separately. Urinary uses the Workshop tract, with filtration in detail. The reproductive views keep the two regional source frames and retain the authored male structures. |
| Partial assembly | Cardiovascular shows the native heart and proximal vessels. Its complete teaching loop is exploded. Digestive shows an upper abdomen and a separate BP3D bowel pair. Their complete route is schematic. A common-frame full assembly needs placement evidence for the remaining joins in both systems. |
| Illustrative placement | Nervous stages the brain, cord and right sciatic pathway. Endocrine combines independently sourced gland positions with an editorial outline. Lymphatic stages the regional route with an enlarged node and editorial organ locators. A metric body overlay needs evidence for those source registrations and the intended node scale. |
| Body locator | The integumentary envelope and the skin and nail sections use separate scales. The sections have no documented position in the envelope model. |

The skeletal overview uses the BodyParts3D envelope in its native frame. The
respiratory overview uses translucent lobes to reveal the lobar tree. Posterior
views expose thoracic and male pelvic landmarks. The detail pairs retain the
reviewed pose and source-frame bounds to within one micrometre. Palette changes
are display-only. Names in the legends identify the colors and anatomical groups.

Gallery replay is offline image evidence. Specialist, pose and runtime coverage
follow the owning reviews. The completed lesson and study assets continue to
have their own acceptance scope, distinct from the coverage of these assembly views.

## Restore the media

The archive `med-assets-teaching-c803735.zip` contains 327 files at their
repository-relative paths. It preserves the 143 teaching files by their
original Git LFS identities, the survey's baseline media and capture
receipts, and the separate dental experiment's six generated MP4s with their
subtitles and results README. The dental build lives at local revision
`06bfb80` on `codex/dental-image26-experiment`.

The **127,459,034-byte** archive has SHA-256
`ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014`.

The [public R2 backup](https://r2-object-library.landy123007.chatgpt.site/download?key=library%2Fmed-assets%2Fteaching%2Fafa6ed28-1fa4-40d5-af01-643460a53471--med-assets-teaching-c803735.zip)
is one Object Library object. A fresh public download on 19 November 2026
matched the archive size and SHA-256. All 327 extracted files matched the
[member manifest](backup-sha256.txt). Keep the local ZIP as an independent copy.

Run from the repository root. Download only if the local archive is missing.
The checksum gates extraction, and `unzip -n` preserves existing files.
The final check identifies local files that differ from the archived set.

```sh
(
set -e
zip=.artifacts/teaching-backup/med-assets-teaching-c803735.zip
key=library/med-assets/teaching/afa6ed28-1fa4-40d5-af01-643460a53471--med-assets-teaching-c803735.zip
archive=$zip
if [ ! -e "$zip" ]; then
  archive=$zip.partial
  mkdir -p .artifacts/teaching-backup
  curl --fail --silent --show-error --get \
    'https://r2-object-library.landy123007.chatgpt.site/download' \
    --data-urlencode "key=$key" --output "$archive"
fi
printf '%s  %s\n' ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014 "$archive" |
  shasum -a 256 -c
if [ "$archive" != "$zip" ]; then
  mv "$archive" "$zip"
fi
unzip -n "$zip"
shasum -a 256 -c sites/body-systems-survey/backup-sha256.txt
)
```

The local integration passed the 434-test offline suite and payload integrity
for all 689 indexed LFS files. A fresh extraction matched all 327 archived
file hashes. The restored survey passed the Chrome checks, and One Breath
passed its 37 Node tests and five-lobe phase sweep.

## Open or rebuild the survey

After restoring the archive, render the gallery from the repository root.
Use Blender 5.2.3 and a fresh presentation directory. On macOS get
command-specific approval for headless Blender before the first run.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P sites/body-systems-survey/render_gallery.py --
```

The default gallery render destination is `.artifacts/body-systems-survey-2026-11-19/presentation-r01/`.
For a repeat render use `--output` with a new directory, inspect the resulting
receipts, then replace the presentation directory before rebuilding the current
report. `MED_ASSETS_REPO` can point to the original hydrated checkout when the
gallery source is being developed in a separate worktree.

Build both reports from the repository root:

```sh
python3.12 sites/body-systems-survey/baseline_report.py
python3.12 sites/body-systems-survey/report.py
```

Open `.artifacts/body-systems-survey-2026-11-19/index.html` locally. The report
links to the original gap survey and to each model and review. The current
report checks each selected GLB and paired screenshot against its exact
render receipt. The gallery checks inherited camera directions, pose frames
and bounds against the owning reviews. The survey viewer needs no server. Follow the
[One Breath setup](../../lessons/one-breath/README.md#open-locally) to run
that interactive lesson.

The original baseline used `2cb53c05577b4cbc2355c4bff293666127d21382`.
`catalog.py` prints the discovery catalogue for the current checkout.
`jobs.json` freezes the selected baseline inputs for the Blender render
recipe. Hydrate those inputs and use a fresh output directory to replay a
baseline plate. For example:

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P sites/body-systems-survey/render.py -- \
  --only skeleton --output .artifacts/body-systems-baseline-replay
```

The retained browser exercise uses Chrome and a disposable profile. Run it as
`node sites/body-systems-survey/verify-browser.mjs --local-only` after building
the reports.
