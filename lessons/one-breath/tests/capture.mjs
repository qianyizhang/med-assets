// Offline scene export from the SAME loader, geometry and state functions used by the lesson.
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
import * as THREE from '../.local/vendor/build/three.module.js';
import {loadModels} from '../asset-loader.mjs';import {createLessonScene,applyLessonState,sceneLabels,CAMERAS} from '../scene.mjs';import {initialState,COPY,breath} from '../state.mjs';import {exchangeSVG} from '../exchange.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),out=process.argv[2];if(!out)throw Error('Output path required');await fs.mkdir(out,{recursive:false});
const manifest=JSON.parse(await fs.readFile(root+'/assets.json'));const read=async item=>{const b=await fs.readFile(root+'/.local/'+item.file);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);};
const models=await loadModels(manifest,read);const view=createLessonScene(models,manifest);
for(const [name,stage,phase] of [['mechanics-rest',0,0],['mechanics-in',0,.38],['airway',1,.3]]){
 const state={...initialState(),stage,phase,elapsed:1.7,breathClock:1.7,playing:phase>0,assets:'ready'};applyLessonState(view,state);const meshes=[];
 view.scene.traverseVisible(o=>{if(!o.isMesh)return;const vertices=[],p=new THREE.Vector3();for(let i=0;i<o.geometry.attributes.position.count;i++){o.getVertexPosition(i,p);p.applyMatrix4(o.matrixWorld);vertices.push(...p.toArray());}const indices=o.geometry.index?Array.from(o.geometry.index.array):vertices.map((_,i)=>i).filter(i=>i<vertices.length/3);const mats=(Array.isArray(o.material)?o.material:[o.material]).map(m=>({color:m.color.toArray(),opacity:m.opacity}));meshes.push({name:o.name,vertices,indices,materials:mats,groups:o.geometry.groups});});
 const config=stage===1?CAMERAS.airway:CAMERAS.mechanics;const record={name,state,camera:config,meshes,labels:sceneLabels(state,manifest),assetIdentities:manifest.assets};await fs.writeFile(out+'/'+name+'.json',JSON.stringify(record));
}
for(const lang of ['en','zh']){const state={...initialState(lang),stage:2,phase:.38,elapsed:1.7,assets:'ready'};await fs.writeFile(out+'/exchange-'+lang+'.svg',exchangeSVG(state));}
await fs.writeFile(out+'/states.json',JSON.stringify({mechanics:{phase:.38},airway:{phase:.3},exchange:{phase:.38},scope:'Actual Three.js geometry/morph/state snapshot for offline rendering; no browser screenshot or runtime pass'},null,2));console.log('Exported shared-scene snapshots',out);
