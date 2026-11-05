# Working in med-assets

Before edits, read [Architecture and workflow](docs/WORKFLOW.md), then the owning
asset's README/review. Code and manifests define current behavior; report and fix
conflicting prose rather than introducing another policy owner.

- Find individual 3D assets in `models/<id>/`, compositions in `assemblies/`,
  imported products in `body/` and `heart/`, and 2D/runnable teaching products in
  `diagrams/` and `lessons/`. Keep asset recipes beside the asset.
- Keep shared inputs/licenses in `sources/`, common code in `tools/`, regression
  suites in `tests/`, and current evidence/decisions in `reviews/<id>/`.
- Preserve original import records, canonical source/export identities, coordinates,
  licenses, public URLs and active unmerged work. Recheck open PRs before broad edits.
- Use fresh output directories under ignored `.artifacts/<outcome>/`; retire spent
  output after moving meaningful findings to their owner. Follow the guide's
  admission and retention gates before expanding or deleting asset families.
- Stage intentional retirements before index-based verification. Required local
  gate: `python3.12 tools/verify.py offline` (Python 3.11+, Node 18+, Git).
  Broad changes with hydrated LFS also run `payload-integrity`; UFF changes run
  the separate `dental` suite. Test affected recipes and failure paths.
- Keep technical, visual, anatomical/clinical, runtime and publication status
  separate. No merge, upload, publication or execution-guard bypass is implied
  by local checks. Preserve the guarded workflows and transport controls.
- Deliver coherent commits and a draft PR with exact checked revision and limits.
  Preserve unrelated changes; merge only with applicable authorization.
