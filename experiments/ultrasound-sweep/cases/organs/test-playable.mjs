import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chapters, pose, render} from './playable.js';
import {cut, endpoints, plane} from './playable-geometry.js';
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
const fields=bands.flatMap(ch=>Array.from({length:ch.frames},(_,i)=>({...plane(ch,i),half:ch.aperture/2,depth:ch.depth})));
for(const tissue of breastVolume(screening,bands[0]).filter(s=>['Fibroglandular tail','Fibroglandular tissue','Subcutaneous fat'].includes(s.id))){
  const [cx,cy,cz]=tissue.center,[rx,ry,rz]=tissue.radii;
  for(let x=Math.ceil(cx-rx);x<=cx+rx;x++){
    const factor=Math.sqrt(Math.max(0,1-((x-cx)/rx)**2));
    const planes=fields.filter(p=>Math.abs(p.level-x)<1e-6 && cy+ry<=p.depth);
    for(let z=Math.ceil(cz-rz*factor);z<=cz+rz*factor;z++)
      assert(planes.some(p=>Math.abs(z-p.center)<=p.half),`Uncovered modeled ${tissue.id} at ${x}, ${z} mm`);
  }
}

console.log(`Verified ${data.length} visits, ${count} changing plane/pose pairs, ${calibrated} case calipers, registered labels and calipers, orbit rendering, and modeled repeat/recovery outcomes.`);
