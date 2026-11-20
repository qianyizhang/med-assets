# Medical teaching assets

- **Contents** · Editable 3D models, registered assemblies, 2D diagrams and runnable lessons.
- **Use** · Education. See each package's source, license, review scope and limitations.
- **Find** · [Asset and evidence owners](docs/WORKFLOW.md#ownership), [source studies](sources/), [model survey](sites/model-survey/), [body-systems survey](sites/body-systems-survey/).
- **Experiment** · [Dental films and offline replay](experiments/dental-image26/).
- **Contribute** · [Repository instructions](AGENTS.md), [glossary](GLOSSARY.md), [gallery design](guideline/design.md), [teaching-asset rubric](guideline/asset-quality.md), [asset admission](docs/WORKFLOW.md#asset-admission), [verification](docs/WORKFLOW.md#verification), [decisions](docs/DECISIONS.md).

## Local checkout

```sh
git lfs install
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/qianyizhang/med-assets.git
cd med-assets
python3.12 tools/verify.py offline
```

- **Payloads** · [Public downloads and Git/LFS recovery](transport/README.md).
- **Backup coverage** · [Exact-tree planning and local byte checks](docs/BACKUP_CHECK.md).
- **Original import** · [Source identities and current exceptions](docs/WORKFLOW.md#import-and-source-integrity).

## Published consumers

| Site | Entry |
| --- | --- |
| Model survey | [Survey](https://med-assets-model-survey.landy123007.chatgpt.site/) · [Build and recovery](sites/model-survey/) |
| Body & Heart | [Atlas](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/) · [3D studio](https://heart-anatomy-imaging-lab.landy123007.chatgpt.site/body/3d/) |
| Anatomy Verification | [Site](https://anatomy-verification.landy123007.chatgpt.site/) · [Viewer integration](gallery/) |
