import * as THREE from '../../vendor/build/three.module.js';
import {abdominalChapters,abdominalVolume} from './playable-abdomen.js';
import {breastChapters,breastVolume,thyroidChapters,thyroidVolume} from './playable-neck-breast.js';
import {clipSectionEdge,cut,depthSpan,footprintScale,plane,sectionContour} from './playable-geometry.js';
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

export function profileGeometry(shape, segments=36, rings=24) {
  const geometry=new THREE.SphereGeometry(1,segments,rings);
  const points=geometry.getAttribute('position');
  for (let i=0; i<points.count; i++) {
    const u=-points.getX(i), v=points.getZ(i);
    const scale=footprintScale(shape,u,v);
    const [front,back]=depthSpan(shape,u*scale,v*scale);
    // Preserve the x/z contour. Interpolate from anterior to posterior
    // using the original sphere side; both sides join at zero depth span.
    const envelope=Math.sqrt(Math.max(0,1-u*u-v*v));
    const side=envelope<1e-5 ? .5 : Math.max(0,Math.min(1,(1-points.getY(i)/envelope)/2));
    points.setXYZ(i,-u*scale*shape.radii[0],shape.center[1]-(front+(back-front)*side),v*scale*shape.radii[2]);
  }
  points.needsUpdate=true;
  geometry.computeVertexNormals();
  return geometry;
}

function style(shape) {
  const id=shape.id;
  if (id==='Anechoic simple cyst') return ['#6aa899',.92];
  if (id.includes('axillary cortex')) return ['#dcaa65',.66];
  if (id.includes('Fibroglandular')) return ['#bc879f',.53];
  if (id==='Retromammary fat') return ['#d5b47e',.42];
  if (id==='Pectoral fascia') return ['#dad0c1',.38];
  if (id==='Chest wall') return ['#9c7d80',.32];
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


const sectionColors={
  'Fibroglandular tissue':'#ffd1ef',
  'Retromammary fat':'#f8c27a',
  'Pectoral fascia':'#f1f5fa',
};

function screeningContours() {
  const group=new THREE.Group();
  const lines=new Map(Object.entries(sectionColors).map(([name,color])=>{
    const geometry=new THREE.BufferGeometry();
    const buffer=new THREE.Float32BufferAttribute(new Float32Array(2*2*82*3),3);
    geometry.setAttribute('position',buffer.setUsage(THREE.DynamicDrawUsage));
    const line=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color,transparent:true,depthTest:false,depthWrite:false}));
    line.frustumCulled=false;
    line.renderOrder=8;
    group.add(line);
    return [name,line];
  }));
  function update(chapter,frame,pose,volume) {
    group.visible=Boolean(chapter.layerLabels);
    if (!group.visible) return;
    const sample=plane(chapter,frame);
    for (const [name,line] of lines) {
      const positions=line.geometry.getAttribute('position');
      let used=0;
      for (const shape of volume) {
        if (shape.id!==name) continue;
        const section=cut(shape,sample);
        if (!section) continue;
        const contour=sectionContour(section);
        for (const [i,a] of contour.entries()) {
          const segment=clipSectionEdge(a,contour[(i+1)%contour.length],pose.fieldWidth/2,pose.depth);
          if (!segment) continue;
          for (const [lateral,depth] of segment) {
            const point=[0,depth,0];
            point[sample.axis]=sample.center+lateral;
            point[sample.normal]=sample.level;
            positions.setXYZ(used++,...ras(point));
          }
        }
      }
      positions.needsUpdate=true;
      line.geometry.setDrawRange(0,used);
    }
  }
  function dispose() {
    for (const line of lines.values()) {
      line.geometry.dispose();
      line.material.dispose();
    }
  }
  return {group,update,dispose};
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
  const contours=record.id==='breast-supplemental-screening' ? screeningContours() : null;
  if (contours) anatomy.add(contours.group);
  const unit=new THREE.SphereGeometry(1,36,24);
  const materials=new Map();
  const profiled=new Map();
  let active,volume;
  function update(chapter,frame) {
    if (active!==chapter) {
      active=chapter;
      tissues.clear();
      volume=recipe.volume(record,chapter);
      for (const shape of volume) {
        if (/^skin$/i.test(shape.id)) continue;
        const [color,opacity]=style(shape);
        const key=color+opacity;
        if (!materials.has(key)) materials.set(key,new THREE.MeshStandardMaterial({
          color,opacity,transparent:opacity<1,depthWrite:opacity>=1,roughness:.84,
        }));
        let geometry=unit;
        if (shape.depthProfile) {
          const signature=[shape.depthProfile,shape.footprint,Math.sign(shape.center[0]),...shape.radii].join(':');
          if (!profiled.has(signature)) {
            // Keep the small node's analytic notch in a lighter 24×16 shell.
            const node=shape.depthProfile==='axillary-cortex';
            // Align the gland's azimuth topology with its 48 measured silhouette samples.
            const segments=node ? 24 : ['lobular','tail-region'].includes(shape.footprint) ? 48 : 36;
            profiled.set(signature,profileGeometry(shape,segments,node ? 16 : 24));
          }
          geometry=profiled.get(signature);
        }
        const tissue=new THREE.Mesh(geometry,materials.get(key));
        tissue.name=shape.id;
        tissue.position.fromArray(ras(shape.center));
        if (geometry===unit) tissue.scale.fromArray(shape.radii);
        tissues.add(tissue);
      }
    }
    const pose=beamOf(chapter,frame,record.family);
    contours?.update(chapter,frame,pose,volume);
    return pose;
  }
  update(initialChapter,initialChapter.evidenceFrame);
  function legend(chapter) {
    const slice=plane(chapter,chapter.evidenceFrame);
    const visible=recipe.volume(record,chapter).filter(shape=>{
      const section=cut(shape,slice);
      return section && Math.abs(section.x)<section.w+40 && section.y-section.h<chapter.depth
        && !/skin|nipple|septum|lumen|shadow/i.test(shape.id);
    });
    const scored=visible.map(shape=>{
      const measure=chapter.marks?.some(mark=>mark.id===shape.id || mark.inner===shape.id);
      const finding=/cyst|nodule|calculus|dilated|cortex|bowel gas/i.test(shape.id);
      const dx=shape.center[slice.axis]-slice.center;
      return {shape,score:(measure ? -100 : 0)+(finding ? -80 : 0)
        +(chapter.layerLabels?.includes(shape.id) ? -70 : 0)+Math.abs(dx)};
    }).sort((a,b)=>a.score-b.score);
    return [...new Map(scored.map(({shape})=>[shape.id,{label:shape.label ?? shape.id,color:(chapter.layerLabels && sectionColors[shape.id]) ?? style(shape)[0]}])).values()]
      .slice(0,5);
  }
  function dispose() {
    skin.geometry.dispose();
    skin.material.dispose();
    unit.dispose();
    contours?.dispose();
    for (const geometry of profiled.values()) geometry.dispose();
    for (const material of materials.values()) material.dispose();
  }
  return {anatomy,skin,radius:recipe.radius,update,legend,dispose};
}
