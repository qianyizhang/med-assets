# Medical teaching assets

This repository is in beta. We ship in small, verified iterations and retire superseded assets and manifest entries as their readers migrate. See the [beta retention policy](docs/WORKFLOW.md#retention).

- **Contents** · Editable 3D models, registered assemblies, 2D diagrams and runnable lessons.
- **Use** · Education. See each package's source, license, review scope and limitations.
- **Find** · [AssetKit for reusable 3D assets](src/assetkit/README.md), [asset and evidence owners](docs/WORKFLOW.md#ownership), [source studies](sources/).
- **Experiment** · [Dental films and offline replay](experiments/dental-image26/).
- **Contribute** · [Repository instructions](AGENTS.md), [glossary](GLOSSARY.md), [teaching-asset rubric](docs/guides/asset-quality.md), [asset admission](docs/WORKFLOW.md#asset-admission), [verification](docs/WORKFLOW.md#verification), [decisions](docs/DECISIONS.md).
- **Maintain an asset** · [Rebuild, promote, release or retire a file](docs/WORKFLOW.md#maintaining-an-asset).
- **Follow work** · [Work-item backlog](records/work-items/backlog.md) and [asset toolkit campaign results](records/campaigns/asset-toolkit.md).

The [maintained 3D family list](docs/gallery/maintained-models.md) identifies each maintained family and its selected teaching files. The [collection archives](transport/README.md#restore-an-archived-collection) restore cold replay inputs and historical evidence.

## Anatomy Gallery

Open the [live Gallery](https://med-assets-model-survey.landy123007.chatgpt.site/) to browse Asset Library or explore a teaching collection under Use Cases. Compare and 3D Stage are available under Tools. For the Gallery’s organization and authoring contracts, see the [product requirements](docs/gallery/README.md) and [design guide](docs/gallery/design.md). For local builds and replay, see the [Gallery source](sites/anatomy-gallery/) and [Body Systems survey](sites/body-systems-survey/).

## Local checkout

Use Git LFS, `uv` (defaulting to Python 3.12 via `.python-version`) and Node.js 24 for the commands below. The first check runs on LFS pointers.

```sh
git lfs install
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
uv sync
uv run pre-commit install
uv run python tools/verify.py offline
uv run pytest src/assetkit/tests
```

- **Payloads** · [Public downloads and Git/LFS recovery](transport/README.md).
- **Blender** · [Choose live iteration or headless replay and set up Blender MCP](docs/WORKFLOW.md#blender-workflow).
- **Backup coverage** · [Exact-tree planning and local byte checks](docs/BACKUP_CHECK.md).
- **Original import** · [Source identities and current exceptions](docs/WORKFLOW.md#import-and-source-integrity).

## Published consumers

| Site | Entry |
| --- | --- |
| Anatomy Gallery | [Public Site](https://med-assets-model-survey.landy123007.chatgpt.site/) · [Build and recovery](sites/anatomy-gallery/) |
| Body & Heart | [Atlas](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/) · [3D studio](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/) |
| Anatomy Verification | [Site](https://anatomy-verification.landy123007.chatgpt.site/) · [Viewer integration](tests/viewer/README.md) |
