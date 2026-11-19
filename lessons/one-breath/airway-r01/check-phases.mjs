// Sample the staged consumer, including actual GLTFLoader morph targets.
import {readFile} from 'node:fs/promises';
import {Vector3} from '../.local/vendor/build/three.module.js';
import {loadModels} from '../asset-loader.mjs';
import {createLessonScene, applyLessonState} from '../scene.mjs';
import {initialState} from '../state.mjs';

const manifest=JSON.parse(await readFile(new URL('../assets.json',import.meta.url)));
const models=await loadModels(manifest,async item=>{
  const bytes=await readFile(new URL('../.local/'+item.file,import.meta.url));
  return bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
});
const view=createLessonScene(models,manifest);
const state={...initialState(),assets:'ready',stage:1,routeFocus:'whole'};
const lungMeshes=[];
view.lungs.traverse(o=>{if(o.isMesh)lungMeshes.push(o);});

function samplePositions(mesh){
  return Array.from({length:mesh.geometry.attributes.position.count},(_,index)=>
    mesh.getVertexPosition(index,new Vector3()));
}
function routeBounds(){
  const endpoints=[0,.25,.5,.75,1].map(f=>view.focusCourses.whole.getPointAt(f).toArray());
  const shown=[];
  view.extension.traverseVisible(o=>{if(o.isMesh)shown.push(o.name);});
  return {endpoints,shown};
}
applyLessonState(view,state);
const rest=lungMeshes.map(samplePositions),restRoute=routeBounds();
applyLessonState(view,{...state,phase:.5});
const lungPeakMm=lungMeshes.map((mesh,index)=>{
  const peak=samplePositions(mesh);
  let max=0;
  for(let i=0;i<peak.length;i++)max=Math.max(max,1000*peak[i].distanceTo(rest[index][i]));
  if(max<1)throw Error('Lung morph failed to reach a displaced peak '+mesh.name);
  return {lobe:mesh.name,vertices:peak.length,maximumDisplacementMm:max};
});
if(JSON.stringify(restRoute)!==JSON.stringify(routeBounds())||!restRoute.shown.length){
  throw Error('Phase changed static airway geometry or visibility unexpectedly');
}
applyLessonState(view,state);
for(const [index,mesh] of lungMeshes.entries()){
  if(samplePositions(mesh).some((p,i)=>!p.equals(rest[index][i])))throw Error('Rest geometry did not recover');
}
console.log(JSON.stringify({phases:[0,.5,0],activeRouteMeshes:restRoute.shown.length,lungPeakMm},null,2));
