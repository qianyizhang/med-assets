import * as THREE from '../../vendor/build/three.module.js';
import {abdominalChapters,abdominalVolume} from './playable-abdomen.js';
import {breastChapters,breastVolume,thyroidChapters,thyroidVolume} from './playable-neck-breast.js';
import {cut,plane} from './playable-geometry.js';
import {fitCaseSkin} from './playable-scene-skin.js';

// Native voxel anchors place each modeled midline and scan region on the delivered exterior.
const recipes={
  abdomen:{chapters:abdominalChapters, volume:abdominalVolume, sources:['liver','gallbladder'],
    anchors:{liver:[137,207],gallbladder:[137,207]}, radius:118},
  thyroid:{chapters:thyroidChapters, volume:thyroidVolume, sources:['thyroid-right','thyroid-left','carotid-right','carotid-left'],
    anchors:{'thyroid-right':[132,385]}, radius:72},
  breast:{chapters:breastChapters, volume:breastVolume, sources:['axilla','breast','breast-subareolar'],
    anchors:{axilla:[33,289],breast:[33,289],'breast-subareolar':[33,289]}, radius:106},
};

const ras=([x,y,z])=>[-x,-y,z];

function scanPoint(chapter, frame) {
  const slice=plane(chapter,frame);
  const point=[0,0,0];
  point[slice.axis]=slice.center;
  point[slice.normal]=slice.level;
  return ras(point);
}

function beamOf(chapter,frame,family) {
  const height=chapter.spectral ? 242 : 365;
  const scale=height/chapter.depth;
  const fieldWidth=Math.min(670/scale,chapter.aperture ?? (chapter.depth<50 ? 66 : 105));
  const near=62/scale, far=322/scale;
  return {
    contact:scanPoint(chapter,frame),
    width:chapter.axis===0 ? [-1,0,0] : [0,0,1],
    beam:[0,-1,0], depth:chapter.depth,
    probe:chapter.linear ? 'linear' : 'curved',
    ...(chapter.linear ? {fieldWidth,probeWidth:family==='thyroid' ? 40 : 48} : {
      fieldWidth:near*2,halfAngle:Math.atan((far-near)/chapter.depth)*180/Math.PI,
    }),
  };
}

function style(shape) {
  const id=shape.id;
  if (/gas|calculus|clavicle|vertebral|diaphragm|septum|fascia/i.test(id)) return ['#dac8a0',.64];
  if (/cyst|nodule|cortex|pelvis|calyx|duct|node/i.test(id)) return ['#e4a760',.88];
  if (/hilum/i.test(id)) return ['#eccc8b',.72];
  if (/kidney|spleen|pancrea/i.test(id)) return ['#ad665f',.58];
  if (/hepatic lobe/i.test(id)) return ['#aa5d51',.48];
  if (/gallbladder/i.test(id)) return ['#91af68',.55];
  if (/lobe|isthmus/i.test(id)) return ['#cf8b70',.55];
  if (/arter|aorta|carotid/i.test(id)) return ['#cf6b57',.76];
  if (/vein|IVC/i.test(id)) return ['#729fb5',.70];
  if (/fat|muscle|chest wall/i.test(id)) return ['#caa184',.32];
  return ['#b2a594',.47];
}

export async function createCaseModel(record,initialChapter) {
  const recipe=recipes[record.family];
  const paths=recipe.chapters(record).map(c=>[0,c.frames-1].map(frame=>{
    const [x,,z]=scanPoint(c,frame);
    return [x,z];
  }));
  const skin=await fitCaseSkin(recipe.sources,recipe.anchors,paths,
    record.family==='breast' ? {reach:24,blend:24} : undefined);
  const anatomy=new THREE.Group();
  const tissues=new THREE.Group();
  anatomy.add(skin,tissues);
  const unit=new THREE.SphereGeometry(1,36,24);
  const materials=new Map();
  let active;
  function update(chapter,frame) {
    if (active!==chapter) {
      active=chapter;
      tissues.clear();
      for (const shape of recipe.volume(record,chapter)) {
        if (/^skin$/i.test(shape.id)) continue;
        const [color,opacity]=style(shape);
        const key=color+opacity;
        if (!materials.has(key)) materials.set(key,new THREE.MeshStandardMaterial({
          color,opacity,transparent:opacity<1,depthWrite:opacity>=1,roughness:.84,
        }));
        const tissue=new THREE.Mesh(unit,materials.get(key));
        tissue.name=shape.id;
        tissue.position.fromArray(ras(shape.center));
        tissue.scale.fromArray(shape.radii);
        tissues.add(tissue);
      }
    }
    return beamOf(chapter,frame,record.family);
  }
  update(initialChapter,initialChapter.evidenceFrame);
  function legend(chapter) {
    const slice=plane(chapter,chapter.evidenceFrame);
    const visible=recipe.volume(record,chapter).filter(shape=>{
      const section=cut(shape,slice);
      return section && Math.abs(section.x)<section.w+40 && section.y-section.h<chapter.depth
        && !/skin|nipple|fascia|septum|wall|lumen|shadow/i.test(shape.id);
    });
    const scored=visible.map(shape=>{
      const measure=chapter.marks?.some(mark=>mark.id===shape.id || mark.inner===shape.id);
      const finding=/cyst|nodule|calculus|dilated|cortex|bowel gas/i.test(shape.id);
      const dx=shape.center[slice.axis]-slice.center;
      return {shape,score:(measure ? -100 : 0)+(finding ? -80 : 0)+Math.abs(dx)};
    }).sort((a,b)=>a.score-b.score);
    return [...new Map(scored.map(({shape})=>[shape.id,{label:shape.label ?? shape.id,color:style(shape)[0]}])).values()]
      .slice(0,5);
  }
  function dispose() {
    skin.geometry.dispose();
    skin.material.dispose();
    unit.dispose();
    for (const material of materials.values()) material.dispose();
  }
  return {anatomy,skin,radius:recipe.radius,update,legend,dispose};
}
