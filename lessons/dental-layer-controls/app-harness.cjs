/* App wiring in Node VM with DOM/canvas/RAF doubles. Not browser/runtime/accessibility QA. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const C=require('./controller.js');
const source=process.env.DENTAL_SOURCE;
if(!source)throw new Error('DENTAL_SOURCE must point to the exact hydrated FDI31 GLB.');
const bytes=fs.readFileSync(source);
assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');
async function start(options={}){
 const element=(dataset={})=>({dataset,disabled:false,value:'0',textContent:'',attrs:{},listeners:{},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,f){this.listeners[k]=f;},fire(k){this.listeners[k]({target:this});}});
 const ids=Object.fromEntries(['model','count','amount','reveal','selection','scene-status','all','reset','load-status','source-glb','play','pause','timeline','time','playback-status','authoring-script','camera-yaw','camera-pitch','camera-zoom','target-0','target-1','target-2','colour-enamel','colour-dentin','colour-pulp','colour-bone','presentation-error'].map(x=>['#'+x,element()]));
 const layers=C.LABELS.map(layer=>element({layer})),controls=[ids['#reveal'],...layers,ids['#all'],ids['#reset'],ids['#play'],ids['#pause'],ids['#timeline'],...Object.entries(ids).filter(([id])=>/^#(camera-|target-|colour-)/.test(id)).map(([,e])=>e)],queue=[];
 let now=0,pixels;
 ids['#authoring-script'].textContent=options.script?Buffer.from(options.script).toString('base64'):'';
 ids['#source-glb'].textContent=(options.corrupt?Buffer.from('bad source'):bytes).toString('base64');
 Object.assign(ids['#model'],{clientWidth:630,clientHeight:440,width:630,height:440,getContext:()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(image){pixels=Buffer.from(image.data);}})});
 const ctx={performance:{now:()=>now},TextDecoder,Uint8Array,Float32Array,Uint32Array,Uint8ClampedArray,DataView,DentalControls:C,atob:s=>Buffer.from(s,'base64').toString('binary'),crypto:options.noCrypto?{}:crypto.webcrypto,
  document:{querySelector:q=>ids[q],querySelectorAll:q=>q==='[data-layer]'?layers:controls},requestAnimationFrame:f=>queue.push(f),ResizeObserver:class {observe(){if(options.observerFails)throw Error('Observer unavailable');}},window:{}};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8'),ctx);vm.runInContext(fs.readFileSync(__dirname+'/authoring.js','utf8'),ctx);await vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8'),ctx);
 const flush=()=>{const pending=queue.splice(0);for(const callback of pending)callback();};flush();
 return {ctx,ids,layers,controls,flush,pixels:()=>pixels,advance:ms=>{now+=ms;flush();},queued:()=>queue.length,evidence:()=>JSON.parse(JSON.stringify(ctx.window.__dentalControlEvidence))};
}
module.exports={start,C};
