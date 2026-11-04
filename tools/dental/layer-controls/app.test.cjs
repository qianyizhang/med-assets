/* Actual app + real renderer with DOM/Canvas/RAF doubles, not a browser. */
const assert=require('node:assert/strict'),test=require('node:test');
const {start,C}=require('./app-harness.cjs');
test('actual app input and button handlers control source layers, preserve camera and reset',async()=>{
 const h=await start();assert(h.controls.filter(e=>e!==h.ids['#pause']).every(e=>!e.disabled));assert(h.ids['#pause'].disabled);const base=h.evidence();assert.equal(base.triangles,105370);assert.deepEqual(base.visible,C.LABELS);
 h.ids['#reveal'].value='63';h.ids['#reveal'].fire('input');h.flush();assert.equal(h.evidence().reveal,.63);assert.equal(h.ids['#amount'].textContent,'63%');
 for(const button of h.layers){button.fire('click');h.flush();assert.deepEqual(h.evidence().visible,[button.dataset.layer]);assert.equal(button.attrs['aria-pressed'],'true');assert.deepEqual(h.evidence().camera,base.camera);}
 h.ids['#all'].fire('click');h.flush();assert.equal(h.evidence().reveal,.63);assert.deepEqual(h.evidence().visible,C.LABELS);
 h.ids['#reset'].fire('click');h.flush();assert.deepEqual(h.evidence(),base);assert.equal(h.ids['#reveal'].value,'0');assert(h.layers.every(e=>e.attrs['aria-pressed']==='false'));
});
test('source hash mismatch fails closed before parsing or rendering',async()=>{const h=await start({corrupt:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/does not match/);assert.equal(h.ctx.window.__dentalControlEvidence,undefined);});
test('missing Web Crypto fails closed',async()=>{const h=await start({noCrypto:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/Web Crypto/);});
test('initialization failure after enabling controls disables them again',async()=>{const h=await start({observerFails:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/Observer unavailable/);});
test('queued source render interrupted by reset cannot restore stale isolated state',async()=>{
 const h=await start(),base=h.evidence();
 for(let i=0;i<12;i++){
  h.ids['#reveal'].value=String(i*7);h.ids['#reveal'].fire('input');h.layers[i%4].fire('click');
  // Interrupt before the already queued RAF runs. It must read current reset state.
  h.ids['#reset'].fire('click');h.ids['#reset'].fire('click');h.flush();assert.deepEqual(h.evidence(),base);
 }
});

test('play, pause, resume, end and replay use absolute fake-clock timeline positions',async()=>{
 const h=await start();h.ids['#play'].fire('click');h.flush();
 assert.equal(h.evidence().playback.playing,true);assert(h.ids['#play'].disabled);assert(!h.ids['#pause'].disabled);
 h.advance(2000);assert.equal(h.evidence().reveal,.5);assert.equal(h.ids['#time'].textContent,'2.00 s / 8.00 s');
 h.ids['#pause'].fire('click');h.flush();const paused=h.evidence();h.advance(5000);assert.deepEqual(h.evidence(),paused);assert.equal(h.queued(),0);
 h.ids['#play'].fire('click');h.advance(2000);assert.deepEqual(h.evidence().visible,['pulp']);
 h.advance(9000);assert.equal(h.evidence().playback.position,8000);assert.equal(h.evidence().playback.playing,false);assert.equal(h.evidence().reveal,0);assert.equal(h.queued(),0);
 assert.equal(h.ids['#playback-status'].textContent,'Sequence finished');h.ids['#play'].fire('click');h.flush();assert.equal(h.evidence().playback.position,0);
});
test('absolute scrub pauses and repeated seeks do not accumulate transforms',async()=>{
 const h=await start();h.ids['#play'].fire('click');h.advance(2300);
 for(const value of [4500,2000,4500,0,8000,2000]){
  h.ids['#timeline'].value=String(value);h.ids['#timeline'].fire('input');h.flush();
  assert.equal(h.evidence().playback.position,value);assert.equal(h.evidence().playback.playing,false);assert.equal(h.ids['#timeline'].value,String(value));
  assert.equal(h.queued(),0);
 }
 assert.equal(h.evidence().reveal,.5);assert.deepEqual(h.evidence().visible,C.LABELS);
 assert.equal(h.ids['#timeline'].attrs['aria-valuetext'],'2.00 s of 8.00 s');
});
test('manual reveal, isolate and all interrupt playback; explicit play reapplies script',async()=>{
 const h=await start();
 for(const action of [()=>{h.ids['#reveal'].value='77';h.ids['#reveal'].fire('input');},()=>h.layers[0].fire('click'),()=>h.ids['#all'].fire('click')]){
  h.ids['#timeline'].value='4500';h.ids['#timeline'].fire('input');h.ids['#play'].fire('click');h.flush();
  action();h.flush();assert.equal(h.evidence().playback.playing,false);const manual=h.evidence();h.advance(1000);assert.deepEqual(h.evidence(),manual);
  h.ids['#play'].fire('click');h.flush();assert.deepEqual(h.evidence().visible,['pulp']);assert.equal(h.evidence().reveal,1);
 }
});
test('queued timed callbacks cannot revive playback or stale state after repeated reset',async()=>{
 const h=await start(),base=h.evidence();
 for(let i=0;i<8;i++){
  h.ids['#play'].fire('click');h.advance(4500);assert.equal(h.queued(),1);
  h.ids['#reset'].fire('click');h.ids['#reset'].fire('click');h.advance(10000);
  assert.deepEqual(h.evidence(),base);assert.equal(h.queued(),0);assert.equal(h.ids['#timeline'].value,'0');
 }
});

test('save interrupted manual state, reopen embedded JSON and replay with identical CPU pixels',async()=>{
 const h=await start(),baseline=h.pixels(),initial=h.evidence();
 h.ids['#play'].fire('click');h.advance(4500);
 h.ids['#reveal'].value='37';h.ids['#reveal'].fire('input');h.flush();
 const saved=h.ctx.window.dentalAuthoring.save(),state=JSON.parse(saved);
 assert.equal(state.position,4500);assert.deepEqual(state.state,{reveal:.37,isolate:'pulp'});
 assert.deepEqual(state.recordedView.camera,initial.camera);
 assert.deepEqual(state.presentation,initial.presentation);
 const reopened=await start({script:saved});
 assert.deepEqual(reopened.evidence(),h.evidence());assert.deepEqual(reopened.pixels(),h.pixels());
 reopened.ids['#play'].fire('click');reopened.advance(500);assert.equal(reopened.evidence().reveal,1);assert.equal(reopened.evidence().isolate,null);
 reopened.ids['#reset'].fire('click');reopened.advance(10000);
 assert.deepEqual(reopened.evidence(),initial);assert.deepEqual(reopened.pixels(),baseline);
});
test('live load is atomic, pauses queued playback, and validates fixed camera/material/source bindings',async()=>{
 const h=await start(),initial=h.evidence(),saved=h.ctx.window.dentalAuthoring.save();
 h.ids['#play'].fire('click');h.advance(4500);const before=h.evidence();
 for(const mutate of [s=>s.source.sha256='0'.repeat(64),s=>s.recordedView.camera.center[0]+=.01,s=>s.viewState.colours.pulp[0]=256,s=>s.position=-1,s=>s.timeline[1].camera={}]) {
  const invalid=JSON.parse(saved);mutate(invalid);
  assert.throws(()=>h.ctx.window.dentalAuthoring.load(JSON.stringify(invalid)));
  assert.deepEqual(h.evidence(),before);
 }
 h.ctx.window.dentalAuthoring.load(saved);h.advance(10000);
 assert.deepEqual(h.evidence(),initial);assert.equal(h.queued(),0);
});
test('invalid embedded script fails closed, and fresh source reimport uses edited timing',async()=>{
 const h=await start(),saved=JSON.parse(h.ctx.window.dentalAuthoring.save());
 saved.timeline=[{time:0,reveal:0,isolate:null},{time:1000,reveal:1,isolate:'enamel'},{time:2500,reveal:0,isolate:null}];
 const reopened=await start({script:JSON.stringify(saved)});
 assert.equal(reopened.evidence().playback.duration,2500);
 reopened.ids['#play'].fire('click');reopened.advance(1000);
 assert.equal(reopened.evidence().isolate,'enamel');assert.equal(reopened.evidence().reveal,1);
 const bad=await start({script:'{}'});assert(bad.controls.every(e=>e.disabled));assert.equal(bad.ctx.window.dentalAuthoring,undefined);
 assert.equal(bad.ctx.window.__dentalControlEvidence,undefined);
});
test('actual camera and palette inputs alter CPU pixels; interrupted reset restores exact source view',async()=>{
 const h=await start(),base=h.evidence(),pixels=h.pixels();
 for(let i=0;i<3;i++){
  h.ids['#play'].fire('click');h.advance(2000);
  for(const [id,value] of [['camera-yaw','.7'],['camera-pitch','1'],['camera-zoom','.9'],['target-0','.05'],['target-1','-.03'],['target-2','.02'],['colour-enamel','#1479b6'],['colour-bone','#4455aa']]){h.ids['#'+id].value=value;h.ids['#'+id].fire(id.startsWith('colour-')?'input':'change');}
  h.flush();assert.equal(h.evidence().playback.playing,false);assert.notDeepEqual(h.pixels(),pixels);assert.equal(h.evidence().camera.yaw,.7);assert.deepEqual(h.evidence().viewState.colours.enamel,[20,121,182]);
  h.ids['#play'].fire('click');h.ids['#reset'].fire('click');h.advance(9000);assert.deepEqual(h.evidence(),base);assert.deepEqual(h.pixels(),pixels);assert.equal(h.queued(),0);
 }
});
test('edited presentation saves/reimports with exact pixels, atomic invalid load, and independent controls',async()=>{
 const h=await start();h.ids['#camera-yaw'].value='.9';h.ids['#camera-yaw'].fire('change');h.ids['#colour-enamel'].value='#bb3355';h.ids['#colour-enamel'].fire('input');h.flush();
 const saved=h.ctx.window.dentalAuthoring.save(),reopened=await start({script:saved});assert.deepEqual(reopened.evidence(),h.evidence());assert.deepEqual(reopened.pixels(),h.pixels());
 const invalid=JSON.parse(saved);invalid.viewState.camera.zoom=99;assert.throws(()=>h.ctx.window.dentalAuthoring.load(JSON.stringify(invalid)));assert.equal(h.ctx.window.dentalAuthoring.save(),saved);
 reopened.ids['#reset'].fire('click');reopened.flush();assert.notDeepEqual(reopened.evidence().viewState,h.evidence().viewState);
});
test('invalid live input rejects camera and colour edits without pausing or partial changes',async()=>{
 const h=await start();h.ids['#play'].fire('click');h.advance(2000);const before=h.evidence();
 for(const [id,value] of [['camera-yaw',''],['camera-zoom','10'],['target-1','NaN'],['colour-pulp','#oops']]){
  h.ids['#'+id].value=value;h.ids['#'+id].fire(id.startsWith('colour-')?'input':'change');assert.deepEqual(h.evidence(),before);assert(h.ids['#presentation-error'].textContent);
 }
 h.ids['#camera-zoom'].value='.9';h.ids['#camera-zoom'].fire('change');h.flush();assert.equal(h.ids['#presentation-error'].textContent,'');assert.equal(h.evidence().playback.playing,false);
});
test('focused number drafts survive playback renders until committed change',async()=>{
 const h=await start(),input=h.ids['#camera-yaw'];h.ctx.document.activeElement=input;
 h.ids['#play'].fire('click');input.value='';h.advance(1200);assert.equal(input.value,'');assert.equal(h.evidence().camera.yaw,.35);
 input.value='-.7';input.fire('change');h.flush();assert.equal(h.evidence().camera.yaw,-.7);assert.equal(h.evidence().playback.playing,false);
 h.ctx.document.activeElement=null;h.ids['#reset'].fire('click');h.flush();assert.equal(input.value,'.35'.replace(/^\./,'0.'));
});
