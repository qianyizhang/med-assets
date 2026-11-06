import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs/promises';
// Execute the bound current viewer staged by tests/viewer/run.py.
// Browser, Three.js and transport contract APIs below are doubles, not WebGL.
const sourceURL=new URL('../public/review/',import.meta.url);
const code=await fs.readFile(new URL('candidate.js',sourceURL),'utf8');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return{promise,resolve,reject};}
export async function boot({hold,throwRender=false,lossDuringRender=false,staticEvidence=false}={}){
 const metrics={renders:0,sizes:0,controlsDisposed:0,rendererDisposed:0,observes:0,disconnects:0,revoked:[],created:[],warnings:[],rafRequested:0,controlUpdates:0,reloads:0};
 const handlers=new Map(),pending=new Map(),allFrames=[],nodes=new Map();let next=1;
 const target={addEventListener(type,fn,options){const a=handlers.get(type)||[];a.push({fn,once:options?.once});handlers.set(type,a)},removeEventListener(type,fn){handlers.set(type,(handlers.get(type)||[]).filter(x=>x.fn!==fn))}};
 const dispatch=(type,persisted)=>{for(const x of [...(handlers.get(type)||[])]){x.fn({persisted});if(x.once)target.removeEventListener(type,x.fn)}};
 const newNode=(connected=false)=>({style:{},dataset:{},hidden:false,clientWidth:900,clientHeight:600,isConnected:connected,childNodes:[],listeners:new Map(),ownerDocument:null,
  addEventListener(type,fn){const list=this.listeners.get(type)||new Set();list.add(fn);this.listeners.set(type,list)},
  removeEventListener(type,fn){this.listeners.get(type)?.delete(fn)},
  emit(type){for(const fn of [...(this.listeners.get(type)||[])])fn({type,preventDefault(){}});this.onclick?.()},
  get textContent(){return this.childNodes.length?this.childNodes.map(x=>x.textContent).join(''):this.text||''},
  set textContent(value){this.text=value;for(const x of this.childNodes)x.isConnected=false;this.childNodes=[]},
  replaceChildren(...children){for(const x of this.childNodes)x.isConnected=false;this.childNodes=children;this.text='';for(const x of children)x.isConnected=this.isConnected},
 });
 const node=id=>{if(id==='#knee-inspection')return null;if(!nodes.has(id)){const x=newNode(true);x.ownerDocument=document;nodes.set(id,x)}return nodes.get(id)};
 const views=['front','back','left'].map(v=>({dataset:{view:v},style:{}}));
 const document={documentElement:{},querySelector:node,querySelectorAll(s){return s==='[data-view]'?views:[]},createElement(){const x=newNode();x.ownerDocument=document;return x},createTextNode(text){const x=newNode();x.textContent=text;x.ownerDocument=document;return x}};
 const record={id:'baseline',asset:{id:'test',name:{en:'Test'}},name:{en:'Test'},source:{encoding:'gzip',sha256:'00',revision:'test'},gates:{}};
 class V{constructor(x=0,y=0,z=0){Object.assign(this,{x,y,z})}toArray(){return[this.x,this.y,this.z]}set(x,y,z){Object.assign(this,{x,y,z});return this}copy(v){return this.set(v.x,v.y,v.z)}add(v){this.x+=v.x;this.y+=v.y;this.z+=v.z;return this}multiplyScalar(k){this.x*=k;this.y*=k;this.z*=k;return this}}
 class Scene{constructor(){this.children=[]}add(x){this.children.push(x)}}
 const model={scene:{traverse(fn){fn(this)},visible:true}};
 class Camera{constructor(){this.position=new V();this.up=new V()}updateProjectionMatrix(){}lookAt(){}}
 const THREE={Vector3:V,Scene,Color:class{},HemisphereLight:class{},DirectionalLight:class{position=new V()},PerspectiveCamera:Camera,OrthographicCamera:Camera,LoadingManager:class{setURLModifier(fn){this.modifier=fn}},Box3:class{min=new V();max=new V(1,1,1);setFromObject(){return this}isEmpty(){return false}getCenter(v){return v.set(.5,.5,.5)}getSize(v){return v.set(1,1,1)}},WebGLRenderer:class{setPixelRatio(){}setSize(){metrics.sizes++}render(){metrics.renders++;if(lossDuringRender && metrics.renders===1)node('#canvas').emit('webglcontextlost');if(throwRender)throw new Error('render failed')}dispose(){metrics.rendererDisposed++}}};
 class OrbitControls{target=new V();update(){metrics.controlUpdates++}dispose(){metrics.controlsDisposed++}}
 const gate=deferred();
 const delay=async(name,value)=>{if(hold===name)await gate.promise;return value};
 class GLTFLoader{async parseAsync(){return delay('parse',model)}}
 class Observer{constructor(fn){this.fn=fn;metrics.observer=this}observe(){metrics.observes++}disconnect(){metrics.disconnects++}}
 class URLs extends URL{static createObjectURL(){const s='blob:test-'+metrics.created.length;metrics.created.push(s);return s}static revokeObjectURL(s){metrics.revoked.push(s)}}
 let fetches=0;
 const ctx=vm.createContext({window:target,document,location:{href:'https://example.invalid/review/candidate.html',search:'',origin:'https://example.invalid',reload(){metrics.reloads++}},URL:URLs,URLSearchParams,Blob,devicePixelRatio:1,ResizeObserver:Observer,AbortController,Uint8Array,crypto:{subtle:{digest:async()=>delay('digest',new Uint8Array([0]).buffer)}},console:{warn(...x){metrics.warnings.push(x)}},fetch:async url=>{fetches++;if(String(url)==='media/models.json')return delay('manifest',{ok:true,arrayBuffer:async()=>delay('manifestBody',new ArrayBuffer(0))});if(fetches===1)return delay('review',{ok:true,json:async()=>delay('reviewJson',{records:[]})});return delay('fetchModel',{ok:true,arrayBuffer:async()=>delay('body',new Uint8Array([1,2]).buffer),headers:{get:()=>null}})},requestAnimationFrame(fn){const id=next++;metrics.rafRequested++;pending.set(id,fn);allFrames.push(fn);return id},cancelAnimationFrame(id){pending.delete(id)}});
 const contract={selectRecord:()=>record,allowedModelURL:()=>new URL('https://example.invalid/model.glb'),inspectGLB:()=>{},decodeTransport:async bytes=>delay('decode',{bytes,mode:'gzip'}),cameraSpec:()=>null};
 const defs={'./source-downloads.mjs':{sourceDownloadsHTML:()=>''},'./runtime-evidence.mjs':{runtimeEvidenceHTML:()=>''},'./evidence-view.mjs':{selectEvidence:()=>staticEvidence?[{file:'retained-static.png'}]:[],captionHTML:()=>'',sharedEvidenceNote:()=>''},'./candidate-contract.mjs':contract,'./model-media.mjs':{parseModelManifest:()=>({}),resolveModelTransport:()=>({url:'https://example.invalid/model.glb',entry:{bytes:2}}),verifyModelTransport:async()=>delay('verifyTransport',{transportBytesVerified:true})},'../vendor/three.module.js':THREE,'../vendor/OrbitControls.js':{OrbitControls},'../body/3d/vendor/GLTFLoader.js':{GLTFLoader}};
 const modules=new Map();
 async function get(spec){
  if(modules.has(spec))return modules.get(spec);
  let m;
  if(['./viewer-lifecycle.mjs','./context-loss.mjs','./camera-reset.mjs','./knee-inspection.mjs'].includes(spec))m=new vm.SourceTextModule(await fs.readFile(new URL(spec,sourceURL),'utf8'),{context:ctx});
  else{
   const values=defs[spec];assert.ok(values,'Unexpected dependency '+spec);
   m=new vm.SyntheticModule(Object.keys(values),function(){for(const[k,v]of Object.entries(values))this.setExport(k,v)},{context:ctx});
  }
  modules.set(spec,m);await m.link(get);return m;
 }
 const main=new vm.SourceTextModule(code,{context:ctx,importModuleDynamically:async spec=>{await delay('imports',null);const m=await get(spec);if(m.status!=='evaluated')await m.evaluate();return m}});await main.link(get);const done=main.evaluate();await turn();await turn();
 return{metrics,pending,allFrames,nodes,views,dispatch,done,gate,handlers,element:node,frame(){const first=[...pending.entries()][0];assert.ok(first);pending.delete(first[0]);first[1]()}};
}
