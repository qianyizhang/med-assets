'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('./controller.js');
function fixture(contract) {
  let now=0;
  const labels=contract ? contract.labels : C.LABELS;
  const parts=labels.map((label,i)=>({label,matrix:C.IDENTITY.map((v,k)=>k===12?i:v)}));
  const c=C.createController(parts,contract,()=>now);
  const frames=[{time:0,reveal:0,isolate:null},{time:1000,reveal:1,isolate:labels[0]},{time:2000,reveal:0,isolate:null}];
  c.setTimeline(frames);
  return {c,frames,parts,set:value=>now=value};
}
test('fake clock drives exact interpolation and stepped named isolation',()=>{
  const {c,set}=fixture(); c.play(); set(500); c.tick();
  assert.deepEqual(c.snapshot(),{reveal:.5,isolate:null});
  set(1000); c.tick(); assert.deepEqual(c.snapshot(),{reveal:1,isolate:'enamel'});
  set(1500); c.tick(); assert.deepEqual(c.snapshot(),{reveal:.5,isolate:'enamel'});
  set(5000); c.tick(); assert.deepEqual(c.snapshot(),{reveal:0,isolate:null});
  assert.deepEqual(c.playback(),{position:2000,playing:false,duration:2000});
});
test('repeated play is idempotent, pause samples elapsed time, resume excludes pause',()=>{
  const {c,set}=fixture(); c.play(); set(200); c.play(); set(400); c.pause();
  assert.equal(c.snapshot().reveal,.4); set(10000); c.tick(); assert.equal(c.snapshot().reveal,.4);
  c.play(); set(10100); c.tick(); assert.equal(c.snapshot().reveal,.5);
});
test('scrub is absolute, pauses, and exact end can replay',()=>{
  const {c,set}=fixture(); c.play(); set(300); c.scrub(1500); set(1000); c.tick();
  assert.deepEqual(c.snapshot(),{reveal:.5,isolate:'enamel'});
  c.scrub(500); assert.equal(c.snapshot().reveal,.5);
  c.scrub(2000); c.play(); assert.deepEqual(c.snapshot(),{reveal:0,isolate:null});
});
test('reset stops queued ticks and restores original matrices across repeated interruptions',()=>{
  const {c,set,parts}=fixture(), baseline=c.resolve(), original=JSON.stringify(parts);
  for(let i=0;i<25;i++){
    c.play(); set(i*1000+500); c.tick(); c.dispatch({type:'reset'}); set(i*1000+800); c.tick();
    assert.deepEqual(c.resolve(),baseline);
    assert.deepEqual(c.playback(),{position:0,playing:false,duration:2000});
  }
  assert.equal(JSON.stringify(parts),original);
});
test('every valid manual action pauses and preserves manual semantics until explicit play',()=>{
  for(const action of [{type:'reveal',value:.25},{type:'isolate',label:'pulp'},{type:'all'}]){
    const {c,set}=fixture(); c.play(); set(1000); c.tick(); c.dispatch(action);
    const state=c.snapshot(); assert.equal(c.playback().playing,false);
    set(1900); c.tick(); assert.deepEqual(c.snapshot(),state);
    c.play(); assert.deepEqual(c.snapshot(),{reveal:1,isolate:'enamel'});
  }
});
test('invalid control, scrub, clock and timeline inputs do not change active state',()=>{
  const {c,set}=fixture(); c.play(); set(400); c.tick();
  const state=c.snapshot(), playback=c.playback();
  for(const action of [{type:'bad'},{type:'reveal',value:NaN},{type:'isolate',label:'unknown'}])assert.throws(()=>c.dispatch(action));
  for(const value of [-1,2001,Infinity,NaN])assert.throws(()=>c.scrub(value));
  for(const frames of [[],new Array(2),[{time:1,reveal:0,isolate:null},{time:2,reveal:1,isolate:null}],
    [{time:0,reveal:0,isolate:null},{time:0,reveal:1,isolate:null}],
    [{time:0,reveal:0,isolate:null},{time:1,reveal:1,isolate:'unknown'}]])assert.throws(()=>c.setTimeline(frames));
  for(const now of [399,NaN,Infinity]){set(now);assert.throws(()=>c.tick());}
  assert.deepEqual(c.snapshot(),state); assert.deepEqual(c.playback(),playback);
});
test('timeline copies input and supports arbitrary named contracts',()=>{
  const contract={labels:['tooth-11','tooth-12'],offsets:{'tooth-11':[0,0,0],'tooth-12':[0,0,0]}};
  const {c,frames}=fixture(contract); frames[1].isolate='unknown';frames[1].time=-1;
  c.scrub(1000); assert.deepEqual(c.resolve().filter(x=>x.visible).map(x=>x.label),['tooth-11']);
  const p=c.playback();p.position=0; assert.equal(c.playback().position,1000);
});
test('timeline replacement stops playback and nonconfigured controller remains manual',()=>{
  const {c,set,frames}=fixture(); c.play();set(800);c.tick();c.setTimeline(frames);
  assert.deepEqual(c.playback(),{position:0,playing:false,duration:2000});
  const manual=C.createController(C.LABELS.map(label=>({label})));
  assert.throws(()=>manual.play());assert.throws(()=>manual.scrub(0));manual.tick();manual.pause();
  manual.dispatch({type:'reveal',value:.5});assert.equal(manual.snapshot().reveal,.5);
});
if (process.env.DENTAL_SOURCE) test('timed actual FDI31 transforms reset exactly without source mutation',()=>{
  const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
  const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
  const bytes=fs.readFileSync(process.env.DENTAL_SOURCE);
  assert.equal(sha(bytes),'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');
  const ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,DataView};
  vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8')+';this.parse=parseGLB;this.tx=transform;',ctx);
  const parts=ctx.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
  const hashes=()=>parts.flatMap(p=>p.primitives.flatMap(pr=>[sha(Buffer.from(pr.pos.buffer)),sha(Buffer.from(pr.idx.buffer))]));
  const before=hashes();let now=0;
  const c=C.createController(parts.map(p=>({label:p.name.split('/').pop()})),undefined,()=>now),baseline=c.resolve();
  c.setTimeline([{time:0,reveal:0,isolate:null},{time:1000,reveal:1,isolate:'pulp'},{time:2000,reveal:0,isolate:null}]);
  for(let i=0;i<20;i++){
    c.play();now+=375;c.tick();
    for(const p of parts)for(const pr of p.primitives)ctx.tx(pr.pos,c.resolve().find(x=>x.label===p.name.split('/').pop()).matrix);
    c.scrub(1250);c.play();now+=100;c.tick();c.dispatch({type:'reset'});now+=500;c.tick();
    assert.deepEqual(c.resolve(),baseline);
  }
  assert.deepEqual(hashes(),before);
  assert.equal(sha(bytes),'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');
});
