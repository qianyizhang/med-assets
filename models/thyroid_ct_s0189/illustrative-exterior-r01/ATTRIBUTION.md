# Source and modifications

Jakob Wasserthal et al., University Hospital Basel, **TotalSegmentator v2.0.1**.
[Dataset record](https://zenodo.org/records/10047292),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [full license](CC-BY-4.0.txt).

Retained source: [s0189 thyroid export](../exports/source-candidate-02/thyroid_ct_s0189_source_frame.glb),
SHA256 `4add07e2efed2d67efb1d4ba225a109fe448043c79182e3d2e1a96e671534883`.
The [original attribution](../provenance/source-candidate-02/migration-2026-10-24/ATTRIBUTION.md)
and [external-source record](../provenance/source-candidate-02/migration-2026-10-24/external-source.json)
remain authoritative for the preceding extraction and coordinate conversion.

2026-10-29 modification: localized Blender Laplacian Smooth treatment of the
existing exterior, with reduced influence on the central bridge and opposite
face. Geometry changes; topology, native source frame, material and original
source are retained. Actual Cycles images depict clean imports of the separate
source and derivative. Color remains illustrative.

Retain the source credit, license and modification notice with the derivative and
its images. No repository-wide license or author endorsement is inferred.

This is one public clinical-source sample, not a normal/healthy atlas. The
presentation treatment is not a new segmentation, clinical validation or measured
tissue surface. Same-sample tracheal clearance and consumer runtime are unverified.

仅为公开临床来源样本的示意外表面；并非健康标准图谱或改进后的分割。
原始模型保留；不新增内部结构。气管关系及浏览器运行尚未验证。
