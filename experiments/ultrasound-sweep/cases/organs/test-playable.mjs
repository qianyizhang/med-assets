import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chapters, pose, render} from './playable.js';
import {clipSectionEdge, cut, depthSpan, endpoints, footprintScale, plane} from './playable-geometry.js';
import {abdominalVolume} from './playable-abdomen.js';
import {breastVolume, thyroidVolume} from './playable-neck-breast.js';

const data=JSON.parse(readFileSync(new URL('./cases.json',import.meta.url)));
const volumes={abdomen:abdominalVolume,thyroid:thyroidVolume,breast:breastVolume};
const cases=Object.fromEntries(data.map(record=>[record.id,record]));
const select=(id, chapterId)=>chapters(cases[id]).find(chapter=>chapter.id===chapterId);
const shape=(record, chapter, id)=>volumes[record.family](record,chapter).find(item=>item.id===id);

function drawing(run) {
  const events=[];
  const gradient={addColorStop(){}};
  const ctx=new Proxy({}, {
    get(target, key) {
      if (key==='createLinearGradient') return ()=>gradient;
      if (key==='measureText') return text=>({width:text.length*6});
      return (...args)=> {
        assert.ok(args.every(value=>typeof value!=='number' || Number.isFinite(value)), key);
        if (['ellipse','moveTo','lineTo','fillText'].includes(key)) events.push([key,...args]);
      };
    }
  });
  run(ctx);
  return JSON.stringify(events);
}

let count=0;
let calibrated=0;
for(const record of data) {
  const route=chapters(record);
  const ids=new Set(route.map(chapter=>chapter.id));
  assert.equal(route.length,ids.size,record.id);
  for(const view of record.views) {
    assert.ok(route.some(chapter=>chapter.viewImage===view.image),view.image);
  }
  for(const chapter of route) {
    count++;
    assert.ok(record.views.some(view=>view.image===chapter.viewImage));
    assert.ok(chapter.frames>=3 && chapter.evidenceFrame>0 && chapter.evidenceFrame<chapter.frames-1);
    const rendered = drawing(ctx=>render(ctx,chapter,0,record));
    const acquired = drawing(ctx=>render(ctx,chapter,chapter.evidenceFrame,record));
    assert.notEqual(rendered,acquired,chapter.id);
    let legend;
    const overlayDrawing = drawing(ctx=>{
      legend=render(ctx,chapter,chapter.evidenceFrame,record,{overlay:true});
    });
    assert.equal(overlayDrawing,acquired,`overlay displaced contours, labels or marks in ${chapter.id}`);
    assert.equal(legend.length,new Set(legend.map(item=>item.label)).size);
    assert.ok(legend.every(item=>item.label && /^#[a-f0-9]{6}$/i.test(item.color)),chapter.id);
    assert.notEqual(drawing(ctx=>pose(ctx,chapter,chapter.evidenceFrame,record,{yaw:Math.PI/2})),
      drawing(ctx=>pose(ctx,chapter,chapter.evidenceFrame,record)),chapter.id);
    assert.notEqual(drawing(ctx=>pose(ctx,chapter,0,record)),
      drawing(ctx=>pose(ctx,chapter,chapter.frames-1,record)),chapter.id);
    const expected = [...(chapter.measurement ?? '').matchAll(/([\d.]+) mm/g)].map(x=>Number(x[1]));
    const marks=chapter.marks ?? [];
    assert.equal(marks.length,expected.length,chapter.id);
    marks.forEach((mark,index)=> {
      const pair=endpoints(volumes[record.family](record,chapter),plane(chapter,chapter.evidenceFrame),mark);
      assert.ok(pair,chapter.id);
      const distance=Math.hypot(pair[0][0]-pair[1][0],pair[0][1]-pair[1][1]);
      assert.ok(Math.abs(distance-expected[index]) < .051,
        `${chapter.id}: ${distance} mm vs ${expected[index]} mm`);
      calibrated++;
    });
  }
}

const biliary=cases['abdomen-biliary-stone'];
const supine=select(biliary.id,'biliary-stone-supine');
const rolled=select(biliary.id,'biliary-stone-roll');
assert.notDeepEqual(shape(biliary,supine,'Mobile calculus').center,shape(biliary,rolled,'Mobile calculus').center);
assert.deepEqual(shape(biliary,supine,'Gallbladder lumen').center,shape(biliary,rolled,'Gallbladder lumen').center);

const renal=cases['abdomen-renal-obstruction'];
const pre=select(renal.id,'renal-right-hydro');
const post=select(renal.id,'renal-right-postvoid');
assert.deepEqual(shape(renal,pre,'Dilated renal pelvis'),shape(renal,post,'Dilated renal pelvis'));
assert.ok(shape(renal,pre,'Bladder lumen').radii[1]>shape(renal,post,'Bladder lumen').radii[1]);

function legendAt(record,chapter,frame) {
  let legend;
  drawing(ctx=>{legend=render(ctx,chapter,frame,record,{overlay:true});});
  return new Map(legend.map(item=>[item.label,item.color]));
}

const thyroid=cases['thyroid-nodule'];
const thyroidPre=select(thyroid.id,'thyroid-axial-superior');
const thyroidIndex=select(thyroid.id,'thyroid-nodule-trans');
const nodule=shape(thyroid,thyroidIndex,'Solid hypoechoic nodule');
assert.equal(cut(nodule,plane(thyroidPre,thyroidPre.evidenceFrame)),null);
const noduleCenter=cut(nodule,plane(thyroidIndex,thyroidIndex.evidenceFrame));
const noduleAdjacent=cut(nodule,plane(thyroidIndex,thyroidIndex.evidenceFrame+5));
assert.ok(noduleCenter.w>noduleAdjacent.w && noduleCenter.h>noduleAdjacent.h);
const focalLegend=legendAt(thyroid,thyroidIndex,thyroidIndex.evidenceFrame);
assert.ok(focalLegend.has('Solid hypoechoic nodule'));
assert.notEqual(focalLegend.get('Solid hypoechoic nodule'),focalLegend.get('Right lobe'));
assert.equal(focalLegend.get('Solid hypoechoic nodule'),
  legendAt(thyroid,thyroidIndex,thyroidIndex.evidenceFrame+5).get('Solid hypoechoic nodule'));
assert.equal(legendAt(thyroid,thyroidIndex,0).has('Solid hypoechoic nodule'),false);
assert.equal(legendAt(thyroid,thyroidPre,thyroidPre.evidenceFrame).has('Solid hypoechoic nodule'),false);

const breast=cases['breast-axillary-node'];
const nodeLong=select(breast.id,'axillary-node-long');
const nodeShort=select(breast.id,'axillary-node-short');
assert.deepEqual(breastVolume(breast,nodeLong),breastVolume(breast,nodeShort));
const cortex=shape(breast,nodeShort,'Right axillary cortex');
const flat={...cortex,depthProfile:undefined};
const notch=depthSpan(cortex,.55,-.12);
const smooth=depthSpan(flat,.55,-.12);
assert.equal(notch[0],smooth[0]);
assert.ok(smooth[1]-notch[1]>.4 && smooth[1]-notch[1]<1.12);
assert.deepEqual(depthSpan(cortex,0,0),depthSpan(flat,0,0));
assert.deepEqual(endpoints(breastVolume(breast,nodeShort),plane(nodeShort,nodeShort.evidenceFrame),nodeShort.marks[0]),
  [[0,17.4],[0,21.2]]);
const wall=shape(breast,nodeShort,'Chest wall');
assert.equal(breastVolume(breast,nodeShort).filter(item=>item.id===wall.id).length,1);
const midline=cut(wall,{center:0,level:0,axis:2,normal:0});
assert.ok(midline.spanAt(0)[1]>midline.spanAt(0)[0]);
const fascia=shape(breast,nodeShort,'Pectoral fascia');
const retro=shape(breast,nodeShort,'Retromammary fat');
for(const [x,z] of [[0,0],[-.4,.2],[.4,-.4]]) {
  const posterior=depthSpan(retro,x,z);
  assert.equal(posterior[1],depthSpan(fascia,x,z)[0]);
  assert.ok(posterior[1]>posterior[0]);
}



const pancreaticLimit=cases['abdomen-limited-pancreas'];
for(const key of ['abd-pancreas-limited','pancreas-retry']) {
  const chapter=select(pancreaticLimit.id,key);
  const slice=plane(chapter,chapter.evidenceFrame);
  const gas = cut(shape(pancreaticLimit,chapter,'Bowel gas'),slice);
  const body = cut(shape(pancreaticLimit,chapter,'Pancreatic body'),slice);
  assert.ok(gas.y<body.y && Math.abs(body.x-gas.x)<gas.w);
  const visible = legendAt(pancreaticLimit,chapter,chapter.evidenceFrame);
  assert.ok(visible.has('Bowel gas'));
  assert.equal(visible.has('Pancreatic body'),false);
  assert.equal(visible.has('Pancreatic tail'),false);
  assert.equal(chapter.measurement,undefined);
}

const breastLimit=cases['breast-limited'];
for(const key of ['breast-retro-limited','breast-retro-limited-repeat']) {
  const chapter=select(breastLimit.id,key);
  const occluder=shape(breastLimit,chapter,'Left nipple');
  assert.ok(occluder.shadow>.9);
  assert.ok(cut(occluder,plane(chapter,chapter.evidenceFrame)));
  assert.equal(chapter.measurement,undefined);
}

// Check the full modeled gland and axillary tail against the *sampled* bands,
// including the lateral tissue that extends beyond the main breast center.
const screening=cases['breast-supplemental-screening'];
const bands=chapters(screening).filter(ch=>ch.id!=='breast-screen-map');
const nippleLevel=bands.find(ch=>ch.id==='breast-screen-right-1');
assert.deepEqual(clipSectionEdge([-10,3],[10,3],5,6),[[-5,3],[5,3]]);
assert.deepEqual(clipSectionEdge([0,-4],[0,8],5,6),[[0,0],[0,6]]);
assert.equal(clipSectionEdge([6,1],[6,5],5,6),null);

const scanDrawing=drawing(ctx=>render(ctx,nippleLevel,nippleLevel.evidenceFrame,screening));
for(const name of nippleLevel.layerLabels) assert.ok(scanDrawing.includes(name));
const gland=shape(screening,nippleLevel,'Fibroglandular tissue');
const tail=shape(screening,nippleLevel,'Fibroglandular tail');
const span=(s,x,z)=>{
  const u=(x-s.center[0])/s.radii[0],v=(z-s.center[2])/s.radii[2];
  return Math.hypot(u,v)<footprintScale(s,u,v) ? depthSpan(s,u,v) : null;
};
let sharedColumns=0;
for(let x=-100;x<=-55;x++) for(let z=5;z<=60;z++) {
  const a=span(gland,x,z),b=span(tail,x,z);
  if(a&&b&&a[0]<b[1]&&b[0]<a[1]) sharedColumns++;
}
assert.ok(sharedColumns>500,'The upper outer extension must connect to the same modeled gland.');
const deepFat=shape(screening,nippleLevel,'Retromammary fat');
for (const modeled of [gland,tail]) for(let x=-112;x<=-10;x++) for(let z=-56;z<=60;z++) {
  const tissueSpan=span(modeled,x,z);
  if(!tissueSpan) continue;
  assert.ok(tissueSpan[0]<=tissueSpan[1]);
  const fatSpan=span(deepFat,x,z);
  if(fatSpan) assert.ok(tissueSpan[1]<=fatSpan[0]-.1499);
}


const fields=bands.flatMap(ch=>Array.from({length:ch.frames},(_,i)=>({...plane(ch,i),half:ch.aperture/2,depth:ch.depth})));
for(const tissue of breastVolume(screening,bands[0]).filter(s=>['Fibroglandular tail','Fibroglandular tissue','Subcutaneous fat'].includes(s.id))){
  const [cx]=tissue.center,[rx]=tissue.radii;
  for(let x=Math.floor(cx-1.4*rx);x<=cx+1.4*rx;x++){
    const bounds=cut(tissue,{axis:2,normal:0,center:0,level:x});
    if (!bounds) continue;
    const planes=fields.filter(p=>Math.abs(p.level-x)<1e-6);
    for(let z=Math.ceil(bounds.x-bounds.w);z<=bounds.x+bounds.w;z++){
      const deep=bounds.spanAt?.(z)[1] ?? bounds.y+bounds.h;
      assert(planes.some(p=>Math.abs(z-p.center)<=p.half && deep<=p.depth),
        `Uncovered modeled ${tissue.id} at ${x}, ${z} mm`);
    }
  }
}

console.log(`Verified ${data.length} visits, ${count} changing plane/pose pairs, ${calibrated} case calipers, registered labels and calipers, orbit rendering, and modeled repeat/recovery outcomes.`);
