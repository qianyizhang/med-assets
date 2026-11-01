import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs/promises';
// Execute the actual canonical/patched module supplied by the Python offline suite.
// Browser, Three.js and transport contract APIs below are doubles, not WebGL.
assert.ok(process.env.CANDIDATE_LIFECYCLE_SOURCE,'Run through test_candidate_lifecycle_patch.py');
const code=await fs.readFile(process.env.CANDIDATE_LIFECYCLE_SOURCE,'utf8');
const lifecycle=await fs.readFile(new URL('../../gallery/candidate-lifecycle/r01/viewer-lifecycle.mjs',import.meta.url),'utf8');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return{promise,resolve,reject};}
async function boot({hold,throwRender=false}={}){
 const metrics={renders:0,sizes:0,controlsDisposed:0,rendererDisposed:0,observes:0,disconnects:0,revoked:[],created:[],warnings:[],rafRequested:0,controlUpdates:0};
 const handlers=new Map(),pending=new Map(),allFrames=[],nodes=new Map();let next=1;
 const target={addEventListener(type,fn,options){const a=handlers.get(type)||[];a.push({fn,once:options?.once});handlers.set(type,a)},removeEventListener(type,fn){handlers.set(type,(handlers.get(type)||[]).filter(x=>x.fn!==fn))}};
 const dispatch=(type,persisted)=>{for(const x of [...(handlers.get(type)||[])]){x.fn({persisted});if(x.once)target.removeEventListener(type,x.fn)}};
 const node=id=>{if(!nodes.has(id))nodes.set(id,{style:{},dataset:{},hidden:false,clientWidth:900,clientHeight:600});return nodes.get(id)};
 const views=['front','back','left'].map(v=>({dataset:{view:v},style:{}}));
 const document={documentElement:{},querySelector:node,querySelectorAll(s){return s==='[data-view]'?views:[]}};
 const record={id:'baseline',asset:{id:'test',name:{en:'Test'}},name:{en:'Test'},source:{encoding:'gzip',sha256:'00',revision:'test'},gates:{}};
 class V{constructor(x=0,y=0,z=0){Object.assign(this,{x,y,z})}toArray(){return[this.x,this.y,this.z]}set(x,y,z){Object.assign(this,{x,y,z});return this}copy(v){return this.set(v.x,v.y,v.z)}add(v){this.x+=v.x;this.y+=v.y;this.z+=v.z;return this}multiplyScalar(k){this.x*=k;this.y*=k;this.z*=k;return this}}
 class Scene{constructor(){this.children=[]}add(x){this.children.push(x)}}
 const model={scene:{traverse(fn){fn(this)},visible:true}};
 class Camera{constructor(){this.position=new V();this.up=new V()}updateProjectionMatrix(){}lookAt(){}}
 const THREE={Vector3:V,Scene,Color:class{},HemisphereLight:class{},DirectionalLight:class{position=new V()},PerspectiveCamera:Camera,OrthographicCamera:Camera,LoadingManager:class{setURLModifier(fn){this.modifier=fn}},Box3:class{min=new V();max=new V(1,1,1);setFromObject(){return this}isEmpty(){return false}getCenter(v){return v.set(.5,.5,.5)}getSize(v){return v.set(1,1,1)}},WebGLRenderer:class{setPixelRatio(){}setSize(){metrics.sizes++}render(){metrics.renders++;if(throwRender)throw new Error('render failed')}dispose(){metrics.rendererDisposed++}}};
 class OrbitControls{target=new V();update(){metrics.controlUpdates++}dispose(){metrics.controlsDisposed++}}
 const gate=deferred();
 const delay=async(name,value)=>{if(hold===name)await gate.promise;return value};
 class GLTFLoader{async parseAsync(){return delay('parse',model)}}
 class Observer{constructor(fn){this.fn=fn;metrics.observer=this}observe(){metrics.observes++}disconnect(){metrics.disconnects++}}
 class URLs extends URL{static createObjectURL(){const s='blob:test-'+metrics.created.length;metrics.created.push(s);return s}static revokeObjectURL(s){metrics.revoked.push(s)}}
 let fetches=0;
 const ctx=vm.createContext({window:target,document,location:{href:'https://example.invalid/review/candidate.html',search:'',origin:'https://example.invalid'},URL:URLs,URLSearchParams,Blob,devicePixelRatio:1,ResizeObserver:Observer,Uint8Array,crypto:{subtle:{digest:async()=>delay('digest',new Uint8Array([0]).buffer)}},console:{warn(...x){metrics.warnings.push(x)}},fetch:async()=>{fetches++;if(fetches===1)return delay('review',{ok:true,json:async()=>delay('reviewJson',{records:[]})});return delay('fetchModel',{ok:true,arrayBuffer:async()=>delay('body',new Uint8Array([1,2]).buffer),headers:{get:()=>null}})},requestAnimationFrame(fn){const id=next++;metrics.rafRequested++;pending.set(id,fn);allFrames.push(fn);return id},cancelAnimationFrame(id){pending.delete(id)}});
 const contract={selectRecord:()=>record,allowedModelURL:()=>new URL('https://example.invalid/model.glb'),inspectGLB:()=>{},decodeTransport:async bytes=>delay('decode',{bytes,mode:'gzip'}),cameraSpec:()=>null};
 const defs={'./source-downloads.mjs':{sourceDownloadsHTML:()=>''},'./runtime-evidence.mjs':{runtimeEvidenceHTML:()=>''},'./evidence-view.mjs':{selectEvidence:()=>[],captionHTML:()=>'',sharedEvidenceNote:()=>''},'./candidate-contract.mjs':contract,'../vendor/three.module.js':THREE,'../vendor/OrbitControls.js':{OrbitControls},'../body/3d/vendor/GLTFLoader.js':{GLTFLoader}};
 const modules=new Map();
 async function get(spec){if(modules.has(spec))return modules.get(spec);let m;if(spec==='./viewer-lifecycle.mjs')m=new vm.SourceTextModule(lifecycle,{context:ctx});else{const values=defs[spec];assert.ok(values,'Unexpected dependency '+spec);m=new vm.SyntheticModule(Object.keys(values),function(){for(const[k,v]of Object.entries(values))this.setExport(k,v)},{context:ctx})}modules.set(spec,m);await m.link(get);return m;}
 const main=new vm.SourceTextModule(code,{context:ctx,importModuleDynamically:async spec=>{await delay('imports',null);const m=await get(spec);if(m.status!=='evaluated')await m.evaluate();return m}});await main.link(get);const done=main.evaluate();await turn();await turn();
 return{metrics,pending,allFrames,nodes,views,dispatch,done,gate,handlers,frame(){const first=[...pending.entries()][0];assert.ok(first);pending.delete(first[0]);first[1]()}};
}

test('persisted hide suspends without disposing or revoking download; show resumes once',async()=>{
 const b=await boot();await b.done;assert.equal(b.pending.size,1);const old=b.allFrames[0];b.dispatch('pagehide',true);assert.equal(b.pending.size,0);assert.equal(b.metrics.rendererDisposed,0);assert.equal(b.metrics.controlsDisposed,0);assert.deepEqual(b.metrics.revoked,[]);
 b.dispatch('pagehide',true);b.dispatch('pageshow',true);assert.equal(b.pending.size,1);const renders=b.metrics.renders;old();assert.equal(b.metrics.renders,renders);assert.equal(b.pending.size,1);b.dispatch('pageshow',true);assert.equal(b.pending.size,1);b.frame();assert.equal(b.pending.size,1);assert.equal(b.metrics.renders,renders+1);
});
test('ordinary unload disposes once, revokes once and removes lifecycle listeners',async()=>{
 const b=await boot();await b.done;b.dispatch('pagehide',false);b.dispatch('pagehide',false);b.dispatch('pageshow',true);assert.equal(b.pending.size,0);assert.equal(b.metrics.controlsDisposed,1);assert.equal(b.metrics.rendererDisposed,1);assert.deepEqual(b.metrics.revoked,b.metrics.created);assert.equal(b.handlers.get('pagehide')?.length||0,0);assert.equal(b.handlers.get('pageshow')?.length||0,0);
});
test('ordinary unload after repeated cached cycles does not lose final cleanup',async()=>{
 const b=await boot();await b.done;for(let i=0;i<3;i++){b.dispatch('pagehide',true);b.dispatch('pageshow',true)}b.dispatch('pagehide',false);assert.equal(b.metrics.rendererDisposed,1);assert.deepEqual(b.metrics.revoked,b.metrics.created);assert.equal(b.pending.size,0);
});
test('late cancelled RAF, resize and UI callbacks cannot mutate disposed viewer',async()=>{
 const b=await boot();await b.done;const late=b.allFrames[0];b.dispatch('pagehide',false);const before={renders:b.metrics.renders,sizes:b.metrics.sizes,status:b.nodes.get('#viewer-status').textContent};late();b.metrics.observer.fn();b.nodes.get('#language').onclick();b.views[0].onclick();assert.equal(b.metrics.renders,before.renders);assert.equal(b.metrics.sizes,before.sizes);assert.equal(b.nodes.get('#viewer-status').textContent,before.status);assert.equal(b.pending.size,0);
});
for(const hold of ['review','reviewJson','fetchModel','body','decode','digest','imports','parse'])test('ordinary unload while awaiting '+hold+' prevents late startup',async()=>{
 const b=await boot({hold});b.dispatch('pagehide',false);const before={renders:b.metrics.renders,sizes:b.metrics.sizes,status:b.nodes.get('#viewer-status')?.textContent};b.gate.resolve();await b.done;assert.equal(b.metrics.renders,before.renders);assert.equal(b.metrics.sizes,before.sizes);assert.equal(b.nodes.get('#viewer-status')?.textContent,before.status);assert.equal(b.pending.size,0);assert.equal(b.metrics.rendererDisposed,hold==='parse'?1:0);assert.deepEqual(b.metrics.revoked,b.metrics.created);
});
test('startup finishing while cached stays suspended until persisted show',async()=>{
 const b=await boot({hold:'parse'});b.dispatch('pagehide',true);b.gate.resolve();await b.done;assert.equal(b.metrics.renders,0);assert.equal(b.pending.size,0);assert.equal(b.metrics.rendererDisposed,0);b.dispatch('pageshow',true);assert.equal(b.metrics.renders,1);assert.equal(b.pending.size,1);assert.deepEqual(b.metrics.revoked,[]);
});
test('startup error retains honest blocked fallback and releases owned resources',async()=>{
 const b=await boot({hold:'parse'});b.gate.reject(new Error('parse failed'));await b.done;assert.match(b.nodes.get('#viewer-status').textContent,/unavailable/);assert.equal(b.nodes.get('#viewport').hidden,true);assert.equal(b.metrics.rendererDisposed,1);assert.deepEqual(b.metrics.revoked,[]);assert.equal(b.pending.size,0);b.nodes.get('#language').onclick();assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);b.dispatch('pagehide',true);b.dispatch('pageshow',true);assert.equal(b.pending.size,0);b.dispatch('pagehide',false);assert.deepEqual(b.metrics.revoked,b.metrics.created);assert.equal(b.metrics.rendererDisposed,1);
});

test('render startup failure keeps fallback usable but blocks stale viewer callbacks',async()=>{
 const b=await boot({throwRender:true});await b.done;assert.match(b.nodes.get('#viewer-status').textContent,/unavailable/);assert.equal(b.metrics.rendererDisposed,1);assert.deepEqual(b.metrics.revoked,[]);const before={sizes:b.metrics.sizes,updates:b.metrics.controlUpdates};b.metrics.observer.fn();b.views[0].onclick();assert.equal(b.metrics.sizes,before.sizes);assert.equal(b.metrics.controlUpdates,before.updates);b.nodes.get('#language').onclick();assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);b.dispatch('pagehide',false);assert.deepEqual(b.metrics.revoked,b.metrics.created);assert.equal(b.metrics.rendererDisposed,1);
});
