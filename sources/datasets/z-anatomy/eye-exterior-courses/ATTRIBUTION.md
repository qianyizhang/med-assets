# Attribution and source boundary

Selected source geometry and this derivative, including renders and teaching
images: **Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0**.
Underlying attribution: **BodyParts3D — The Database Center for Life Science —
CC BY-SA 2.1 Japan**. Credit Kousaku Okubo, Gauthier Kervyn and Marcin Zielinski.
The upstream license additionally credits **Cranial Nerves and Foramina —
University of Dundee, CAHID — CC BY 4.0**. Full upstream credits are retained in
[the retained upstream License.txt](../small-static-studies/upstream/License.txt). No kidney or inner-ear exception objects are selected.

- [Pinned Z-Anatomy source](https://github.com/Z-Anatomy/Models-of-human-anatomy/tree/bb293be456f6d2245191f37752d14ec76894740d)
- [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- [BodyParts3D](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html)

[provenance.json](provenance.json) pins the archive/member size and SHA256.
The exact original `Startup.blend` is retained externally and unchanged, rather
than duplicated in this small package. Replay requires that exact source.

Changes: evaluate only the 20 named surfaces with the source's existing subdivision
and curve settings; export static triangles and exact native matrices through a
common coordinate-basis conversion; preserve per-corner normals with vertex splits;
use four declared neutral display materials; group existing nodes into unilateral
scenes; render and add editorial teaching cues. No fitting, smoothing operation,
fusion, missing tissue reconstruction, source geometry edits or animation transfer.

[source-inventory.json](source-inventory.json) is the canonical record for source
names, parents, matrices, raw/evaluated counts, curve settings, modifiers, world
geometry hashes and raw material metadata. Material metadata is provenance only;
action-labelled shaders are not exported or interpreted as muscle function.
