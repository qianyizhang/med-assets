const test=require('node:test'),assert=require('node:assert/strict');
const C=require('./controller.js');
const camera={yaw:.35,pitch:1.15,zoom:1,center:[1,2,3],extent:.1};
const A=require('./authoring.js')(C,()=>({...camera,center:[...camera.center]}));
const parts=C.LABELS.map(label=>({label}));
function setup(){let now=0;const clock=()=>now,c=A.fresh(parts,clock);c.setTimeline(A.SHOT);return {c,clock,advance:n=>now+=n,save:()=>A.serialize(c,parts,630,440)};}
test('script serializes source, native frame, labels, offsets and fixed view/material provenance',()=>{
 const h=setup(),s=JSON.parse(h.save());assert.equal(s.source.bytes,2052220);assert.deepEqual(s.labels,C.LABELS);assert.deepEqual(s.offsets,C.OFFSETS);assert.deepEqual(s.recordedView.camera,camera);assert.equal(s.presentation.materials,A.PRESENTATION.materials);
 assert.equal(A.serialize(A.load(h.save(),parts,h.clock),parts,630,440),h.save());
});
test('interrupted playback exports last sampled state, reopens paused, and can replay/reset',()=>{
 const h=setup();h.c.play();h.advance(4500);h.c.tick();h.advance(999);
 const c=A.load(h.save(),parts,h.clock);assert.deepEqual(c.snapshot(),{reveal:1,isolate:'pulp'});assert.deepEqual(c.playback(),{position:4500,playing:false,duration:8000});
 c.play();h.advance(500);c.tick();assert.equal(c.snapshot().isolate,null);c.dispatch({type:'reset'});h.advance(9999);c.tick();assert.deepEqual(c.snapshot(),{reveal:0,isolate:null});assert.equal(c.playback().position,0);
});
test('manual state and retained script cursor survive reopening independently',()=>{
 const h=setup();h.c.scrub(4500);h.c.dispatch({type:'reveal',value:.17});h.c.dispatch({type:'isolate',label:'bone'});
 const c=A.load(h.save(),parts,h.clock);assert.deepEqual(c.snapshot(),h.c.snapshot());assert.equal(c.playback().position,4500);c.play();assert.deepEqual(c.snapshot(),{reveal:1,isolate:'pulp'});
});
test('rejects foreign version/source, changed baseline, extra controls and invalid state/cursor',()=>{
 const h=setup();
 for(const mutate of [s=>s.version=3,s=>s.source.sha256='bad',s=>s.labels.reverse(),s=>s.offsets.pulp[0]=0,s=>s.presentation.colours.pulp[0]=0,s=>s.recordedView.camera.yaw=0,s=>s.recordedView.width=0,s=>s.position=9000,s=>s.state.reveal=2,s=>s.state.isolate='unknown',s=>s.state.extra=1,s=>s.timeline[0].time=1,s=>s.timeline[0].material={},s=>s.extra=true]) {
  const s=JSON.parse(h.save());mutate(s);assert.throws(()=>A.load(JSON.stringify(s),parts,h.clock));
 }
 for(const bad of ['null','{}','[]','invalid',' '.repeat(1048577)])assert.throws(()=>A.load(bad,parts,h.clock));
});
test('timeline copies and exported JSON cannot mutate live controller or fixed palette',()=>{
 const h=setup(),original=h.save(),frames=h.c.timeline();frames[0].reveal=1;frames.push({});assert.equal(h.save(),original);
 assert(Object.isFrozen(A.PRESENTATION.colours.pulp));assert(Object.isFrozen(A.SHOT[0]));
 const s=JSON.parse(original);s.timeline[1].time=1500;const c=A.load(JSON.stringify(s),parts,h.clock);s.timeline[1].time=500;assert.equal(c.timeline()[1].time,1500);
});
test('equivalent reordered JSON keys load, and invalid export view is rejected',()=>{
 const h=setup(),s=JSON.parse(h.save());s.source=Object.fromEntries(Object.entries(s.source).reverse());assert.deepEqual(A.load(JSON.stringify(s),parts,h.clock).snapshot(),h.c.snapshot());
 for(const width of [0,NaN,Infinity,20000])assert.throws(()=>A.serialize(h.c,parts,width,440));
});
test('camera and palette edits pause without sampling and reset restores independent captured baseline',()=>{
 const h=setup(),base=h.c.view();h.c.play();h.advance(2000);h.c.tick();const view=h.c.view();
 view.camera={yaw:-.8,pitch:.5,zoom:1.2,target:[.1,-.1,.05]};view.colours.enamel=[22,77,133];
 h.c.editView(view);assert.equal(h.c.playback().playing,false);assert.equal(h.c.playback().position,2000);
 view.camera.target[0]=.2;view.colours.enamel[0]=255;assert.equal(h.c.view().camera.target[0],.1);assert.equal(h.c.view().colours.enamel[0],22);
 const copy=h.c.view();copy.camera.target[0]=0;copy.colours.pulp[0]=0;assert.notDeepEqual(h.c.view(),copy);
 const other=setup();assert.deepEqual(other.c.view(),base);
 h.c.play();h.advance(2500);h.c.tick();h.c.dispatch({type:'reset'});h.advance(9000);h.c.tick();assert.deepEqual(h.c.view(),base);assert.deepEqual(h.c.snapshot(),{reveal:0,isolate:null});
});
test('invalid presentation rejects atomically including playback and deep arrays',()=>{
 const h=setup();h.c.play();h.advance(1500);h.c.tick();const before={view:h.c.view(),playback:h.c.playback(),state:h.c.snapshot()};
 for(const mutate of [v=>v.camera.yaw=NaN,v=>v.camera.pitch=Infinity,v=>v.camera.zoom=.49,v=>v.camera.target=[0,0,.251],v=>delete v.camera.target[1],v=>v.camera.extra=1,v=>v.colours.pulp=[1,2,3,4],v=>v.colours.bone[0]=.5,v=>v.colours.enamel[1]=-1,v=>v.colours.enamel[2]=256,v=>v.colours.extra=[1,2,3],v=>v.colours.pulp.alpha=0,v=>v.camera.target.extra=0]){
  const v=h.c.view();mutate(v);assert.throws(()=>h.c.editView(v));assert.deepEqual({view:h.c.view(),playback:h.c.playback(),state:h.c.snapshot()},before);
 }
});
test('v2 preserves edited view and exact recorded target, v1 migrates and unsupported versions reject',()=>{
 const h=setup(),v=h.c.view();v.camera.yaw=.8;v.camera.target=[.1,-.2,.05];v.colours.pulp=[1,2,3];h.c.editView(v);
 const saved=h.save(),s=JSON.parse(saved);assert.equal(s.version,2);assert.deepEqual(s.recordedView.camera.center,[1.01,1.98,3.005]);
 const reopened=A.load(saved,parts,h.clock);assert.equal(A.serialize(reopened,parts,630,440),saved);reopened.dispatch({type:'reset'});assert.deepEqual(reopened.view(),A.VIEW_DEFAULT);
 const legacy=JSON.parse(setup().save());legacy.version=1;delete legacy.viewState;const migrated=A.load(JSON.stringify(legacy),parts,h.clock);assert.deepEqual(migrated.view(),A.VIEW_DEFAULT);assert.equal(JSON.parse(A.serialize(migrated,parts,630,440)).version,2);
 legacy.version=0;assert.throws(()=>A.load(JSON.stringify(legacy),parts,h.clock));
});
