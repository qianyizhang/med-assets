/* App wiring in Node VM with DOM/canvas/RAF doubles. Not browser/runtime/accessibility QA. */
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const C=require('./controller.js');
const source=process.env.DENTAL_SOURCE;
if(!source)throw new Error('DENTAL_SOURCE must point to the exact hydrated FDI31 GLB.');
const bytes=fs.readFileSync(source);
assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');
async function start(options={}){
 const element=(dataset={})=>({dataset,disabled:false,value:'0',textContent:'',attrs:{},listeners:{},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,f){this.listeners[k]=f;},fire(k){this.listeners[k]({target:this});}});
 const ids=Object.fromEntries(['model','count','amount','reveal','selection','scene-status','all','reset','load-status','source-glb'].map(x=>['#'+x,element()]));
 const layers=C.LABELS.map(layer=>element({layer})),controls=[ids['#reveal'],...layers,ids['#all'],ids['#reset']],queue=[];
 ids['#source-glb'].textContent=(options.corrupt?Buffer.from('bad source'):bytes).toString('base64');
 Object.assign(ids['#model'],{clientWidth:630,clientHeight:440,width:630,height:440,getContext:()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(){}})});
 const ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,Uint8ClampedArray,DataView,DentalControls:C,atob:s=>Buffer.from(s,'base64').toString('binary'),crypto:options.noCrypto?{}:crypto.webcrypto,
  document:{querySelector:q=>ids[q],querySelectorAll:q=>q==='[data-layer]'?layers:controls},requestAnimationFrame:f=>queue.push(f),ResizeObserver:class {observe(){if(options.observerFails)throw Error('Observer unavailable');}},window:{}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8'),ctx);await vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8'),ctx);
 const flush=()=>{while(queue.length)queue.shift()();};flush();
 return {ctx,ids,layers,controls,flush,evidence:()=>JSON.parse(JSON.stringify(ctx.window.__dentalControlEvidence))};
}
test('actual app input and button handlers control source layers, preserve camera and reset',async()=>{
 const h=await start();assert(h.controls.every(e=>!e.disabled));const base=h.evidence();assert.equal(base.triangles,105370);assert.deepEqual(base.visible,C.LABELS);
 h.ids['#reveal'].value='63';h.ids['#reveal'].fire('input');h.flush();assert.equal(h.evidence().reveal,.63);assert.equal(h.ids['#amount'].textContent,'63%');
 for(const button of h.layers){button.fire('click');h.flush();assert.deepEqual(h.evidence().visible,[button.dataset.layer]);assert.equal(button.attrs['aria-pressed'],'true');assert.deepEqual(h.evidence().camera,base.camera);}
 h.ids['#all'].fire('click');h.flush();assert.equal(h.evidence().reveal,.63);assert.deepEqual(h.evidence().visible,C.LABELS);
 h.ids['#reset'].fire('click');h.flush();assert.deepEqual(h.evidence(),base);assert.equal(h.ids['#reveal'].value,'0');assert(h.layers.every(e=>e.attrs['aria-pressed']==='false'));
});
test('source hash mismatch fails closed before parsing or rendering',async()=>{const h=await start({corrupt:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/does not match/);assert.equal(h.ctx.window.__dentalControlEvidence,undefined);});
test('missing Web Crypto fails closed',async()=>{const h=await start({noCrypto:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/Web Crypto/);});
test('initialization failure after enabling controls disables them again',async()=>{const h=await start({observerFails:true});assert(h.controls.every(e=>e.disabled));assert.match(h.ids['#load-status'].textContent,/Observer unavailable/);});
