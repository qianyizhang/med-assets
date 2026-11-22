export const oralSpacesPath = 'use-cases/oral-spaces';
export const regionalPath = 'use-cases/regional-locators';
export const oralFolder = 'diagrams/oral_spaces/exports/r01/';
export const ovaryLocator = { id: 'ovary-tubal-context', system: 'reproductive', name: 'Ovary and tubal end' };
export const ovaryPickupDetail = 'reproductive-female-left-pickup';

export function teachingDisplayPath(original) {
  const slash = original.lastIndexOf('/');
  return original.slice(0, slash + 1) + 'display/' + original.slice(slash + 1, -4) + '.webp';
}

export const oralSpaces = {
  en: {
    question: 'Where is the oral vestibule relative to the teeth?',
    cue: 'In the coronal cutaway, find the teeth and gingiva. The vestibule lies toward the cheeks, and the oral cavity proper lies toward the tongue. The two spaces communicate.',
    title: 'Oral spaces · English cutaway',
    alt: 'Coronal teaching cutaway with the cheeks and vestibules outside the teeth, hard palate above the tongue and floor of the mouth below it.',
    limit: 'This original r01 schematic has no measured scale. Colors cue the mucosal reflections toward the alveolar and gingival region. The anterior lips and posterior fauces fall outside this plane.',
    review: 'The independent review accepted the cutaways for this 2D teaching task. The separate 3D mouth reconstruction remains rejected because the cheek and palate geometry did not form a coherent cavity.',
  },
  zh: {
    question: '口腔前庭位于牙齿的哪一侧？',
    cue: '在冠状面示意图中找出牙齿和牙龈。口腔前庭在靠颊的一侧，固有口腔在靠舌的一侧。两者相通。',
    title: '口腔空间关系 · 中文剖面图',
    alt: '冠状面教学示意图。颊和口腔前庭位于牙齿外侧，舌上方是硬腭，下方是口底。',
    limit: '本图为 r01 原创示意图，无实测比例。色彩提示黏膜向牙槽和牙龈区反折。前方的唇和后方的咽峡不在此切面内。',
    review: '独立评审认可这套二维教学图的有限用途。三维口腔重建仍未通过评审，颊部与腭部的几何结构未能形成连贯的口腔。',
  },
};

export const regionalLessons = [
  {
    id: 'aortic-arch',
    system: 'cardiovascular',
    name: 'Aortic arch branches',
    zh: '主动脉弓分支定位',
    question: 'Which branches arise directly from the aortic arch?',
    cue: 'Follow the three direct origins into the junction detail. The source groups the brachiocephalic trunk and right common carotid artery under 1, labels the left common carotid 2 and labels the left subclavian 3. The right subclavian (4) branches from the brachiocephalic system.',
    cueZh: '在连接处放大图中找出三个直接起点。源模型将头臂干与右颈总动脉合为编号 1，左颈总动脉为 2，左锁骨下动脉为 3。右锁骨下动脉（4）来自头臂干系统。',
    plates: [
      {
        original: 'reviews/aortic_tree_z/2026-10-29-arch-locators/overview-comparison.png',
        title: 'Arch region overview',
        alt: 'Matched views of the arch region, with four numbered source-group leaders added to the right panel.',
      },
      {
        original: 'reviews/aortic_tree_z/2026-10-29-arch-locators/junction-comparison.png',
        title: 'Enlarged junction detail',
        alt: 'Matched close views of the branch junction with the same four source-group numbers.',
      },
    ],
    scale: 'Each Original / Updated pair shares a camera, crop and scale. The junction view is enlarged separately. Source left is screen right.',
    limit: 'The Z-Anatomy r02 source retains open junctions, cropped ends and a joined trunk/carotid mesh. The leaders annotate named source surfaces. They establish neither vessel lumens nor a separate trunk/carotid boundary.',
    credit: 'Z-Anatomy (CC BY-SA 4.0), with historical BodyParts3D / DBCLS attribution.',
    model: 'models/aortic_tree_z/exports/r02/aortic_tree_z_source_frame.glb',
    package: 'lessons/aortic-arch-locators/README.md',
    review: 'reviews/aortic_tree_z/2026-10-29-arch-locators/README.md',
  },
  {
    id: 'pulmonary-vein',
    system: 'cardiovascular',
    name: 'Pulmonary vein in context',
    zh: '肺静脉同病例定位',
    question: 'Where is the pulmonary vein relative to the heart and lungs?',
    cue: 'In the posterior overview, find the pink component on the patient’s left (screen left). Compare it alone and beside the translucent heart and five lung lobes from the same s1233 case. Then follow the marked region to the detail below.',
    cueZh: '从后方总览找到患者左侧（画面左侧）的粉色部分。对照单独显示与加入同一病例 s1233 的半透明心脏和五个肺叶的视图，再看下方的局部放大图。',
    plates: [{
      original: 'lessons/pulmonary-vein-context/pulmonary-vein-context.png',
      title: 'Component alone and with same-case context',
      alt: 'Two matched columns show the retained pulmonary-vein component by itself and with the heart and lungs. Each column shows the posterior overview above its detail.',
    }],
    scale: 'Each row uses a matched camera and scale across columns. The lower row enlarges the region marked in the overview. All meshes share the source case frame.',
    limit: 'The metadata-cleanup r01 export retains only the largest component from the source extraction. Branch names, the other components and lumen continuity are unresolved. Color and transparency are display cues.',
    credit: 's1233 / tb3 source case and TotalSegmentator v2.0.1 contributors (CC BY 4.0 surface attribution and Apache 2.0 label notice).',
    model: 'models/pulmonary_vein/exports/metadata-cleanup-r01/pulmonary_vein.glb',
    package: 'lessons/pulmonary-vein-context/README.md',
    review: 'reviews/pulmonary_vein/2026-10-30-context/README.md',
  },
  {
    id: 'brain-source-cut',
    system: 'nervous',
    name: 'Brainstem source cut',
    zh: '脑干源模型截断',
    question: 'Where does the retained brain model end?',
    cue: 'Find the dashed bracket below both visible medulla surfaces. Match the bracket in the front overview to the enlarged view. In the body, the brainstem continues into the spinal cord.',
    cueZh: '在正面总览中找出延髓两侧可见表面下方的虚线括号，再在放大图中找到同一标记。人体的脑干向下与脊髓相连。',
    plates: [{
      original: 'reviews/brain/2026-10-29-source-cut/screenshots/front-comparison.png',
      title: 'Front overview and detail · Original / Updated',
      alt: 'Both updated front views mark the flat inferior cut with a dashed bracket outside the tissue.',
    }],
    scale: 'Original and Updated share the same crop and scale within each row. The detail magnifies pixels from the retained contact render.',
    limit: 'The bracket marks the inferior boundary of the BodyParts3D 4.0 atlas r2 export. It marks an editorial source cut. The missing continuation and reduced-resolution faceting remain.',
    credit: 'BodyParts3D / Anatomography, © Database Center for Life Science (CC BY 4.0). Bracket and viewports added for teaching.',
    model: 'models/brain/exports/bodyparts3d-4.0-atlas-r2/brain-source-frame.glb',
    package: 'lessons/brain-source-cut/README.md',
    review: 'reviews/brain/2026-10-29-source-cut/README.md',
  },
  ovaryLocator,
];
