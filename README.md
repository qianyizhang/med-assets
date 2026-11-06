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
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
python3.12 tools/verify.py offline
python3.12 tools/fetch_asset.py models/kidney_left/exports/metadata-cleanup-r01/kidney_left.glb --hydrate
```

Python 3.11+, Git and Node.js 18+ are required. The pointer-only checkout stays
small; on-demand R2 hydration verifies Git-pinned bytes and preserves source paths.
See [public downloads and delivery](transport/README.md) for curl, cache and upload
workflows. For full LFS recovery, run `git lfs pull` followed by
`python3.12 tools/verify.py payload-integrity`.

The offline gate checks metadata/behavior and may inspect selected local media;
it does not exhaustively verify payload bytes or remote availability.
[Verification](docs/WORKFLOW.md#verification) owns the independent checks and gates.
[Backup checking](docs/BACKUP_CHECK.md) provides read-only full-tree planning and
comparison; verified R2 payload copies are not a complete Git-tree backup.

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
