# Salivary glands: useful placement, rejected duct course
# 唾液腺：保留可用定位，拒绝有问题的导管走行

- **Improved:**3gland-pair silhouettes in coherent jaw/muscle context, instead of floating primitive blobs. Parotid duct gross course over the masseter is retained.
- **改进：**3对腺体在同源颌骨与肌肉参照中的外形和相对位置，不再只有孤立基本几何体；保留腮腺导管经过咬肌表面的大体走行。
- **Excluded, not repaired:**both submandibular ducts. The original left source curve crosses the modeled mylohyoid surface. The right course is unaccepted, not independently claimed faulty. See the optional diagnostic closeup.
- **排除而非修复：**两侧下颌下腺导管。已确认左侧源曲线穿过模型下颌舌骨肌表面；右侧尚未获得接受，不宣称也已独立证实错误。问题见独立诊断近景。
- **Still missing:**sublingual ducts, mucosal outlet papillae, verified lumens, full oral mucosa and complete duct routing. No clinical, surgical, flow, animation or full-organ validation. Original remains **Needs revision**, count delta **0**.
- **仍缺少：**舌下腺小导管、黏膜开口乳头、已验证管腔、完整口腔黏膜及导管走行。不是临床、手术、流动、动画或完整器官验证；原草稿仍需修改，通过数量不增加。

## Reading the images / 如何看图
- Comparison is unregistered: different source models and poses, not a morphometric before/after. Annotated context identifies the3gland families; native views preserve original source surfaces and effective transforms.
- 对比图未配准：来源及姿态不同，不能作形态测量。标注图说明3类腺体；原生视图保留源表面及有效变换。
- Primary GLB has6glands +2parotid ducts. Auxiliary context adds mandible and paired mylohyoid, superficial masseter, genioglossus. These are2roles for1scoped candidate, not2organ passes.
- 主GLB包含6个腺体及2条腮腺导管；辅助GLB加入下颌骨及双侧下颌舌骨肌、咬肌浅部、颏舌肌。它们是同一受限候选模型的不同角色，不是2个器官通过。
- Context has empty tooth sockets and coarse muscle surfaces. It is not a dental reconstruction or complete head. Colors are illustrative. Failure-view transparency/highlight are diagnostic display only; source geometry is unchanged.
- 参照含空牙槽及粗糙肌肉表面，不是牙科重建或完整头部。颜色仅作示意；问题视图的透明度及高亮只用于诊断展示，未改动源几何。

## Evidence and scope
Independent source verification checked effective matrices and nearest-source vertex preservation. Independent r02 subset check confirmed ONLY2rejected duct objects were removed; retained node/attribute/index/material payloads are unchanged. These checks do not establish complete anatomy. The failure test samples the Bezier centerline against native muscle triangles; it is not exhaustive tissue collision or clinical variation analysis.

Native views, annotations, comparison and failure closeup were actually inspected. Replay results are separate. No browser-runtime or clinical-expert pass is claimed. Existing accepted parotid-envelope history remains unchanged; this is not a duplicate whole-organ promotion.

## Lesson
A faithful export can faithfully preserve a misleading anatomical relationship. We excluded the unaccepted components and kept clear negative evidence rather than moving a duct to make a collision test pass. Both excluded objects are absent from default exports; the optional original-source diagnostic can be reproduced with an explicitly named diagnostic-only build flag.

## References
- WSU Lab22, pp19–20: https://learning.medicine.wsu.edu/wp-content/uploads/sites/4/2022/09/PDF-Lab-22.pdf — text and actual teaching figure inspected. The Netter-derived image/PDF is NOT redistributed.
- NIH NIDCR: https://www.nidcr.nih.gov/health-info/saliva-salivary-gland-disorders — broad gland locations only, not detailed route validation.

## Rights
Selected Z-Anatomy derivative meshes and source-derived renders: CC BY-SA4.0. Retain source License.txt, attribution to Z-Anatomy—the libre3D atlas, historical BodyParts3D—Database Center for Life Science—CC BY-SA2.1Japan, Kousaku Okubo, Gauthier Kervyn, Marcin Zielinski and upstream credited contributors. Source license inventory contains no salivary-specific exception; this is not an independent per-object rights audit. No separate public license is declared for newly authored scripts/prose. References retain their own rights.
