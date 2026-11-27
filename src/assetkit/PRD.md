# AssetKit Product Requirements & Migration Specification (PRD)

> **Document role:** `PRD.md` defines the target repository state after porting existing artifacts, the public Python/CLI APIs across AssetKit's 6 bounded contexts, and end-to-end authoring workflows (centered on Ultrasound Anatomy).  
> See [DESIGN.md](DESIGN.md) for the DDD submodule architecture, invariants, economy rules, and architectural trade-offs.

---

## 1. Target State After Porting Existing Artifacts

Porting the current repository (~86 discovered asset directories, 194 runtime exports totaling ~579 MB, 13 lessons, 32 ultrasound cases / 16 sweeps, 133 teaching assessments, and 81 selections) into AssetKit organizes the repository into **two primary declarative sets** (plus immutable reviews and curated selections):

| Layer | Estimated Scale After Porting | Owned On Disk | Submodule Owner |
| --- | --- | --- | --- |
| **Maintained Assets** | **~80–90 Assets** across ~65–70 package directories; **~160 Revisions**; **~220–260 Exports** (~500–600 addressable **Parts**) | `<package>/assets.json` (1 file per package directory, declaring `1..N` Assets) | `assetkit.registry` + `assetkit.build` |
| **Shared Concepts** | **~150–250 Concepts** + typed DAG edges (`part_of`, `is_a`, `located_in`, `produces`, `participates_in`, `drains_to`, etc.) | `sources/concepts.json` (1 compact shared file; terms added on demand) | `assetkit.vocab` |
| **Consumers** | **~70–80 Consumers**: 11 Body Systems stops, 12 other lessons, 16 ultrasound sweeps, 32 ultrasound exam cases, 3 published sites | `<consumer>/consumer.json` (co-located with each lesson, tour family, or site) | `assetkit.delivery` |
| **Reviews** | **~130–200 Reviews** (133 teaching assessments + ~71 ultrasound part reviews) | `reviews/` (existing immutable dated JSON files) | `assetkit.curation` |
| **Selections** | **~80–100 Selections** (81 teaching defaults + recommended revisions + R2 admissions) | `docs/gallery/maintained-selections.json` + recommendations | `assetkit.curation` |

### Key Structural Shifts From Today
1. **Fewer, cleaner Asset identities:** Multi-asset folders (`models/joints/` → 4 Assets; `models/peripheral_nerves/` → 3 Assets) declare their assets cleanly in one `assets.json`; multi-file shared-frame atlases (`body/anatomy-workshop-r1/body-3d-delivery/`) stay **1 Atlas Asset** with 18 Exports and 513 Parts; pure consumer folders (`lessons/body-systems/`) are **Consumers**, not asset packages.
2. **Immediate payload hygiene:** Today, **88 of 194** runtime exports exceed the `1.5 MB` soft cap and **38** exceed the `4.0 MB` hard cap (`579.1 MB` total). Porting makes bloated exports and low-utilization consumers immediately visible via `uv run assetkit economy`.
3. **Zero duplicate hand-edited indexes:** Per-package legacy manifests consolidate into `<package>/assets.json`, while Gallery's ~3,300-line `library-packages.json` and R2 sync plans become compiled projections from `assetkit.curation`.

---

## 2. What the Two Sets Roughly Look Like

### 2.1 Maintained Asset Set (`<package>/assets.json`)
```json
{
  "schemaVersion": 1,
  "assets": [
    {
      "id": "liver-s1233",
      "title": "Liver · s1233",
      "kind": "model",
      "families": ["digestive", "ultrasound-abdomen"],
      "concepts": ["liver"],
      "revisions": [
        {
          "id": "r03",
          "status": "active",
          "recipe": "recipes/build_liver.py",
          "provenance": {
            "source": "TotalSegmentator",
            "subject": "s1233",
            "license": "CC-BY-4.0",
            "units": "m",
            "laterality": "right",
            "registration": "native"
          },
          "capabilities": ["isolate-parts", "bmode-slice"],
          "exports": [
            {
              "id": "surface",
              "role": "teaching-mesh",
              "variant": "normal",
              "format": "glb",
              "path": "exports/r03/liver-surface.glb",
              "sha256": "...",
              "bytes": 320000,
              "triangles": 14000,
              "parts": [
                { "id": "liver-outer", "selector": "Liver_Outer", "concepts": ["liver"] }
              ]
            },
            {
              "id": "vessels",
              "role": "detail-overlay",
              "variant": "normal",
              "format": "glb",
              "path": "exports/r03/liver-vessels.glb",
              "sha256": "...",
              "bytes": 680000,
              "triangles": 28000,
              "parts": [
                { "id": "portal-vein", "selector": "PortalVein", "concepts": ["portal-vein"] },
                { "id": "hepatic-vein", "selector": "HepaticVein", "concepts": ["hepatic-vein"] }
              ]
            },
            {
              "id": "focal-lesion",
              "role": "pathology-overlay",
              "variant": "focal-lesion",
              "format": "glb",
              "path": "exports/r03/liver-focal-lesion.glb",
              "sha256": "...",
              "bytes": 75000,
              "triangles": 2400,
              "parts": [
                {
                  "id": "focal-lesion-01",
                  "selector": "FocalLesion_01",
                  "concepts": ["hepatic-focal-lesion"],
                  "provenance": {
                    "source": "authored-pathology-v1",
                    "subject": "synthetic",
                    "registration": "illustrative",
                    "limits": ["Authored teaching lesion fitted to s1233 right lobe"]
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 2.2 Consumer Set (`<consumer>/consumer.json`)
```json
{
  "schemaVersion": 1,
  "consumers": [
    {
      "id": "ultrasound:case:abdomen:focal-lesion",
      "title": "Abdominal Ultrasound · Focal Liver Lesion",
      "kind": "ultrasound-case",
      "requirements": [
        { "id": "parenchyma", "concepts": ["liver"], "subject": "s1233", "status": "satisfied" },
        { "id": "vessels", "concepts": ["portal-vein", "hepatic-vein"], "subject": "s1233", "status": "satisfied" },
        { "id": "lesion", "concepts": ["hepatic-focal-lesion"], "variant": "focal-lesion", "status": "satisfied" },
        { "id": "caval-junction", "concepts": ["hepatic-vein-ivc-junction"], "subject": "s1233", "status": "open-gap" }
      ],
      "pins": [
        { "requirement": "parenchyma", "asset": "liver-s1233", "revision": "r03", "export": "surface", "parts": ["liver-outer"], "sha256": "...", "registration": "native" },
        { "requirement": "vessels", "asset": "liver-s1233", "revision": "r03", "export": "vessels", "parts": ["portal-vein", "hepatic-vein"], "sha256": "...", "registration": "native" },
        { "requirement": "lesion", "asset": "liver-s1233", "revision": "r03", "export": "focal-lesion", "parts": ["focal-lesion-01"], "sha256": "...", "registration": "illustrative" }
      ]
    }
  ]
}
```

---

## 3. Common APIs by Submodule

| Workflow | Submodule & Python API | CLI Command |
| --- | --- | --- |
| **Validate everything** | `Workspace.load(repo).validate()` | `uv run assetkit validate` |
| **Plan / run recipe rebuild** | `build.plan_build(...)` → `build.run_build(..., apply=True)` | `uv run assetkit build <asset> <rev> [--apply]` |
| **Refresh hashes & GLB stats** | `build.sync_manifest(repo, path, apply=True)` | `uv run assetkit sync <pkg>/assets.json [--apply]` |
| **Delivery economy scorecard** | `ws.delivery.economy(ws.registry, policy)` | `uv run assetkit economy` |
| **Impact before edit/retire** | `ws.delivery.impact(target, ws.registry, ws.curation)` | `uv run assetkit impact <id\|path>` |
| **Candidate resolution** | `ws.delivery.resolve(cid, ws.registry, ws.vocab, ws.curation)` | `uv run assetkit resolve <consumer> [--req <id>]` |
| **Runtime load bundle** | `ws.delivery.bundle_for(cid, ws.registry)` | `uv run assetkit bundle <consumer>` |
| **Open anatomy gap backlog** | `ws.delivery.open_gaps(prefix)` | `uv run assetkit gaps [--prefix ultrasound:]` |
| **Compile Gallery / R2 plan** | `ws.curation.compile_gallery(...)` / `plan_r2_sync(...)` | `uv run assetkit compile --target gallery\|r2` |

---

## 4. End-to-End Walkthrough: Ultrasound Anatomy

1. **Audit & Gap Tracking:** Each ultrasound sweep/case declares `requirements` and `pins` in `consumer.json`. `uv run assetkit resolve ultrasound:sweep:abdomen-tracks:liver` matches `liver` and `gallbladder` to `s1233-body-delivery@r1` (`registration: native`, `qualified: false`) while surfacing `portal_vein_and_splenic_vein` and `inferior_vena_cava` as `unmatched`. `uv run assetkit gaps --prefix ultrasound:` produces the exact build backlog.
2. **Extending With Pathology / Foreign Details:** Keep **1 `liver-s1233` Asset**. Express **Fatty Liver** via B-mode material parameters (`variant: "fatty"`). Express **Focal Liver Lesion** via a lightweight additive `focal-lesion` overlay Export (`~75 KB`, `registration: illustrative`, foreign/synthetic provenance)—or a standalone `detail` Asset attached via a Consumer Pin transform. Overview stops still download only `liver-surface.glb` (~320 KB, 100% utilization).
3. **Refining & Rebuilding (`r02` → `r03`):** Run `uv run assetkit build liver-s1233 r03 --apply` → `uv run assetkit sync models/liver/assets.json --apply` → `uv run assetkit economy` (verifies size/triangle caps & utilization) → `uv run assetkit impact liver-s1233` (shows exact affected sweeps, tours, reviews, and selections) → record a dated `Review` bound to `r03`'s `sha256` → advance consumer `pins` and `Selection`.
4. **Runtime Consumption:** Ultrasound tour builders (`build_abdomen.py`, `assemble_tours.py`) call `ws.delivery.bundle_for(consumer_id, ws.registry)` to receive exact verified file paths, selected parts, transforms, licenses, and limits—eliminating hardcoded asset paths.

---

## 5. Phased Porting Plan

1. **Phase 1 — Pilot Slice:** Author native `sources/concepts.json`, `assets.json` for `models/liver` & `body/anatomy-workshop-r1`, and `consumer.json` for abdominal sweeps/cases.
2. **Phase 2 — Build-Loop Integration:** Wire ultrasound tour builders to `delivery.bundle_for()` and recipe rebuilds to `build.plan_build()` / `build.sync_manifest()`.
3. **Phase 3 — Full Port & Compilation:** Port remaining ~80 Assets and ~12 Lessons; compile Gallery's `library-packages.json` and R2 sync plans from `curation`, then retire legacy adapters.
