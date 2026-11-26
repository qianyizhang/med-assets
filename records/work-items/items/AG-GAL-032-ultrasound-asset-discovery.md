---
description: Make ultrasound tours and their reusable model revisions discoverable in the main Anatomy Gallery.
scope: Anatomy Gallery Use Cases and Asset Library
status: stable
last_update: 2026-11-25
document_class: work_record
work_id: AG-GAL-032
work_status: ready
work_kind: build
added: 2026-11-25
tags: gallery, ultrasound, evidence, transport
depends_on: none
---

# AG-GAL-032 — Bring ultrasound tours and assets into Gallery discovery

**Owner** · Anatomy Gallery, in coordination with the ultrasound campaign.

A visitor entering through the main Gallery should be able to find a body-region tour, open a named scan view and identify the exact reusable anatomy behind it. Today the Gallery points to the original fixed gallbladder lesson. The sweep builder assembles a separate catalog, and the Library already carries some upstream models. The refined breast used for probe contact, for example, needs an explicit relationship to its HRA source. [Gallery ultrasound entry](../../../sites/anatomy-gallery/app/src/content/gallery/ultrasound-data.js) · [Sweep catalog builder](../../../experiments/ultrasound-sweep/assemble_tours.py) · [Asset Library contract](../../../docs/gallery/asset-library.md)

## Scope and acceptance

1. Reconcile the assembled sweep catalog against Gallery discovery. Cover abdomen, thyroid, breast and axilla, and the pregnancy stages. Include the normal aortic screening survey from the assembled local study. Record a destination or a specific reason for holding each route or asset family. [Ultrasound campaign](../../campaigns/ultrasound-gallery.md)
2. From **Use Cases → Ultrasound Anatomy**, visitors can open each admitted tour at a named keyframe and return to its collection. Existing gallbladder bookmarks still resolve. Build the links from stable sweep and keyframe identities so a renamed title cannot break discovery.
3. From **Asset Library**, a visitor can find each admitted reusable model and identify which sweeps use its exact revision. Reuse an existing lineage for a refined export and give independently authored anatomy its own source record. Keep probe poses, simulated scans, overlays and acquired comparisons grouped by sweep and keyframe. Review this grouping with the owner before settling the asset display. [Tour and asset review scope](../../../docs/gallery/use-cases/ultrasound-anatomy.md)
4. Preserve the distinction between a modeled scan and an acquired reference. Carry source, credit, reuse terms and export identity into the Gallery. Give restricted or local-only material a visible disposition in the reconciliation. Gallery links must work from the assembled site independently of a developer’s localhost server or ignored build directories. [Acquired reference records](../../../experiments/ultrasound-sweep/research/README.md)
5. Verify the built Gallery from both entry points. Trace a refined breast export and a stage-specific pregnancy model to their keyframes, test the original gallbladder bookmark, and check all catalog links and downloadable identities. Record the tested revision, any held assets and the applicable Gallery and repository gate results. [Verification gates](../../../docs/WORKFLOW.md#verification)
