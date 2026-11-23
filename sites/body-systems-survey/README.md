# Body systems in 3D

Seven new teaching setups and four refinements cover eleven adult body
systems. The studies let learners trace a route, isolate an anatomical
junction or compare two poses. [The study brief](study-brief.md) records the
baseline gaps, acceptance criteria and package links. Each package owns its
build and check commands, source attribution, and scope of review.

## Body Systems on the unified Site

The ordinary Site reads the [Body Systems collection export](../../lessons/body-systems/README.md). Rebuild this report and use its export command when the collection adopts a new reviewed plate. This directory owns the dated report, its local 3D replay and archive recovery.

## Outcome

The original teaching revision was
[`c803735865f4f14d6baf939c13b10f112445fe48`](revision.txt).
It produced twelve editable Blender scenes, twelve GLBs, 56 matched
clean-import view pairs and seven One Breath browser captures. The survey
also retained the baseline plates from 55 render jobs. Two concept plates
record visual direction for skin and lymphatic return. The [study brief
records their prompts](study-brief.md#imagegen-concept-prompts).

- **Technical.** Blender 5.2.3 opened all twelve editable scenes with
  auto-execution disabled. Each package records its check and replay results.
  Nine GLBs replayed byte-for-byte. Endocrine, lymphatic and nervous studies
  reproduced their decoded geometry with different GLB serialization.
- **Visual and runtime.** The combined survey passed local Chrome checks for
  image decoding, system links, keyboard disclosure and 390 px reflow. In that original revision, only
  [One Breath](../../reviews/one-breath/airway-r01/README.md) was exercised in
  live local WebGL. Its 3D views and independent exchange schematic have
  separate checks. The [adrenal exterior review](../../reviews/endocrine-locator/adrenal-study-r04/README.md) records the later full-gallery WebGL check.
- **Anatomy.** Reference screening supports the stated introductory uses.
  Specialist approval remains open. Individual records identify schematic
  structures, authored joins, pose limits and exceptions.
- **Delivery.** The repository carries the recipes, input identities, lesson
  code, report source, review findings and exact media hashes. The existing
  galleries have separate deployment sources. The [gallery design guide](../../docs/gallery/design.md) proposes how their catalogue and review routes connect to these teaching views.

## Gallery presentation audit

See the [med-assets glossary](../../GLOSSARY.md) for **System assembly**,
**Asset detail**, and the placement and camera terms used in the audit.
The [19 November refinement proposal](next-round-spec.md) records the checked
baseline and the original proposals for all eleven systems. The dated reviews
below record the results.

| Status | Systems and remaining work |
| --- | --- |
| Native or shared frame | Skeletal and muscular use their native atlases. Respiratory uses the shared thoracic scene, with the upper airway and enlarged terminal airspaces available separately. Urinary uses the Workshop tract, with filtration in detail. The reproductive views keep the two regional source frames and retain the authored male structures. |
| Partial assembly | With the optional s1233 bundle, cardiovascular shows the heart and great vessels and digestive shows the esophagus through colon and accessory organs in the same scan frame. The fallback shows the Workshop heart and proximal vessels, and the Workshop upper abdomen and BP3D bowel in separate frames. Full-route teaching remains in the exploded cardiovascular loop and schematic digestive tract. [Same-case audit](../../assemblies/workshop-s1233/README.md) · [Cardiovascular review](../../reviews/cardiovascular-loop/README.md) · [Digestive review](../../reviews/digestive-route/r01/README.md). |
| Illustrative placement | Nervous stages the brain, cord and right sciatic pathway. Endocrine combines independently sourced gland positions with an editorial outline. Lymphatic stages the regional route with an enlarged node and editorial organ locators. A metric body overlay needs evidence for those source registrations and the intended node scale. |
| Body locator | The integumentary envelope and the skin and nail sections use separate scales. The sections have no documented position in the envelope model. |

The skeletal overview uses the BodyParts3D envelope in its native frame. The
respiratory overview uses translucent lobes to reveal the lobar tree. Posterior
views expose thoracic and male pelvic landmarks. The detail pairs retain the
reviewed pose and source-frame bounds to within one micrometre. Palette changes
are display-only. Names in the legends identify the colors and anatomical groups.

Gallery replay supplies offline image evidence. A local Chrome run at
`ba0bf3d6be59adfa7065cb5cefea8f442476121b` also passed all 24 static 3D
launches, including missing-model fallback and retry. Specialist review,
pose, and lesson runtime evidence follow the owning reviews.

The optional [same-case Workshop update](../../assemblies/workshop-s1233/README.md)
includes digestive and cardiovascular overviews in the s1233 scan frame.
Those two sections retain their partial status and show the measured limits
when the local assembly receipts and renders are present.

## Local before-and-after comparisons

The [first surface review](../../reviews/body-systems/2026-11-20-surface-quality/README.md)
scores the terminal airspaces, seated nail and s1233 adrenal group. The
[adrenal close-up review](../../reviews/endocrine-locator/adrenal-study-r04/README.md)
applies the [refined rubric](../../docs/guides/asset-quality.md) to the interpreted
teaching exterior. The [next adrenal study](../../reviews/endocrine-locator/adrenal-study-r05/README.md)
compares it to a surface rebuilt against the original s1233 gland labels. The
[blind comparison](../../reviews/endocrine-locator/adrenal-study-r05/compare.html)
lets you inspect five matched views before revealing their scores. The
[Anatomy Gallery](../anatomy-gallery/README.md) links the s1233 study to the
separate BodyParts3D verification record and expanded family.
The surface comparisons use checked-in GLBs. The earlier
atlas-to-scan comparison uses the locally restored regional models.

Open **Before and after** within a system. Each panel links the
original and updated isometric and orthographic renders to their model
identities and the owning review. The report checks camera, scale and PNG
dimensions for matched pairs. Where available, **Open updated view in 3D**
opens a static preview with named part controls. New exports show their own
materials. Regional views use the comparison palette. The digestive cutaway
shows the pyloric opening, and its close-up shows the ducts and papilla.
The skin envelope markers open the enlarged skin and nail sections.

The teaching archive below restores the original survey. New comparison
media is local under `.artifacts/body-systems-refinement-2026-11-19/` and uses
the owning recipes. Build regional before-and-after views from the original
pinned GLBs and their restored gallery render receipts:

```sh
round=.artifacts/body-systems-refinement-2026-11-19
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P sites/body-systems-survey/render_gallery.py -- --compare-regions \
  --output "$round/regional-renders"
python3.12 sites/body-systems-survey/report.py
```

Use a fresh output directory for repeat renders. Move a checked replay into
the expected local path to include it in the report. See the
[gastroduodenal section recipe](../../assemblies/digestive-route/r02/README.md)
for the revised cutaway. Its gallery path is `$round/digestive-r03`, with
the render receipt under `renders/`. Regional views reuse the original model
bytes. The isolated color treatments and nail lift are display changes.
For the [Cardiac Atlas cutaway](../../assemblies/cardiovascular-loop/valve-study-r01/README.md),
use `$round/cardiovascular` as the study directory. It supplies the
matched right and left valve views and the mitral leaflet lift.

For the smoother same-case overviews, prepare and export the
[s1233 derivative](../../assemblies/workshop-s1233/README.md) into
`$round/same-case/assemblies`, then run:

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  -P sites/body-systems-survey/render_gallery.py -- \
  --compare-workshop "$round/same-case/assemblies" \
  --output "$round/same-case-renders"
python3.12 sites/body-systems-survey/report.py
```

This uses the original same-case bundle for the original views. The updated
plates preserve the scan frame. The report reads the source colon separation
from the checked mask audit.

Three focused studies add standalone teaching groups:

| Study | Local path under `$round` |
| --- | --- |
| [Right root and ramus](../../assemblies/nervous-senses/root-study-r01/README.md) | `nervous-root/` |
| [Endocrine neck and abdomen](../../assemblies/endocrine-locator/r02/README.md) | `endocrine/` |
| [Lymph-node section](../../assemblies/lymphatic-return/r02/README.md) | `lymphatic/checked-build/` and `lymphatic/checked-renders/` |

An interrupted or invalid optional same-case restore shows the fallback
assemblies and reports the failing file in the build log. Restore or rebuild
both the assembly and its render receipts before reopening the report.

## Restore the media

The archive `med-assets-teaching-c803735.zip` contains 327 files at their
repository-relative paths. It preserves the 143 teaching files by their
original Git LFS identities, the survey's baseline media and capture
receipts, and the separate dental experiment's six generated MP4s with their
subtitles and results README. The [dental experiment](../../experiments/dental-image26/README.md)
records the original revision and how to replay the build from frozen inputs.

The **127,459,034-byte** archive has SHA-256
`ccdf0a5dafadf0a4d251a19b83f14ec157e29abdcfe4b3c1199498700d37b014`.

The [public R2 backup](https://r2-object-library.landy123007.chatgpt.site/download?key=library%2Fmed-assets%2Fteaching%2Fafa6ed28-1fa4-40d5-af01-643460a53471--med-assets-teaching-c803735.zip)
is one Object Library object. A fresh public download on 19 November 2026
matched the archive size and SHA-256. All 327 extracted files matched the
[member manifest](backup-sha256.txt). Keep the local ZIP as an independent copy.

From the repository root, restore to the original paths with the verified collection command. Omit `--from-zip` to download the pinned ZIP, or pass `--output DIRECTORY` to rehearse in an empty tree. Existing conflicting files stop restoration before any missing members are installed.

```sh
python3.12 transport/tools/restore_collection.py teaching-media \
  --from-zip .artifacts/teaching-backup/med-assets-teaching-c803735.zip
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
and bounds against the owning reviews. Open the image gallery from disk. For
interactive 3D, start the [local viewer server](#open-in-3d). Follow the [One
Breath setup](../../lessons/one-breath/README.md#open-locally) to run that lesson.

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

## Open in 3D

Start the local server after restoring the gallery media and hydrating its
selected GLBs. It rebuilds the original gallery and serves it at
[127.0.0.1:8847](http://127.0.0.1:8847/).

```sh
python3.12 sites/body-systems-survey/serve.py
```

If that port is occupied, pass `--port 8848`. The server rebuilds the report
with launch links for its listening port.

Use **Open in 3D** on a System assembly, or open an individual delivered model
under **Models, review and attribution**. The viewer supports orbit, zoom,
named structure visibility and, with the same-case digestive assembly restored,
a fixed-camera stomach comparison. The server checks asset hashes and serves
the identified GLBs and linked gallery files on loopback. It stops after
four hours or Ctrl-C. **Open in 3D** links from the disk report use the same
local server.

The server reuses pinned Three.js modules if they are already cached or
staged for the repository's runtime fixtures. If the modules are missing,
start it once with `--fetch-vendor` to fetch and verify those exact modules.
In an isolated development worktree, point `MED_ASSETS_REPO` at the hydrated
checkout that holds the gallery artifacts and assets.

Verify in disposable Chrome with the running local server. Use `--with-s1233`
when the same-case gallery additions are installed.

```sh
node sites/body-systems-survey/verify-browser.mjs --local-only \
  --with-s1233 --viewer=http://127.0.0.1:8847
```

For the screenshot-only report, run the same harness without `--viewer`.
