import {runEsophagus} from './esophagus/probe.mjs';
import * as THREE from './vendor/build/three.module.js';
import {GLTFLoader} from './vendor/examples/jsm/loaders/GLTFLoader.js';
import {samples,normalPolicy,auditGeometry,validNormals,mutateGeometry} from './lymph_diagnostics.mjs';

// Deterministic scene API checks, not native UI/click/playback controls QA.
const canvas=document.querySelector('canvas'), status=document.querySelector('#status');
const errors=[];let lost=false;
addEventListener('error',e=>errors.push(String(e.message)));
addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
canvas.addEventListener('webglcontextlost',()=>{lost=true;errors.push('WebGL context lost');});
const assert=(test,message)=>{if(!test)throw Error(message);};
const hash=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
const b64=bytes=>{let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(s);};
const post=async (path,value)=>{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});assert(r.ok,`${path}: HTTP ${r.status}`);return r.json();};
const settle=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
const frames=[],checks=[],normalDiagnostics=[];
function check(test,label){checks.push({label,passed:!!test});assert(test,label);}
const read=gl=>{const p=new Uint8Array(512*512*4);gl.readPixels(0,0,512,512,gl.RGBA,gl.UNSIGNED_BYTE,p);return p;};
const diff=(a,b,tolerance=2)=>{let changed=0,max=0;for(let i=0;i<a.length;i+=4){let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(a[i+k]-b[i+k]));max=Math.max(max,d);if(d>tolerance)changed++;}return {changedPixels:changed,maxChannelDifference:max};};

async function run(){
 const fixture=await (await fetch('fixture.json')).json();
 check(THREE.REVISION===fixture.threeRevision,'Official Three revision matches fixture');
 check(navigator.webdriver===false,'Normal Firefox, WebDriver not enabled');
 const gl=canvas.getContext('webgl2',{alpha:false,antialias:false,preserveDrawingBuffer:true});
 assert(gl,'WebGL2 unavailable; no security/graphics fallback attempted');
 const debug=gl.getExtension('WEBGL_debug_renderer_info');
 const browser={userAgent:navigator.userAgent,webdriver:navigator.webdriver,devicePixelRatio,
  version:gl.getParameter(gl.VERSION),renderer:gl.getParameter(gl.RENDERER),vendor:gl.getParameter(gl.VENDOR),
  unmaskedRenderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null,
  unmaskedVendor:debug?gl.getParameter(debug.UNMASKED_VENDOR_WEBGL):null,attributes:gl.getContextAttributes()};
 const renderer=new THREE.WebGLRenderer({canvas,context:gl,antialias:false});
 renderer.setPixelRatio(1);renderer.setSize(512,512,false);renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;
 const scene=new THREE.Scene();scene.background=new THREE.Color('#171b20');
 scene.add(new THREE.HemisphereLight(0xffffff,0x777788,2));
 const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(2,3,4);scene.add(light);
 const camera=new THREE.OrthographicCamera(-1,1,1,-1,.00001,1000);
 renderer.render(scene,camera);gl.finish();const blank=read(gl);
 const previous=new Map();

 async function load(id){
  const resource=id==='lymphCandidate'?fixture.lymphCandidate:fixture.resources.find(x=>x.id===id);assert(resource,'Missing asset fixture');
  const response=await fetch(resource.path,{redirect:'error',credentials:'omit'});assert(response.ok,'Asset HTTP failure');
  const bytes=await response.arrayBuffer();check(bytes.byteLength===resource.bytes,`${id}: exact byte count`);
  check(await hash(bytes)===resource.sha256,`${id}: exact SHA-256`);
  const view=new DataView(bytes);assert(view.getUint32(0,true)===0x46546c67&&view.getUint32(4,true)===2&&view.getUint32(8,true)===bytes.byteLength,'Invalid GLB header');
  assert(view.getUint32(16,true)===0x4e4f534a,'Missing GLB JSON');
  const doc=JSON.parse(new TextDecoder().decode(bytes.slice(20,20+view.getUint32(12,true))));
  check(doc.nodes.length===fixture[id].nodes&&doc.meshes.length===fixture[id].meshes,`${id}: expected source scene counts`);
  assert(doc.buffers.length===1&&!doc.buffers[0].uri&&!doc.images?.length&&!doc.extensionsRequired?.length,'Only reviewed embedded GLBs permitted');
  if(id==='lymph'||id==='lymphCandidate')check(doc.materials.every(m=>!m.doubleSided),`${id}: source materials single-sided`);
  const manager=new THREE.LoadingManager();manager.setURLModifier(()=>{throw Error('Unexpected external GLB resource request');});
  const model=await new GLTFLoader(manager).parseAsync(bytes,'');
  let meshCount=0,morphCount=0;
  model.scene.traverse(o=>{if(o.isMesh){meshCount++;if(o.morphTargetInfluences?.length)morphCount++;
   const p=o.geometry.attributes.position;assert(p&&p.count>0,'Empty loaded POSITION');
   for(let i=0;i<p.array.length;i++)assert(Number.isFinite(p.array[i]),'Nonfinite loaded POSITION');}});
  check(meshCount===fixture[id].renderMeshes,`${id}: expected rendered mesh count`);
  if(id==='lymph'||id==='lymphCandidate')model.scene.traverse(o=>{if(o.isMesh){
   const n=o.geometry.attributes.normal;assert(n&&n.count>0,'Missing loaded normals');
   for(const x of n.array)assert(Number.isFinite(x),'Nonfinite normal');
   const report=auditGeometry(o.geometry),materials=Array.isArray(o.material)?o.material:[o.material];
   const frontSide=materials.every(m=>m.side===THREE.FrontSide);
   normalDiagnostics.push({asset:id,assetSHA256:resource.sha256,mesh:o.name,...report,frontSide});
   check(report.nonfinite===0,`${id}/${o.name}: finite referenced normals`);
   check(frontSide,`${id}/${o.name}: loaded material culls back faces`);
   // Source defects are retained as observations, not silently repaired. The
   // compact candidate is required to have nonzero unit referenced normals.
   if(id==='lymphCandidate')check(validNormals(report),`${id}/${o.name}: nonzero unit referenced normals`);
  }});
  if(id==='heart')check(morphCount===fixture.heart.morphRenderMeshes,'heart: 232 rendered morph primitives');
  const nodes=new Map();for(let i=0;i<doc.nodes.length;i++)nodes.set(i,await model.parser.getDependency('node',i));
  const transforms=new Map();model.scene.traverse(o=>transforms.set(o,JSON.stringify([o.position.toArray(),o.quaternion.toArray(),o.scale.toArray()])));
  return {id,resource,model,doc,nodes,transforms,meshCount,morphCount};
 }
 function fit(objects,direction){
  scene.updateMatrixWorld(true);const box=new THREE.Box3();for(const o of objects)box.union(new THREE.Box3().setFromObject(o));
  assert(!box.isEmpty()&&[...box.min.toArray(),...box.max.toArray()].every(Number.isFinite),'Invalid bounds');
  const center=box.getCenter(new THREE.Vector3()),radius=box.getSize(new THREE.Vector3()).length()/2;
  assert(radius>0&&radius<100,'Unexpected asset scale');
  camera.left=camera.bottom=-radius*1.2;camera.right=camera.top=radius*1.2;
  camera.position.copy(center).add(new THREE.Vector3(...direction).normalize().multiplyScalar(radius*4));
  camera.up.set(0,1,0);camera.near=Math.max(radius/1000,.000001);camera.far=radius*20;
  camera.lookAt(center);camera.updateProjectionMatrix();
  return {min:box.min.toArray(),max:box.max.toArray(),cameraPosition:camera.position.toArray(),target:center.toArray(),orthographicSpan:radius*2.4};
 }
 function unchanged(asset){asset.model.scene.traverse(o=>assert(asset.transforms.get(o)===JSON.stringify([o.position.toArray(),o.quaternion.toArray(),o.scale.toArray()]),'Unexpected transform mutation'));}
 function visibleNodes(asset){return [...asset.nodes].filter(([i])=>'mesh' in asset.doc.nodes[i]).map(([i,o])=>({node:i,name:asset.doc.nodes[i].name,visible:o.visible}));}
 async function snapshot(id,asset,extra={},compare=null,minChanged=null,maxChanged=null){
  document.querySelector('#phase').textContent=id;status.textContent='Rendering exact source scene; deterministic API state only.';
  unchanged(asset);scene.updateMatrixWorld(true);renderer.render(scene,camera);gl.finish();
  const pixels=read(gl);assert(gl.getError()===gl.NO_ERROR&&!lost&&!gl.isContextLost(),'GL error/context lost');
  const presence=diff(pixels,blank);assert(presence.changedPixels>500,'No meaningful rendered asset pixels');
  let comparison=null;
  if(compare){assert(previous.has(compare),'Unknown comparison frame');comparison={from:compare,...diff(pixels,previous.get(compare))};
   if(minChanged!==null)check(comparison.changedPixels>=minChanged,`${id}: visible change from ${compare}`);
   if(maxChanged!==null)check(comparison.changedPixels<=maxChanged,`${id}: return/pause equivalence to ${compare}`);}
  previous.set(id,pixels);await settle();
  const rect=canvas.getBoundingClientRect();
  assert(devicePixelRatio===1&&Number.isFinite(window.mozInnerScreenX)&&Number.isFinite(window.mozInnerScreenY),'Unreviewed display-coordinate layout');
  const result={id,asset:asset.id,assetSHA256:asset.resource.sha256,pixelSHA256:await hash(pixels),
   width:512,height:512,backgroundDifference:presence,comparison,glError:gl.getError(),contextLost:lost||gl.isContextLost(),
   culling:{enabled:gl.isEnabled(gl.CULL_FACE),mode:gl.getParameter(gl.CULL_FACE_MODE),frontFace:gl.getParameter(gl.FRONT_FACE)},
   visibleNodes:visibleNodes(asset),rendererInfo:{calls:renderer.info.render.calls,triangles:renderer.info.render.triangles},
   displayRect:{x:Math.round(window.mozInnerScreenX+rect.left),y:Math.round(window.mozInnerScreenY+rect.top),width:rect.width,height:rect.height},
   ...extra,canvasPNG:canvas.toDataURL('image/png'),rgbaBase64:b64(pixels)};
  assert(result.glError===0,'Post-settle GL error');
  const receipt=await post('snapshot',result);assert(receipt.displayMatch,'Displayed canvas does not match real readPixels');
  delete result.canvasPNG;delete result.rgbaBase64;frames.push(result);
 }
 const lymph=await load('lymph');scene.add(lymph.model.scene);check(!lymph.model.animations.length,'lymph: static source has no animation');
 const lymphCamera=fit([lymph.model.scene],[1,.5,2]);
 const capsule=lymph.nodes.get(2);
 for(const layer of fixture.lymph.layers)check(lymph.doc.nodes[layer.node].name===layer.name,`lymph: exact source layer ${layer.node}`);
 await snapshot('lymph-full',lymph,{camera:lymphCamera,labelWarning:fixture.lymph.labelWarning});
 capsule.visible=false;await snapshot('lymph-capsule-hidden',lymph,{},'lymph-full',100);
 for(const layer of fixture.lymph.layers)lymph.nodes.get(layer.node).visible=true;
 await snapshot('lymph-restored',lymph,{},'lymph-full',null,0);
 // Camera and lighting stay identical across assets; reverse is the opposite view.
 const reverseCamera=fit([lymph.model.scene],[-1,-.5,-2]);
 await snapshot('lymph-source-lit-reverse',lymph,{camera:reverseCamera});
 const useCamera=spec=>{camera.position.fromArray(spec.cameraPosition);camera.lookAt(new THREE.Vector3(...spec.target));camera.updateProjectionMatrix();};
 scene.remove(lymph.model.scene);
 const candidate=await load('lymphCandidate');scene.add(candidate.model.scene);
 check(!candidate.model.animations.length,'lymph candidate: static');
 useCamera(lymphCamera);await snapshot('lymph-candidate-lit-front',candidate,{camera:lymphCamera},'lymph-full',100);
 useCamera(reverseCamera);await snapshot('lymph-candidate-lit-reverse',candidate,{camera:reverseCamera},'lymph-source-lit-reverse');
 // Diagnostic normal visualization uses the loaded normals and explicit front/back
 // sidedness. It is not the GLB material appearance or an anatomy check.
 useCamera(lymphCamera);scene.remove(candidate.model.scene);scene.add(lymph.model.scene);
 const normalFront=new THREE.MeshNormalMaterial({side:THREE.FrontSide});
 const normalBack=new THREE.MeshNormalMaterial({side:THREE.BackSide});
 scene.overrideMaterial=normalFront;
 await snapshot('lymph-source-normal-front',lymph,{camera:lymphCamera,diagnostic:'normal-front'});
 scene.overrideMaterial=normalBack;
 await snapshot('lymph-source-normal-back',lymph,{camera:lymphCamera,diagnostic:'normal-back'},'lymph-source-normal-front',100);
 scene.remove(lymph.model.scene);scene.add(candidate.model.scene);scene.overrideMaterial=normalFront;
 await snapshot('lymph-candidate-normal-front',candidate,{camera:lymphCamera,diagnostic:'normal-front'},'lymph-source-normal-front');
 scene.overrideMaterial=normalBack;
 await snapshot('lymph-candidate-normal-back',candidate,{camera:lymphCamera,diagnostic:'normal-back'},'lymph-candidate-normal-front',100);
 // Four fixed samples only. All fits use source bounds, including the candidate.
 for(const sample of samples.slice(1)) {
  const spec=fit([lymph.model.scene],sample.direction);
  for(const [label,asset] of [['source',lymph],['candidate',candidate]]) {
   scene.remove(lymph.model.scene,candidate.model.scene);scene.add(asset.model.scene);
   for(const [side,material] of [['front',normalFront],['back',normalBack]]) {
    scene.overrideMaterial=material;
    await snapshot(`lymph-${label}-orbit-${sample.id}-${side}`,asset,
     {camera:spec,diagnostic:`normal-${side}`,orbitSample:sample.id},
     side==='back'?`lymph-${label}-orbit-${sample.id}-front`:label==='candidate'?`lymph-source-orbit-${sample.id}-front`:null);
   }
  }
 }
 scene.remove(lymph.model.scene,candidate.model.scene);scene.add(candidate.model.scene);
 useCamera(lymphCamera);scene.overrideMaterial=normalFront;
 // Require real renderer sensitivity AND exact return to the pinned candidate.
 // A missing/ineffective mutation must fail the >=100 changed-pixel threshold.
 for(const kind of ['negated-normals','reversed-winding']) {
  const restores=[];
  try {
   const geometries=new Set();candidate.model.scene.traverse(o=>{if(o.isMesh)geometries.add(o.geometry);});
   for(const geometry of geometries)restores.push(mutateGeometry(geometry,kind));
   await snapshot(`lymph-control-${kind}`,candidate,
    {camera:lymphCamera,diagnostic:'normal-front',negativeControl:kind,mutatedInMemory:true},
    'lymph-candidate-normal-front',100);
  } finally {for(const restore of restores.reverse())restore();}
  await snapshot(`lymph-control-${kind}-restored`,candidate,
   {camera:lymphCamera,diagnostic:'normal-front',restoredAfter:kind},'lymph-candidate-normal-front',null,0);
 }
 scene.overrideMaterial=null;normalFront.dispose();normalBack.dispose();scene.remove(candidate.model.scene);
 const heart=await load('heart');scene.add(heart.model.scene);
 check(heart.model.animations.length===1,'heart: exactly one animation clip');
 const clip=heart.model.animations[0];check(clip.name===fixture.heart.animationName&&Math.abs(clip.duration-fixture.heart.duration)<1e-7,'heart: exact authored 0.8 s clip');
 check(clip.tracks.length===fixture.heart.morphRenderMeshes,'heart: every source morph primitive has a loaded animation track');
 const mixer=new THREE.AnimationMixer(heart.model.scene),action=mixer.clipAction(clip);action.setLoop(THREE.LoopRepeat,Infinity);action.play();
 function weights(index){
  const rows=[];let tested=0,maxError=0;
  for(const expected of fixture.heart.tracks){
   assert(heart.doc.nodes[expected.node].name===expected.name,'Unexpected morph source node');
   let count=0;
   heart.nodes.get(expected.node).traverse(o=>{if(o.isMesh&&o.morphTargetInfluences){
    assert(o.morphTargetInfluences.length===1,'Unexpected morph width');const value=o.morphTargetInfluences[0];
    const error=Math.abs(value-expected.values[index]);assert(Number.isFinite(value)&&error<1e-5,`Morph mismatch ${expected.name}: ${value} vs ${expected.values[index]}`);
    rows.push({node:expected.node,name:expected.name,primitive:o.name,value,expected:expected.values[index]});tested++;count++;maxError=Math.max(maxError,error);}});
   assert(count>0,'Missing loaded morph primitive');
  }
  assert(tested===fixture.heart.morphRenderMeshes,'Wrong morph evaluation count');return {testedMorphPrimitives:tested,maxMorphError:maxError,morphs:rows};
 }
 const heartCamera=fit([heart.model.scene],[0,0,1]);
 for(let i=0;i<fixture.heart.times.length;i++){
  const t=fixture.heart.times[i];mixer.setTime(t);
  await snapshot(`heart-full-${i}`,heart,{timeSeconds:t,actionTime:action.time,camera:heartCamera,...weights(i)},i?'heart-full-0':null,i===1||i===2?50:null,i===3?10:null);
 }
 mixer.setTime(.2);action.paused=true;mixer.update(.1);
 await snapshot('heart-paused',heart,{timeSeconds:.2,pauseUpdateSeconds:.1,...weights(1)},'heart-full-1',null,0);
 action.paused=false;mixer.setTime(clip.duration);
 await snapshot('heart-exact-loop',heart,{timeSeconds:clip.duration,actionTime:action.time,...weights(0)},'heart-full-0',null,0);
 const valves=new Set(fixture.heart.valveNodes);
 for(const [i,o] of heart.nodes)if('mesh' in heart.doc.nodes[i])o.visible=valves.has(i);
 const valveCamera=fit(fixture.heart.valveNodes.map(i=>heart.nodes.get(i)),[.18,.9,.5]);
 for(let i=0;i<fixture.heart.times.length;i++){
  const t=fixture.heart.times[i];mixer.setTime(t);
  await snapshot(`heart-valves-${i}`,heart,{timeSeconds:t,camera:valveCamera,diagnosticOnly:true,...weights(i)},i?'heart-valves-0':null,i===1||i===2?20:null,i===3?10:null);
 }
 for(const [i,o] of heart.nodes)if('mesh' in heart.doc.nodes[i])o.visible=true;
 mixer.setTime(0);fit([heart.model.scene],[0,0,1]);
 await snapshot('heart-restored',heart,{timeSeconds:0,...weights(0)},'heart-full-0',null,0);
 scene.remove(heart.model.scene);
 await runEsophagus({THREE,GLTFLoader,renderer,scene,camera,snapshot,check,fixture:fixture.esophagus});
 assert(!errors.length,'Page errors recorded');
 status.textContent=`PASS: ${frames.length} checked render states including deliberate diagnostic mutations. Software CI only; native UI, clinical, hardware QA not performed.`;
 await post('complete',{schema:1,passed:true,browser,threeRevision:THREE.REVISION,checks,frames,errors,normalDiagnostics,normalPolicy,orbitSamples:samples,
  claims:{softwareCIRender:true,deterministicMixerAndLayerState:true,nativeUIInteractionQA:false,wholeSiteQA:false,hardwarePerformanceQA:false,clinicalQA:false}});
}
run().catch(async error=>{
 status.textContent=`FAILED: ${error.stack||error}`;
 try{await post('complete',{schema:1,passed:false,error:String(error.stack||error),checks,frames,errors,normalDiagnostics,normalPolicy,orbitSamples:samples});}catch{}
});
