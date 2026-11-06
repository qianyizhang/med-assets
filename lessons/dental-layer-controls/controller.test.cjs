const assert=require('node:assert/strict');
const test=require('node:test');
const fs=require('node:fs');
const vm=require('node:vm');
const crypto=require('node:crypto');
const C=require('./controller.js');
const parts=()=>C.LABELS.map((label,i)=>({label,matrix:C.IDENTITY.map((v,k)=>k===12?i*.01:v)}));
const create=()=>C.createController(parts());
const unchanged=(c,b)=>assert.deepEqual(c.resolve(),b);
test('initial state captures every baseline matrix',()=>{const c=create();assert.deepEqual(c.snapshot(),{reveal:0,isolate:null});assert.deepEqual(c.resolve().map(p=>p.matrix),parts().map(p=>p.matrix));});
test('repeated reveal is idempotent, never accumulates',()=>{const c=create();c.dispatch({type:'reveal',value:.64});const a=c.resolve();for(let i=0;i<100;i++)c.dispatch({type:'reveal',value:.64});unchanged(c,a);});
test('reveal round trip is exact, not merely equal offsets',()=>{const c=create(),b=c.resolve();for(const value of [1,.8,.02,.99,.44,0])c.dispatch({type:'reveal',value});unchanged(c,b);});
test('every isolate hides exactly three source labels',()=>{const c=create();for(const label of C.LABELS){c.dispatch({type:'isolate',label});assert.deepEqual(c.resolve().filter(p=>p.visible).map(p=>p.label),[label]);}});
test('isolation preserves reveal transforms and clear restores visibility',()=>{const c=create();c.dispatch({type:'reveal',value:.72});const b=c.resolve();for(const label of C.LABELS){c.dispatch({type:'isolate',label});assert.deepEqual(c.resolve().map(p=>p.matrix),b.map(p=>p.matrix));c.dispatch({type:'all'});unchanged(c,b);}});
test('reset restores baseline after each layer and arbitrary reveal',()=>{const c=create(),b=c.resolve();for(const label of C.LABELS)for(const value of [.01,.31,.77,1]){c.dispatch({type:'reveal',value});c.dispatch({type:'isolate',label});c.dispatch({type:'reset'});unchanged(c,b);}});
test('reset is idempotent',()=>{const c=create(),b=c.resolve();for(let i=0;i<100;i++)c.dispatch({type:'reset'});unchanged(c,b);});
test('show all does not reset separation',()=>{const c=create();c.dispatch({type:'reveal',value:1});c.dispatch({type:'isolate',label:'pulp'});c.dispatch({type:'all'});assert.equal(c.snapshot().reveal,1);assert.equal(c.resolve().filter(p=>p.visible).length,4);});
test('invalid reveal rejects atomically',()=>{const c=create();c.dispatch({type:'reveal',value:.3});const b=c.resolve();for(const value of [NaN,Infinity,-Infinity,-.01,1.01,'1',null]){assert.throws(()=>c.dispatch({type:'reveal',value}));unchanged(c,b);}});
test('unknown labels and actions reject atomically',()=>{const c=create(),b=c.resolve();for(const action of [{type:'isolate',label:'nerve'},{type:'isolate',label:null},{type:'other'},null]){assert.throws(()=>c.dispatch(action));unchanged(c,b);}});
test('missing duplicate and extra layers reject before controls exist',()=>{assert.throws(()=>C.createController(parts().slice(1)));assert.throws(()=>C.createController([...parts(),parts()[0]]));const p=parts();p[1].label='enamel';assert.throws(()=>C.createController(p));p[1].label='unknown';assert.throws(()=>C.createController(p));});
test('invalid baseline matrices reject',()=>{for(const m of [[1],Array(16).fill(NaN),Array(16).fill(Infinity)]){const p=parts();p[0].matrix=m;assert.throws(()=>C.createController(p));}});
test('external mutations do not change captured baseline or state',()=>{const p=parts(),c=C.createController(p),b=c.resolve();p[0].matrix[12]=99;const resolved=c.resolve();resolved[0].matrix[12]=88;const state=c.snapshot();state.reveal=1;unchanged(c,b);});
test('1000 mixed transitions always finite and bounded',()=>{const c=create();for(let i=0;i<1000;i++){c.dispatch({type:'reveal',value:(i*31%101)/100});c.dispatch({type:'isolate',label:C.LABELS[i%4]});assert(c.resolve().every(p=>p.matrix.every(Number.isFinite)));}c.dispatch({type:'reset'});unchanged(c,create().resolve());});
const sourcePath=process.env.DENTAL_SOURCE;
if(sourcePath){
 test('real GLB positions indices and bytes remain unchanged across controls',()=>{
  const bytes=fs.readFileSync(sourcePath);const sha=b=>crypto.createHash('sha256').update(b).digest('hex');const hash=sha(bytes);assert.equal(hash,'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');
  const ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,DataView};vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8')+';this.parse=parseGLB;this.tx=transform;',ctx);
  const array=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);const real=ctx.parse(array);assert.equal(real.length,4);
  const hashes=()=>real.flatMap(p=>p.primitives.flatMap(pr=>[sha(Buffer.from(pr.pos.buffer)),sha(Buffer.from(pr.idx.buffer))]));const before=hashes();const c=C.createController(real.map(p=>({label:p.name.split('/').pop(),matrix:C.IDENTITY})));
  for(let i=0;i<100;i++){c.dispatch({type:'reveal',value:(i%101)/100});c.dispatch({type:'isolate',label:C.LABELS[i%4]});for(const part of real){const state=c.resolve().find(x=>x.label===part.name.split('/').pop());for(const pr of part.primitives)ctx.tx(pr.pos,state.matrix);}}
  c.dispatch({type:'reset'});assert.deepEqual(hashes(),before);assert.equal(sha(bytes),hash);assert.equal(real.reduce((n,p)=>n+p.primitives.reduce((m,pr)=>m+pr.idx.length/3,0),0),105370);
 });
}
test('reset exactly restores captured rotated and scaled baseline matrices',()=>{
 const p=parts();p[0].matrix=[0,2,0,0,-3,0,0,0,0,0,4,0,.2,-.3,.4,1];
 const c=C.createController(p),base=c.resolve();c.dispatch({type:'reveal',value:1});c.dispatch({type:'isolate',label:'bone'});c.dispatch({type:'reset'});unchanged(c,base);
});
if(sourcePath)test('source and separation envelope fit fixed desktop and narrow viewports',()=>{
 const bytes=fs.readFileSync(sourcePath),ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,DataView};vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8')+';this.parse=parseGLB;this.fit=fixedEnvelopeCamera;',ctx);
 const real=ctx.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)).map(p=>({...p,label:p.name.split('/').pop()}));
 for(const [w,h] of [[630,440],[830,510],[300,380],[1000,380]]){
  const camera=ctx.fit(real,w,h,C.OFFSETS),saved=JSON.stringify(camera),sc=.85*Math.min(w,h)/camera.extent,cy=Math.cos(camera.yaw),sy=Math.sin(camera.yaw),cp=Math.cos(camera.pitch),sp=Math.sin(camera.pitch);
  for(const p of real)for(const pr of p.primitives)for(const reveal of [0,.25,.5,.75,1])for(let i=0;i<pr.pos.length;i+=3){
   const off=C.OFFSETS[p.label],x=pr.pos[i]+off[0]*reveal-camera.center[0],y=pr.pos[i+1]+off[1]*reveal-camera.center[1],z=pr.pos[i+2]+off[2]*reveal-camera.center[2];
   const rx=x*cy+z*sy,rz=-x*sy+z*cy,px=w/2+rx*sc,py=h/2-(y*cp-rz*sp)*sc;assert(px>=0&&px<w&&py>=0&&py<h);
  }
  assert.equal(JSON.stringify(camera),saved);
 }
});
