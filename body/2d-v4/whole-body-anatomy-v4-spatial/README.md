# Whole-body anatomy · Spatial SVG asset pack
# 全身解剖 · 精修 SVG 素材包

Version 4.0-spatial · 2026-10-21

54 stable canonical anatomy IDs; 21 regional views (overview plus 20 focused views); 54 presentation-ready primary SVG parts. Each primary file shows one anatomical depiction. Paired organs or a distributed tissue network within a single view remain together. Additional depictions are explicit, labelled variants; complete source-coordinate groups are separate overlays.

保留 54 个稳定器官／组织标识，提供 54 个可直接用于展示的主要 SVG 素材。每个主要文件对应一个解剖视图；同一视图内的成对器官或分布性组织保留在一起。其他视图单列为标注清楚的变体，完整主图坐标图层则另存为叠加素材。

## Contents · 内容

- atlas.svg: complete refined atlas / 完整精修图谱
- head.svg: full-size refined head source with independent views / 独立多视图精修头部源图
- overview.svg: calm whole-body overview / 简洁全身总览
- regions/: focused, labelled regional views / 分区放大视图
- parts/<canonical-id>.svg: 54 single-view primary parts / 54 个单视图主要素材
- variants/: explicit additional views, named by anatomy and view / 按器官及视图命名的补充素材
- overlay-parts/: complete canonical groups retaining all source depictions / 保留全部源图示的完整器官图层
- manifest.json: canonical ID → primary → variants → overlay mapping, labels, source selectors, bounds, placements, centers and hashes / 标识映射、标签、选择器、边界、位置、锚点及校验值
- centers.json and head-centers.json: annotation anchors in their respective source spaces / 各源图坐标中的注释锚点
- parts-index.csv: compact design-tool index / 简明索引
- metadata.json: provenance and representation notes / 来源与示意说明
- previews/ and contact-sheets/: fresh raster previews / 新渲染的像素预览及检查拼图
- validation.json and SHA256SUMS.txt: validation and checksums / 验证记录与校验值

These are editable 2D SVG vectors, not 3D meshes, scanned anatomy, or a rigged model. No disease, injury, surgery, or treatment overlay is included.

本素材为可编辑二维 SVG 矢量图，不是三维网格、医学扫描或骨骼绑定模型；不含病变、损伤、手术或治疗叠加图层。

## Coordinate contract · 坐标约定

Source paths, transforms, gradients and definitions are preserved. Each manifest entry names its source_file and coordinate_space: atlas.svg, head.svg and kidney-depth.svg have independent coordinate spaces, and head-source parts must not be positioned directly in the full-body atlas without a separate transform. A cropped viewBox never translates geometry. Visible-pixel bounds exclude invisible interaction targets, and adaptive padding prevents strokes touching the export boundary. Any required export clip is explicitly recorded in the manifest. ViewBox x/y values may be nonzero; every width/height is positive.

保留源路径、变换、渐变和定义。清单以 source_file 和 coordinate_space 指定来源：atlas.svg 与 head.svg 使用各自独立坐标，头部源图素材不能未经变换直接放入全身主图。裁剪 viewBox 不改变几何坐标。裁剪依据实际可见像素，不让透明交互热区撑大画布；自适应留白避免笔画贴边。必要的裁剪均在清单中明示。viewBox 起点可非零，宽高始终为正。

To place an SVG image back in its named source, use reassemble_source.image_placement x/y/width/height. For a zero-origin editor workspace, use local_origin_transform and a 0 0 width height viewBox; keep that transform if later reassembling. Centers are annotation anchors, not anatomical centroids, and a canonical center may belong to a different source view than a variant. Use the viewBox center for an isolated part's initial layout if needed.

重组指定源图时按清单的 reassemble_source.image_placement 放置 SVG 图像。需零起点画布时使用 local_origin_transform，并保留该变换以便重组。centers 为注释锚点而非解剖重心，规范锚点可能属于另一个源视图；单独排版时可先使用 viewBox 中心。

## Reuse · 复用

Each SVG is self-contained: no scripts, remote images, downloaded fonts or network dependencies. All required original defs are included. When inlining multiple SVGs in one DOM, namespace IDs and update their references, or deduplicate a shared defs block. Host applications must provide their own accessible interaction handlers. Separate SVG image files require no ID rewriting.

每个 SVG 均可独立渲染，无脚本、远程图片、字体下载或网络依赖。将多个 SVG 内联到同一 DOM 时须为 ID 添加命名空间并同步引用，或合并共享 defs；以独立图片方式使用无需改写。交互逻辑由宿主应用提供。

Normal anatomy may be a baseline for future disease explanations. Keep later disease or treatment overlays separate and keyed to the same canonical ID. Do not treat independent reproductive configurations or pregnancy views as one person's simultaneous anatomy.

可将正常解剖作为后续疾病解说底图；病变或治疗图层应单独保存并沿用器官标识。不同生殖构型及妊娠视图不可拼为同一个人的同时解剖。

## Source and educational limits · 来源与教育用途限制

Authored educational vector artwork with reference-informed original head/torso drawings and explicitly attributed Servier-based support adaptations. It is not traced from medical scans or a licensed clinical atlas. Shapes, relative sizes, spatial overlap, tissue counts, vessel/nerve routes and magnification are simplified. Blood is a tissue sample; the reproductive overview is a locator; a fetal illustration does not specify a gestational week. All medical teaching or clinically consequential use needs qualified clinical review. Do not use for diagnosis, procedures or measurements.

本素材为参考资料辅助创作及明确署名改绘的教学矢量图，并非医学扫描描摹或临床图谱。形态、相对尺寸、空间重叠、组织数量、血管／神经走行和放大比例均有简化。血液为组织样本，生殖系统总览为定位图标，胎儿示意不指明特定孕周。医学教学及临床相关用途须经专业审核；不可用于诊断、操作或解剖测量。

## Validation · 验证

Automated checks cover 54 unique canonical IDs, nonzero viewBoxes, visible pixels, preserved selected source geometry, self-contained definitions, no internal workspace paths, no remote dependencies, safe crop clearances and SHA-256 checksums. Nine large contact sheets show all 54 primary exports for visual review. Review status is recorded in validation.json. A render/geometry check does not certify clinical accuracy.

自动检查覆盖 54 个唯一规范标识、有效 viewBox、可见像素、源几何保留、定义完整性、无内部路径及远程依赖、安全留边和 SHA-256 校验。九张大尺寸检查拼图覆盖全部主要素材，逐项像素检查状态见 validation.json。渲染与几何验证不等于临床准确性认证。

## Spatial connection · 全身定位关联

spatial.json maps every canonical part and all 21 regions to a whole-body bodyBox and, where useful, paired points. Each manifest part includes sourceView and bodyOrigin, and each SVG root carries data-source-view and data-body-origin-box. body-locator.svg supplies the same-coordinate body silhouette and skeletal landmarks.

Use bodyOrigin to show where the detail belongs before moving to sourceView. A bodyBox is a schematic locator, not an exact mapping of the detail geometry. Source-view changes are explicit: lateral or near-midline head, posterior gland detail, transverse kidney section, tissue samples, alternative pelvis and pregnancy examples have independent scale or orientation. The kidney depth view is viewed from the feet, with front at top, back at bottom, and patient right at image left. Do not imply a literal 3D morph or measured scan registration.

spatial.json 将全部规范素材与 21 个区域关联到全身定位框；各 SVG 与清单保留 sourceView 和 bodyOrigin。先显示人体中的位置，再转入细节视图。定位框是示意定位，不是细节几何的精确配准。侧位／近正中头部、腺体后面、肾横断面、组织样本、不同盆腔构型和妊娠例图均有独立方向或比例。肾横断图从足端看，图上为前、图下为后，人体右侧在图像左侧；不可暗示真实三维形变或扫描配准。

## Source relationships · 素材来源关系

source-relationships.json records the immediate source file, canonical group, selected depiction, original source coordinates and body origin for each exported primary, variant, overlay and region. artwork-provenance.json distinguishes original reference-informed drawings from attributed Servier adaptations and records each consulted source. license-registry.json and LICENSE-NOTES.md distinguish source-reference licenses from original-art rights. No reference-image directory is included.

Regional SVGs use explicit viewport clips to prevent neighboring views from bleeding into arbitrary aspect-ratio embeds. English labels retain data-en/data-zh attributes for localization. All previews were freshly rendered from the frozen v4 inputs. Historical v3 artwork and previews are not copied into this package.

See INTEGRATION.md for file selection, body-origin highlighting, camera transitions and explicit orientation changes.
