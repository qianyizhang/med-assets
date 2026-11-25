import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  chapters, landmarkAnchors, locatorProject, paintRaster, planeAt, pose, projectedShell,
  render, sampleRaster, sampledTrace,
} from './playable.js';
import { cross, dot, landmarks, sampler, softNames, sub, volumeFor } from './playable-model.js';

const cases = JSON.parse(await readFile(new URL('cases.json', import.meta.url), 'utf8'));
const names = stage => [null, ...volumeFor(stage).names, ...softNames];
const exam = id => chapters(cases.find(record => record.id === 'pregnancy-' + id));
const find = (list,id) => {
  const chapter=list.find(entry=>entry.id===id);
  assert.ok(chapter,`Missing chapter ${id}`);
  return chapter;
};
const viewTissues = chapter => {
  const raster=sampleRaster(chapter,chapter.evidenceFrame,220,140);
  const terms=names(chapter.stage);
  return new Set([...raster.labels].filter(id=>id>0).map(id=>terms[id]));
};
const close = (a,b,tolerance=1e-7) => assert.ok(Math.abs(a-b)<tolerance,`${a} != ${b}`);

let acquisitions=0;
const all = [];
for (const record of cases) {
  const list=chapters(record);
  const worked=new Set(record.views.map(view=>view.image));
  assert.equal(list.length,new Set(list.map(chapter=>chapter.id)).size);
  assert.deepEqual(new Set(list.map(chapter=>chapter.viewImage)),worked);
  for (const chapter of list) {
    acquisitions++;
    assert.ok(chapter.frames>=3 && chapter.evidenceFrame>=0 && chapter.evidenceFrame<chapter.frames);
    assert.ok(chapter.observation.length>20);
    const initial=planeAt(chapter,0), evidence=planeAt(chapter,chapter.evidenceFrame);
    assert.ok(Math.hypot(...sub(initial.contact,evidence.contact))>.10,`${record.id}/${chapter.id}: static probe`);
    for (const frame of [0,chapter.evidenceFrame,chapter.frames-1]) {
      const plane=planeAt(chapter,frame);
      close(dot(plane.normal,plane.width),0);
      close(dot(plane.normal,plane.beam),0);
      close(Math.hypot(...cross(sub(plane.target,plane.contact),plane.beam)),0);
    }
    const terminal=sampleRaster(chapter,chapter.evidenceFrame,88,55);
    const initialRaster=sampleRaster(chapter,0,88,55);
    assert.ok(terminal.labels.some(value=>value>0),`Empty evidence: ${record.id}/${chapter.id}`);
    assert.notDeepEqual(terminal.labels,initialRaster.labels,`Static section: ${record.id}/${chapter.id}`);
    all.push(chapter);
  }
}

const earlyNormal=exam('early-normal'), earlyAbnormal=exam('early-abnormal'), earlyLimited=exam('early-limited');
assert.ok(viewTissues(find(earlyNormal,'tv-location')).has('yolk_sac'));
assert.ok(viewTissues(find(earlyNormal,'tv-crl')).has('embryo'));
assert.ok(viewTissues(find(earlyAbnormal,'tubal-measure')).has('ectopic yolk sac'));
assert.ok(!viewTissues(find(earlyAbnormal,'tv-location')).has('gestational_sac'));
assert.ok(!viewTissues(find(earlyLimited,'tv-location')).has('embryo'));
assert.ok(!find(earlyLimited,'right-adnexal-repeat').measure);
assert.ok(!earlyLimited.some(chapter=>chapter.signal));
const tubal=find(earlyAbnormal,'tubal-measure');
assert.equal(tubal.measure.label,'18 mm');
const ectopicModel=sampler('early','abnormal',landmarks('early','abnormal'));
assert.equal(ectopicModel.scan(57,-13,-3),ectopicModel.ids['tubal sac']);
assert.equal(ectopicModel.scan(59,-13,-3),ectopicModel.ids['ectopic yolk sac']);
const tubalRaster=sampleRaster(tubal,tubal.evidenceFrame);
for (const anchor of landmarkAnchors(tubal,tubalRaster)) {
  assert.equal(tubalRaster.labels[anchor.y*tubalRaster.columns+anchor.x],anchor.id);
}

const normalNT=find(exam('first-normal'),'nt'), raisedNT=find(exam('first-abnormal'),'nt');
for (const [ch,mm] of [[normalNT,1.5],[raisedNT,4.5]]) {
  assert.ok(viewTissues(ch).has('NT space'));
  assert.ok(viewTissues(ch).has('posterior skin'));
  close(Math.hypot(...sub(ch.measure.a,ch.measure.b)),mm);
}
assert.ok(!find(exam('first-limited'),'nt-repeat').measure);

const midNormal=exam('mid-normal'), midAbnormal=exam('mid-abnormal'), midLimited=exam('mid-limited');
assertHeartLandmarks(midNormal);
assert.equal(midLimited.filter(chapter=>['lvot-repeat','rvot-repeat','3vv-repeat','3vt-repeat'].includes(chapter.id)).length,4);
for (const tag of ['lvot','rvot','3vv','3vt']) {
  const first=find(midLimited,tag), repeat=find(midLimited,tag+'-repeat');
  assert.ok(first.shadow && repeat.shadow);
  assert.notDeepEqual(planeAt(first,8).contact,planeAt(repeat,8).contact);
}
for (const tag of ['insertion','omphalocele-sagittal']) {
  assert.ok(viewTissues(find(midAbnormal,tag)).has('sac membrane'));
}
assert.ok(!viewTissues(find(midNormal,'insertion')).has('sac membrane'));
assert.ok(viewTissues(find(midNormal,'mid-cervix')).has('cervical_canal'));
assert.ok(viewTissues(find(midNormal,'right-hand')).has('hands'));

const lateNormal=exam('late-normal'), lateAbnormal=exam('late-abnormal'), lateLimited=exam('late-limited');
for (const [list,dvp,efw] of [[lateNormal,46,1970],[lateAbnormal,17,1294]]) {
  const ch=find(list,'fluid');
  assert.ok(viewTissues(ch).has('nearest fluid'));
  assert.ok(viewTissues(ch).has('maternal interface'));
  close(Math.hypot(...sub(ch.measure.a,ch.measure.b)),dvp,1e-2);
  assert.equal(find(list,'interval-growth').growth[1],efw);
}
for (const tag of ['fluid','fluid-repeat','ac-initial','ac-repeat']) {
  assert.ok(find(lateLimited,tag).shadow);
  assert.ok(!find(lateLimited,tag).measure);
}
assert.equal(find(lateLimited,'interval-growth').growth[1],null);
assert.equal(sampledTrace(find(lateNormal,'ua'),.75),16);
assert.equal(sampledTrace(find(lateAbnormal,'ua'),.75),0);
assert.equal(sampledTrace(find(lateAbnormal,'ua-repeat'),.75),0);
assert.equal(sampledTrace(find(lateLimited,'ua-repeat'),.18),null);
for (const list of [lateNormal,lateAbnormal]) {
  for (const chapter of list.filter(chapter=>chapter.signal)) {
    assert.ok(viewTissues(chapter).has('cord'));
    assert.equal(sampler('late',chapter.kind,landmarks('late',chapter.kind)).scan(...chapter.target),
      volumeFor('late').names.indexOf('cord')+1);
  }
}
for (const chapter of all.filter(entry=>entry.signal?.mode==='M-mode')) {
  const {cycles,seconds}=chapter.signal;
  for (let i=0;i<=cycles;i++) close(sampledTrace(chapter,i/cycles),sampledTrace(chapter,0));
  assert.ok(chapter.measurement.includes(String(Math.round(cycles*60/seconds))));
}
function paintPair(chapter,raster=sampleRaster(chapter,chapter.evidenceFrame)) {
  const standard=new Uint8ClampedArray(raster.pixels.length*4);
  const overlay=new Uint8ClampedArray(standard.length);
  assert.deepEqual(paintRaster(chapter,raster,standard,false),[]);
  const legend=paintRaster(chapter,raster,overlay,true);
  const unchanged=index=>standard.subarray(index*4,index*4+4)
    .every((value,channel)=>value===overlay[index*4+channel]);
  for (let i=0;i<raster.labels.length;i++) {
    if (!raster.labels[i]) assert.ok(unchanged(i),`Overlay colors outside anatomy in ${chapter.id}`);
  }
  return { raster,legend,overlay,standard,unchanged };
}

const ectopicOverlay=paintPair(tubal,tubalRaster);
const earlyNames=names('early');
const yolk=earlyNames.indexOf('ectopic yolk sac');
const fluid=earlyNames.indexOf('tubal sac');
const ringPixel=tubalRaster.labels.indexOf(yolk);
assert.ok(ringPixel>=0 && !ectopicOverlay.unchanged(ringPixel));
assert.ok(ectopicOverlay.legend.some(entry=>entry.label==='Ectopic yolk-sac rim'));
const innerPixels=[...tubalRaster.labels].filter((id,i)=>id===fluid && (
  tubalRaster.labels[i-2]===yolk || tubalRaster.labels[i+2]===yolk));
assert.ok(innerPixels.length>0,'Lucent pixels reach the sampled yolk-sac boundary');
const normalOverlay=paintPair(normalNT), raisedOverlay=paintPair(raisedNT);
const ntId=names('first').indexOf('NT space');
const ntCount=pair=>pair.raster.labels.reduce((n,id)=>n+(id===ntId),0);
assert.ok(ntCount(raisedOverlay)>ntCount(normalOverlay)*1.9);
for (const pair of [normalOverlay,raisedOverlay]) {
  assert.ok(pair.legend.some(entry=>entry.label==='NT space'));
  assert.ok(!pair.unchanged(pair.raster.labels.indexOf(ntId)));
}
const limitedAC=find(lateLimited,'ac-repeat');
const occluded=paintPair(limitedAC);
const clearRaster=sampleRaster({...limitedAC,shadow:undefined},limitedAC.evidenceFrame);
let occludedPixels=0;
for (let i=0;i<clearRaster.labels.length;i++) {
  if (clearRaster.labels[i] && !occluded.raster.labels[i]) {
    assert.ok(occluded.unchanged(i));
    occludedPixels++;
  }
}
assert.ok(occludedPixels>100);
assert.ok(paintPair(find(midAbnormal,'insertion')).legend.some(entry=>entry.label==='Sac membrane'));
assert.ok(paintPair(find(lateNormal,'fluid')).legend.some(entry=>entry.label==='Amniotic fluid pocket'));

function fakeCanvas() {
  const calls=[];
  const context={
    canvas:{ownerDocument:{createElement:()=>({getContext:()=>({
      createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),
      putImageData:()=>{},
    })})}},
    measureText:text=>({width:text.length*7}),
  };
  for (const method of [
    'fillRect','fillText','beginPath','moveTo','lineTo','arc','ellipse','fill',
    'stroke','save','restore','closePath','drawImage',
  ]) context[method]=(...args)=>calls.push([method,...(method==='drawImage'?args.slice(1):args)]);
  return {context,calls};
}
for (const chapter of [tubal,normalNT,find(midNormal,'four-chamber'),find(lateAbnormal,'ua-repeat')]) {
  const gray=fakeCanvas(),tinted=fakeCanvas();
  assert.deepEqual(render(gray.context,chapter,chapter.evidenceFrame,null),[]);
  assert.ok(render(tinted.context,chapter,chapter.evidenceFrame,null,{overlay:true}).length>0);
  // The title names the overlay; all scan, annotation and trace drawing geometry stays identical.
  const drawOps=calls=>calls.filter(([method,label])=>method!=='fillText'||!label.startsWith('MODELED '));
  assert.deepEqual(drawOps(gray.calls),drawOps(tinted.calls));
  const plane=planeAt(chapter,chapter.evidenceFrame);
  for (const yaw of [-Math.PI/2,-Math.PI/4,0,Math.PI/4,Math.PI/2]) {
    const project=locatorProject(chapter.stage,yaw);
    const shell=projectedShell(chapter.stage,project);
    assert.ok(shell.radii.every(radius=>Number.isFinite(radius)&&radius>0));
    assert.ok(Number.isFinite(shell.rotation));
    const model=fakeCanvas();
    pose(model.context,chapter,chapter.evidenceFrame,null,{yaw});
    const expected=[...project(plane.target),3];
    assert.ok(model.calls.some(([method,...args])=>method==='arc'
      && args.slice(0,3).every((n,i)=>n===expected[i])));
  }
  assert.notDeepEqual(locatorProject(chapter.stage,0)(plane.contact),
    locatorProject(chapter.stage,Math.PI/2)(plane.contact));
}

console.log(`Verified ${acquisitions} registered and changing chapters across ${cases.length} pregnancy exams.`);

function assertHeartLandmarks(list) {
  for (const [tag,landmarks] of [
    ['four-chamber',['right_atrium','left_atrium','right_ventricle','left_ventricle']],
    ['lvot',['left_ventricle','aortic_outflow']],
    ['rvot',['right_ventricle','pulmonary_outflow']],
    ['3vv',['aortic_outflow','pulmonary_outflow','superior_vena_cava']],
    ['3vt',['aortic_outflow','pulmonary_outflow','trachea']],
  ]) {
    const seen=viewTissues(find(list,tag));
    for (const name of landmarks) assert.ok(seen.has(name),`${tag}: missing ${name}`);
  }
}
