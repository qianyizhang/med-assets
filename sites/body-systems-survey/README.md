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

## Restore the media

The archive `med-assets-teaching-c803735.zip` contains 327 files at their
repository-relative paths. It preserves the 143 teaching files by their
original Git LFS identities, the survey's baseline media and capture
receipts, and the separate dental experiment's six generated MP4s with their
subtitles and results README. The dental build lives at local revision
`06bfb80` on `codex/dental-image26-experiment`.

Archive identity: **127,459,034 bytes**, SHA-256
`ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014`.

Local archive: `.artifacts/teaching-backup/med-assets-teaching-c803735.zip`.
R2 destination: [Object Library](https://r2-object-library.landy123007.chatgpt.site/)
under `med-assets/teaching`. The upload is pending the library’s upload password.

From the repository root, verify the archive before extraction. The unzip
command preserves existing files. The final check identifies any local
files that differ from the archived set.

```sh
zip=.artifacts/teaching-backup/med-assets-teaching-c803735.zip
printf '%s  %s\n' ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014 "$zip" | shasum -a 256 -c
unzip -n "$zip"
shasum -a 256 -c sites/body-systems-survey/backup-sha256.txt
```

The local integration passed the 434-test offline suite and payload integrity
for all 689 indexed LFS files. A fresh extraction matched all 327 archived
file hashes. The restored survey passed the Chrome checks, and One Breath
passed its 37 Node tests and five-lobe phase sweep.

## Open or rebuild the survey

After restoring the archive, build both reports from the repository root:

```sh
python3.12 sites/body-systems-survey/baseline_report.py
python3.12 sites/body-systems-survey/report.py
```

Open `.artifacts/body-systems-survey-2026-11-19/index.html` locally. The report
links to the original gap survey and to each model and review. The current
report checks each teaching GLB and each matched screenshot against the owning
render receipt. The survey viewer needs no server. Follow the
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
