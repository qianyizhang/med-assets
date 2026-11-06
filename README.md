# Medical teaching assets

Editable models, exports, 2D artwork and teaching experiences with source-specific
licenses, reproducible recipes and scoped review evidence. These are educational
assets; a technical check does not establish anatomical or clinical approval.

## Find and change an asset

| Content | Owner |
|---|---|
| Individual 3D assets and their recipes | [models](models/) |
| Compositions with explicit registration | [assemblies](assemblies/) |
| Imported whole-body atlases and cardiac/imaging products | [body](body/), [heart](heart/) |
| 2D diagrams and runnable lessons | [diagrams](diagrams/), [lessons](lessons/) |
| Dated survey reports and Site authoring | [sites/model-survey](sites/model-survey/) |
| Current decisions and exact supporting evidence | [reviews](reviews/) |
| External source inputs, notices and recovery material | [sources](sources/) |
| Shared utilities and regression checks | [tools](tools/), [tests](tests/) |
| External viewer integration and guarded delivery | [gallery](gallery/), [ci](ci/), [transport](transport/) |

Open the asset's export README and linked review for its source, recipe, status
and limits. Asset-specific build/render/check code belongs in its `recipes/`.
The [model survey](sites/model-survey/) is a dated derived report, not an asset
registry. Start contributing with [AGENTS.md](AGENTS.md)
and the single [architecture/workflow guide](docs/WORKFLOW.md).

## Quick start

```sh
git lfs install
git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
git lfs pull
python3.12 tools/verify.py payload-integrity
```

Python 3.11+, Git and Node.js 18+ are required. With pointers only, run
`python3.12 tools/verify.py offline`; it checks metadata and behavior, not media
bytes. [Verification](docs/WORKFLOW.md#verification) describes dental/replay
prerequisites and the independent quality/runtime gates.

For an offline incremental plan against a current mirror manifest, or a byte
comparison against downloaded files, see [backup checking](docs/BACKUP_CHECK.md).
This scopes work to one exact committed tree, including LFS payloads; it performs
no transfer, manifest write, replacement or deletion.
The linked guide also describes a serialized connector adapter and the explicit
exclusive-writer guarantee, journal and verification steps it requires.

## Provenance and published consumers

The 2026-10-22 import preserves 17 source bundles and 591 extracted-file identities
in [SHA256SUMS](SHA256SUMS) and [metadata](metadata/). These are historical records,
not today's file list. Explicit current exceptions live in
[current-import-overrides.json](metadata/current-import-overrides.json).
Original source ZIPs are not duplicated beside extracted content.

Preserve package licenses and attribution. Servier artwork and TotalSegmentator
surface adaptations carry their own CC BY 4.0 credits; label-source Apache notices
do not replace surface attribution. Authored cardiac/synthetic-imaging packages
declare no separate public license. Synthetic volumes are not patient scans.

Published [Body & Heart](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/),
[3D studio](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/)
and [Anatomy Verification](https://anatomy-verification.landy123007.chatgpt.site/)
have independent deployed sources. Local integration recipes are not deployments.
See [decisions and outstanding work](docs/DECISIONS.md) for cross-cutting boundaries.
