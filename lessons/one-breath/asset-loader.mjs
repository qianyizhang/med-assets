import * as THREE from './.local/vendor/build/three.module.js';
import {GLTFLoader} from './.local/vendor/examples/jsm/loaders/GLTFLoader.js';
export const defaultRead=async item=>{const r=await fetch(`./.local/${item.file}`,{redirect:'error',credentials:'omit'});if(!r.ok)throw Error(`${item.id}: HTTP ${r.status}`);return r.arrayBuffer();};
export async function loadModels(manifest,read=defaultRead){
 const pairs=await Promise.all(manifest.assets.map(async item=>{
  const raw=await read(item);if(raw.byteLength!==item.bytes)throw Error(item.id+': asset size mismatch');
  const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),x=>x.toString(16).padStart(2,'0')).join('');if(sha!==item.sha256)throw Error(item.id+': asset identity mismatch');
  const d=new DataView(raw);if(d.getUint32(0,true)!==0x46546c67||d.getUint32(4,true)!==2||d.getUint32(8,true)!==raw.byteLength)throw Error('Invalid GLB');
  const doc=JSON.parse(new TextDecoder().decode(new Uint8Array(raw,20,d.getUint32(12,true))));
  if(doc.buffers.some(x=>x.uri)||doc.images?.some(x=>x.uri||!Number.isInteger(x.bufferView))||doc.extensionsRequired?.length)throw Error('Only embedded reviewed models are supported');
  const manager=new THREE.LoadingManager();manager.setURLModifier(()=>{throw Error('Unexpected external model resource')});
  // Intentional neutral teaching palette; source embedded textures are retained in bytes but unused.
  const loader=new GLTFLoader(manager);loader.register(parser=>({name:'NeutralTeachingMaterial',loadMaterial:index=>{const m=new THREE.MeshStandardMaterial({color:'#c7a28e',roughness:.85});m.name=parser.json.materials[index]?.name||'';return Promise.resolve(m);}}));
  return [item.id,await loader.parseAsync(raw,'')];
 }));return Object.fromEntries(pairs);
}
