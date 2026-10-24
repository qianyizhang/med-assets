# HRA paired breast atlas study · source-candidate-02

Exact media transfer and independent GitHub LFS SHA/size/header readback passed on 2026-10-24 at 10:11:33 UTC. This confirms byte transport, not anatomy or runtime quality.

- Authored/sculpted atlas, not patient scan; simplified lobes and ducts, not complete microanatomy.
- Open/nonmanifold source components remain; no watertightness or clinical validation.
- Material-only illustrative palette; source geometry and transforms retained. Layer views do not validate physiology.

## Included records

- [Dated scoped review](bounded-record.json)
- [Source and external dependency map](../../../sources/datasets/breasts_hra-bounded/external-source-map.json)
- [Attribution](../../../models/breasts_hra/exports/source-candidate-02/ATTRIBUTION.md)

Exact canonical GLB plus 3 selected current WebPs, unchanged. Original PNG identity remains separate from actual WebP identity. Historical records and recipes are explicitly external; no portable rebuild or new gate claim.

Run `python tests/breasts_hra/verify_bounded.py`; default checks the manifest subset, while `--strict-package` checks standalone closure. Neither mode fetches sources, renders or validates runtime.
