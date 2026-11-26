import * as THREE from '../../vendor/build/three.module.js';
import {acquisitionPlane,chapters} from './playable.js';
import {getAcquisition,tubesAt} from './playable-model.js';
import {fitCaseSkin} from '../organs/playable-scene-skin.js';

const sides=['Right','Left'];
const sideShift=side=>side==='Right' ? -19 : 19;
const ras=(side,[x,y,z])=>[-(x+sideShift(side)),-y,z];

function pose(record,chapter,frame) {
  const acquisition=getAcquisition(record,chapter,frame);
  const {horizontal,depth}=acquisitionPlane(record,chapter,acquisition);
  return {
    contact:ras(chapter.side,[acquisition.anchorX,0,acquisition.z]),
    width:[-horizontal.x,-horizontal.y,horizontal.z],
    beam:[-depth.x,-depth.y,depth.z],depth:acquisition.depth,
    fieldWidth:acquisition.width,probe:'linear',probeWidth:42,
  };
}

function loft(rings, side, annular=false) {
  const n=rings[0].length;
  const vertices=rings.flatMap(ring=>ring.flatMap(point=>ras(side,point)));
  const indices=[];
  const copyRing = (row) => {
    const first=vertices.length/3;
    for (const point of rings[row]) vertices.push(...ras(side,point));
    return first;
  };
  const connect = (row,next) => {
    // The terminal cut is flat. Split its vertex normals from the longitudinal
    // wall so reducing straight runs cannot round over the displayed cut edge.
    const endFace=rings[row][0][2]===rings[next][0][2];
    const lower=endFace ? copyRing(row) : row*n;
    const upper=endFace ? copyRing(next) : next*n;
    for (let j=0;j<n;j++) {
      const k=(j+1)%n;
      indices.push(lower+j,lower+k,upper+j,lower+k,upper+k,upper+j);
    }
  };
  for (let row=0;row+1<rings.length;row++) connect(row,row+1);
  if (annular) {
    connect(rings.length-1,0);
  } else {
    const bottom=copyRing(0), top=copyRing(rings.length-1);
    for (let j=1;j<n-1;j++) indices.push(bottom,bottom+j+1,bottom+j,top,top+j,top+j+1);
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function tubeRing({z,tube},inside=false) {
  const {x,y,rx,ry,lx,ly,lrx,lry}=tube;
  const [cx,cy,a,b]=inside ? [lx,ly,lrx,lry] : [x,y,rx,ry];
  return radial((cos,sin)=>[cx+a*cos,cy+b*sin,z]);
}
// Bound the sampled outer and lumen contours together. A straight segment
// needs only its end rings; the bulb and eccentric stenosis retain extra rings.
function retainedSections(samples, tolerance=.025) {
  const keep=new Set([0,samples.length-1]);
  function split(start,end) {
    const a=samples[start], b=samples[end];
    let worst=tolerance, at;
    for (let i=start+1;i<end;i++) {
      const actual=samples[i], t=(actual.z-a.z)/(b.z-a.z);
      const delta=(key)=>actual.tube[key]-(a.tube[key]+(b.tube[key]-a.tube[key])*t);
      const outer=Math.hypot(delta('x'),delta('y'))+Math.max(Math.abs(delta('rx')),Math.abs(delta('ry')));
      const lumen=Math.hypot(delta('lx'),delta('ly'))+Math.max(Math.abs(delta('lrx')),Math.abs(delta('lry')));
      if (Math.max(outer,lumen)>worst) { worst=Math.max(outer,lumen); at=i; }
    }
    if (at===undefined) return;
    keep.add(at);
    split(start,at);
    split(at,end);
  }
  split(0,samples.length-1);
  return samples.filter((_,i)=>keep.has(i));
}

function wallInterior(sample) {
  if (!sample.tube.mural) return tubeRing(sample,true);
  // The tissue classifier places eccentric plaque between this wall and the blood pool.
  const {tube,z}=sample;
  const scale=1-tube.wall/Math.max(tube.rx,tube.ry);
  return radial((cos,sin)=>[tube.x+tube.rx*scale*cos,tube.y+tube.ry*scale*sin,z]);
}
function radial(point) {
  return Array.from({length:40},(_,seg)=>{
    const theta=seg*Math.PI/20;
    return point(Math.cos(theta),Math.sin(theta));
  });
}

function plaqueRings({z,tube}) {
  const {x,y,rx,ry,lx,ly,lrx,lry,wall}=tube;
  const outline=1-wall/Math.max(rx,ry);
  const dx=x-lx,dy=y-ly;
  const inner=radial((cos,sin)=>{
    const u=rx*cos,v=ry*sin;
    const a=(u/lrx)**2+(v/lry)**2;
    const b=2*(dx*u/lrx**2+dy*v/lry**2);
    const c=(dx/lrx)**2+(dy/lry)**2-1;
    const exit=(-b+Math.sqrt(Math.max(0,b*b-4*a*c)))/(2*a);
    const t=Math.min(outline,Math.max(0,exit));
    return [x+t*u,y+t*v,z];
  });
  const outer=radial((cos,sin)=>[x+outline*rx*cos,y+outline*ry*sin,z]);
  return [outer,inner];
}

function plaqueGeometry(samples,side) {
  const outlines=samples.map(plaqueRings);
  const outer=outlines.map(([ring])=>ring);
  const inner=outlines.map(([,ring])=>ring);
  // Join the outer and residual-lumen contours at both ends without placing
  // a cap across the visible lumen.
  return loft([...outer,...inner.reverse()],side,true);
}

function mesh(geometry,name,color,opacity) {
  const result=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({
    color,opacity,transparent:opacity<1,depthWrite:opacity===1,side:THREE.DoubleSide,roughness:.85,
  }));
  result.name=name;
  return result;
}

function vessels(record,side) {
  const group=new THREE.Group();
  const tubes=new Map();
  for (let z=0;z<=141;z+=.8) {
    for (const tube of tubesAt(record,side,z)) {
      if (!tubes.has(tube.name)) tubes.set(tube.name,[]);
      tubes.get(tube.name).push({z,tube});
    }
  }
  for (const [id,samples] of tubes) {
    const venous=id==='IJV';
    const sections=retainedSections(samples);
    const shell=[...sections.map(sample=>tubeRing(sample)),...sections.map(wallInterior).reverse()];
    group.add(mesh(loft(shell,side,true),
      side+' '+id,venous ? '#6498b0' : '#c96659',venous ? .54 : .46));
    group.add(mesh(loft(sections.map(sample=>tubeRing(sample,true)),side),
      side+' '+id+' lumen',venous ? '#2d617e' : '#9a463d',.72));
    const plaque=samples.filter(({tube})=>tube.mural);
    if (plaque.length>1) group.add(mesh(plaqueGeometry(plaque,side),'Carotid plaque','#e8c175',.95));
  }
  return group;
}

export async function createCaseModel(record) {
  const paths=chapters(record).map(section=>[0,section.frames-1].map(frame=>{
    const [x,,z]=pose(record,section,frame).contact;
    return [x,z];
  }));
  const sources=['carotid-right','carotid-left','thyroid-right','thyroid-left'];
  // The clavicle-to-mandible model maps from the lower s1127 neck to
  // beneath the chin. This registration uses the same exterior for both sides.
  const anchors=Object.fromEntries(sources.map(id=>[id,[132,350]]));
  const skin=await fitCaseSkin(sources,anchors,paths,{reach:18,blend:29});
  const anatomy=new THREE.Group();
  anatomy.add(skin,...sides.map(side=>vessels(record,side)));
  return {
    anatomy,skin,radius:96,
    update:(chapter,frame)=>pose(record,chapter,frame),
    legend(chapter) {
      const items=[
        {label:'Carotid arteries',color:'#c96659'},
        {label:'Internal jugular veins',color:'#6498b0'},
      ];
      if (chapter.target==='VA') items[0].label='Vertebral and carotid arteries';
      if (record.kind==='abnormal' && chapter.side==='Right') items.push({label:'Carotid plaque',color:'#e8c175'});
      return items;
    },
    dispose() {
      anatomy.traverse(object=>{
        object.geometry?.dispose();
        object.material?.dispose();
      });
    },
  };
}
