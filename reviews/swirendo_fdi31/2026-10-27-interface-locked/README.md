# FDI 31: retain the interface-locked research candidate

**Draft evidence only. The 26.5 MB model and review images remain local; this PR
ships neither payloads nor LFS pointers. No canonical asset changes.**

## Decision

| Version | Bytes | Triangles | Decision |
|---|---:|---:|---|
| Extracted master | 51,333,280 | 2,569,422 | Preserve as reference, not anatomical ground truth |
| Interface-locked candidate | 26,524,356 | 1,328,980 | Retain for further review |
| Further simplification 0.10 | 21,562,592 | 1,080,892 | Reject for promotion |
| Further simplification 0.05 | 19,908,672 | 998,198 | Reject for promotion |

- **Improvement over r03:** 915,501 original protected triangles retained exactly;
  375,466 new exterior triangles passed conservative foreign-label-support exclusion.
  The 3 historical local interface witnesses no longer depart from their master
  interfaces in matched sections. This is not a global no-overlap certificate.
- **Why stop:** both smaller trials passed technical checks but contracted local
  geometric islands; 0.05 also flattened a dentin detail. Those islands are not
  verified anatomical structures. No evidence justifies this loss as an improvement.
- **Tradeoff:** 48.3% fewer faces than the master, but about twice historical r03.
  File-size reduction is not a measured runtime gain. No further trials this round.

## Evidence and separate gates

[Evidence index](evidence-index.json) binds exact local media hashes/sizes and
checksums of the included technical receipts. It is a scoped decision record,
**not** a foundation record or claim that missing media can be read from GitHub.

| Gate | Evidence / limit |
|---|---|
| Technical | [Independent export/topology checks](interface-independent-validation.json), [old witness checks](old-witness-location-check.json), [sampled occupancy screen](matched-occupancy-screen.json). No new duplicate/zero-area defects; inherited defects remain. |
| Visual utility | Prior matched context/zoom sections reviewed; representative interface and rejection figures re-inspected while preparing this MR. Images are **not delivered here**. Local sections do not certify full 3-D appearance. |
| Refinement | [Comparison receipt](refinement-comparison.json). 2 trials; sampled errors, not global bounds or biological accuracy. Builds: 341.6/603.5 s; peak child RSS about 1.96/1.94 GiB. |
| Anatomy / clinical | Unapproved. Prepared T2 specimen, `inprogress` labels, source truncation, open/nonmanifold geometry and inherited coincident triangles remain. |
| Runtime | Unmeasured. Complete 5-way 3-D rendering was not finished; no browser/FPS claim. |
| Payload | Blocked pending separately authorized existing transport flow. No source download, upload or Site publication performed for this MR. |

Use the [review contract](../../../docs/REVIEW_CONTRACT.md); the medical QA priority
clarification is proposed separately in [PR93](https://github.com/qianyizhang/med-assets/pull/93).
This decision does not duplicate or depend on unmerged rule text.

## Provenance and delivery boundary

Benz, Leander; Heck, Katrin; Walter, Elias (2024), *Data: Visualization of Pulpal
Structures by SWIR in Endodontic Access Preparation*,
[DOI 10.5282/ubm/data.477](https://data.ub.uni-muenchen.de/477/),
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Derivative change: protected source interfaces with exterior-only simplification;
4 source-labelled layers, original specimen frame and mm-to-m scale retained.
Preserve attribution and ShareAlike for derivatives, not a repository-wide license.

[Existing source mapping](../../../sources/datasets/swirendo-pilot/source-map.json)
and [historical r03 ingestion](../../../docs/dental-atlas/pilot-ingestion.md) remain
unchanged. This is a new candidate, not a clean r03 rebuild. Original inputs,
recipes, full receipts and rejected binaries remain local. This PR is not a
self-contained geometry reproduction package.

**Next delivery step:** authorize staging the exact candidate and 4 PNGs on the
existing public Dental review Site, then a separate hash-named manifest-only PR
under the [bounded transport policy](../../../transport/README.md). Independent
fresh LFS readback must precede any candidate/image pointers. Only then add a
complete export/review package. No new host, credentials, public-audience change,
private-account data, rejected trial binaries or canonical promotion is needed.
