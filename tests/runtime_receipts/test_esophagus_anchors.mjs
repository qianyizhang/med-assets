// Genuine GLTFLoader + Raycaster regression. No DOM, GL, browser or synthetic mesh.
// Inputs are supplied by run_esophagus_anchor_regression.py; missing input fails.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {resolveAnchors,setEsophagusView} from '../../ci/esophagus/probe.mjs';
const root=process.env.ESOPHAGUS_VENDOR_ROOT;
assert.ok(root,'Exact Three fixture root required');
const THREE=await import(pathToFileURL(resolve(root,'build/three.module.js')));
const {GLTFLoader}=await import(pathToFileURL(resolve(root,'examples/jsm/loaders/GLTFLoader.js')));
assert.equal(THREE.REVISION,'180');
const fixture=JSON.parse(readFileSync(new URL('../../ci/esophagus/fixture.json',import.meta.url)));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
async function load(variant){
  const path=process.env['ESOPHAGUS_'+variant.toUpperCase()];assert.ok(path,'Pinned GLB path required');
  const bytes=readFileSync(path);assert.equal(bytes.length,fixture[variant].bytes);assert.equal(hash(bytes),fixture[variant].sha256);
  const manager=new THREE.LoadingManager();manager.setURLModifier(()=>{throw Error('Unexpected external GLB dependency');});
  const model=await new GLTFLoader(manager).parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.length),'');
  const nodes=new Map();for(const l of fixture.layers)nodes.set(l.node,await model.parser.getDependency('node',l.node));
  const scene=new THREE.Scene();scene.add(model.scene);
  const camera=new THREE.OrthographicCamera(-1,1,1,-1,.00001,1000);
  setEsophagusView(THREE,camera,false);scene.updateMatrixWorld(true);
  setEsophagusView(THREE,camera,true);scene.updateMatrixWorld(true);
  // Exact preceding five isolated-layer states, restored before the failed step.
  for(const layer of fixture.layers){for(const [i,node] of nodes)node.visible=i===layer.node;scene.updateMatrixWorld(true);}
  for(const node of nodes.values())node.visible=true;
  scene.remove(model.scene);scene.add(model.scene);setEsophagusView(THREE,camera,true);scene.updateMatrixWorld(true);
  return {model,nodes,scene,camera};
}
function geometryHashes(nodes){
  return [...nodes.values()].map(o=>[o.geometry.index,...Object.values(o.geometry.attributes)].map(a=>hash(Buffer.from(a.array.buffer,a.array.byteOffset,a.array.byteLength))));
}
for(const variant of ['baseline','candidate']){
  test(`${variant}: reproduce original anchor 3 miss with exact loaded geometry`,async()=>{
    const {nodes,camera}=await load(variant),results=[];
    for(const l of fixture.layers){
      const ndc=new THREE.Vector3(...l.anchor).project(camera),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(ndc.x,ndc.y),camera);
      const hits=ray.intersectObjects([...nodes.values()],true);
      results.push(!!hits[0]&&hits[0].object===nodes.get(l.node));
      if(l.number===3){assert.equal(hits.length,0);assert.equal(nodes.get(l.node).visible,true);assert.equal(nodes.get(l.node).material.side,THREE.DoubleSide);}
    }
    assert.deepEqual(results,[true,true,false,true,true]);
  });
  test(`${variant}: actual displayed pixel rays hit all five original compartments`,async()=>{
    const {nodes,camera}=await load(variant),before=geometryHashes(nodes);
    const anchors=resolveAnchors(THREE,nodes,camera,fixture.layers);
    assert.deepEqual(anchors.map(a=>a.pixel),[[193,220],[198,156],[256,116],[337,116],[411,167]]);
    for(const a of anchors){
      assert.equal(a.raycast.actual.uuid,nodes.get(a.hitNode).uuid);
      assert.equal(a.raycast.actual.visible,true);assert.equal(a.raycast.actual.materialSide,THREE.DoubleSide);
      assert.ok(Math.abs(a.raycast.actual.distance-.27749999821186067)<1e-12);
    }
    assert.deepEqual(geometryHashes(nodes),before,'No geometry mutation');
    assert.ok([...nodes.values()].every(o=>o.visible));
  });
}
test('wrong compartment still fails and retains actual hit/expected identity/coordinates',async()=>{
  const {nodes,camera}=await load('candidate');
  const wrong={...fixture.layers[2],anchor:fixture.layers[0].anchor};
  assert.throws(()=>resolveAnchors(THREE,nodes,camera,[wrong]),error=>{
    assert.match(error.message,/Numbered anchor misses its loaded compartment/);
    const details=JSON.parse(error.message.slice(error.message.indexOf('{')));
    assert.equal(details.anchorId,3);assert.equal(details.expected.uuid,nodes.get(2).uuid);
    assert.equal(details.actual.uuid,nodes.get(0).uuid);assert.ok(details.actual.distance>0);
    for(const key of ['anchorWorld','projectedNDC','pixel','pixelCenterNDC','rayOrigin','rayDirection','cameraPosition'])assert.ok(Array.isArray(details[key]),key);
    return true;
  });
});
test('hidden expected compartment is rejected despite Raycaster including invisible objects',async()=>{
  const {nodes,camera}=await load('candidate');nodes.get(2).visible=false;
  assert.throws(()=>resolveAnchors(THREE,nodes,camera,[fixture.layers[2]]),/"visible":false/);
});
