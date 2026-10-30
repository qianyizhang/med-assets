# Attribution and derivative limits

BodyParts3D, © The Database Center for Life Science (DBCLS), licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
per the [official license page](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html),
updated 2025-02-27. The repository retains the
[official license snapshot](../../../sources/datasets/bp3d-4.0-glands/official-license-snapshot.html),
[source frame](../../../sources/datasets/bp3d-4.0-glands/SOURCE-FRAME.md) and
[archive member identities](../../../sources/datasets/bp3d-4.0-glands/external-source-members.json).
Historical OBJ license headers remain unchanged. No provider endorsement is implied.

Inputs retained from PR #24:

| Source | Components | SHA256 |
| --- | --- | --- |
| [Hypothalamus export](../../../models/hypothalamus/exports/source-candidate-01/hypothalamus_source_frame.glb), 75,720 bytes | FJ1760 + FJ1808 | `b6d73d6b5a33006391a743c650ccc06b65b9b9afaaaebbcf1d05102d4399274c` |
| [Pituitary export](../../../models/pituitary/exports/source-candidate-01/pituitary_source_frame.glb), 22,296 bytes | FJ1796 | `8eae4c6d05b0c9de5128ae6f574a97265cb392a44567fcac5ea0b9b7f1dbca68` |

Earlier changes: atlas component selection, millimetres to metres with proper
glTF axis rotation, coordinate seam handling and illustrative smooth shading.
This derivative adds a boolean union, localized stalk smoothing and continuous
editorial vertex colors. The original exports and detailed source/history are
preserved; this separate teaching GLB and its review renders retain CC BY 4.0
attribution. It is not a new scan, measured stalk reconstruction, tissue
segmentation or clinical model. No lobes, nuclei, portal vessels or axons were added.

Anatomical relation reference: Satogami et al., *Normal Pituitary Stalk:
High-Resolution MR Imaging at 3T*, AJNR 31:355–359 (2010),
[doi:10.3174/ajnr.A1836](https://pmc.ncbi.nlm.nih.gov/articles/PMC7964128/).
The paper supports continuity and taper only; this derivative's shape and
editorial joins were not validated against its subjects or measurements.
