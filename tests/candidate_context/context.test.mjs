import test from 'node:test';
import assert from 'node:assert/strict';
import {boot} from '../candidate_lifecycle/module-harness.mjs';

function lose(b){b.nodes.get('#canvas').emit('webglcontextlost');}
function unavailable(b){
  assert.match(b.nodes.get('#viewer-status').textContent,/unavailable|交互视图不可用/);
  assert.equal(b.nodes.get('#viewport').hidden,true);
  assert.equal(b.nodes.get('#controls').hidden,true);
  assert.match(b.nodes.get('#error').textContent,/Reload|重新加载/);
  assert.equal(b.pending.size,0);
}
function usableEvidence(b){
  assert.equal(b.nodes.get('#source-file').hidden,false);
  assert.equal(b.nodes.get('#source-file').href,b.metrics.created[0]);
  assert.deepEqual(b.metrics.revoked,[]);
  assert.match(b.nodes.get('#fallback').innerHTML,/retained-static.png/);
}

test('loaded context loss leaves ready, stops camera/render work and retains evidence',async()=>{
  const b=await boot({staticEvidence:true});await b.done;
  lose(b);unavailable(b);usableEvidence(b);
  const before={...b.metrics};for(const view of b.views)view.onclick();for(const fn of b.allFrames)fn();b.metrics.observer.fn();
  assert.equal(b.metrics.renders,before.renders);assert.equal(b.metrics.sizes,before.sizes);assert.equal(b.metrics.controlUpdates,before.controlUpdates);
  assert.equal(b.metrics.rendererDisposed,1);assert.equal(b.metrics.controlsDisposed,1);
});
test('locale changes after loss keep bilingual unavailable/reload and valid downloads',async()=>{
  const b=await boot({staticEvidence:true});await b.done;lose(b);b.nodes.get('#language').onclick();
  assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);assert.match(b.nodes.get('#error').textContent,/重新加载/);usableEvidence(b);
  b.nodes.get('#language').onclick();assert.match(b.nodes.get('#error').textContent,/Reload/);unavailable(b);
});
test('loss while Chinese is selected is reported immediately in Chinese',async()=>{
  const b=await boot();await b.done;b.nodes.get('#language').onclick();lose(b);
  assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);assert.match(b.nodes.get('#error').textContent,/重新加载/);
});
test('cached return and restoration events cannot revive an unavailable view',async()=>{
  const b=await boot({staticEvidence:true});await b.done;lose(b);const renders=b.metrics.renders;
  for(let i=0;i<3;i++){b.dispatch('pagehide',true);b.nodes.get('#canvas').emit('webglcontextrestored');b.dispatch('pageshow',true);}
  unavailable(b);usableEvidence(b);assert.equal(b.metrics.renders,renders);assert.equal(b.metrics.rendererDisposed,1);
});
test('context loss while cached is not revived on persisted return',async()=>{
  const b=await boot();await b.done;b.dispatch('pagehide',true);lose(b);b.dispatch('pageshow',true);unavailable(b);
});
test('late parse success after loading context loss cannot initialize or paint ready',async()=>{
  const b=await boot({hold:'parse',staticEvidence:true});lose(b);const updates=b.metrics.controlUpdates;b.gate.resolve();await b.done;
  unavailable(b);usableEvidence(b);assert.equal(b.metrics.renders,0);assert.equal(b.metrics.controlUpdates,updates);assert.equal(b.metrics.rendererDisposed,1);
});
test('late parse failure after loss cannot overwrite the recovery message',async()=>{
  const b=await boot({hold:'parse',staticEvidence:true});lose(b);const message=b.nodes.get('#error').textContent;b.gate.reject(new Error('late parse failure'));await b.done;
  unavailable(b);usableEvidence(b);assert.equal(b.nodes.get('#error').textContent,message);assert.equal(b.metrics.warnings.length,0);
});
test('context loss inside first frame cannot be overwritten by final ready completion',async()=>{
  const b=await boot({lossDuringRender:true,staticEvidence:true});await b.done;unavailable(b);usableEvidence(b);assert.equal(b.metrics.rendererDisposed,1);
});
test('normal failed startup stays blocked and does not acquire a context-loss recovery state',async()=>{
  const b=await boot({hold:'parse',staticEvidence:true});b.gate.reject(new Error('parse failed'));await b.done;
  const message=b.nodes.get('#error').textContent;lose(b);assert.equal(b.nodes.get('#error').textContent,message);assert.equal(message,'parse failed');usableEvidence(b);
  assert.equal(b.nodes.get('#canvas').listeners.get('webglcontextlost')?.size||0,0);b.nodes.get('#language').onclick();assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);
});
test('loss and final unload clean listener/resource ownership exactly once',async()=>{
  const b=await boot();await b.done;const canvas=b.nodes.get('#canvas');lose(b);lose(b);
  assert.equal(canvas.listeners.get('webglcontextlost')?.size||0,0);b.dispatch('pagehide',false);b.dispatch('pagehide',false);
  assert.equal(b.metrics.rendererDisposed,1);assert.equal(b.metrics.controlsDisposed,1);assert.deepEqual(b.metrics.revoked,b.metrics.created);
  const status=b.nodes.get('#viewer-status').textContent;lose(b);canvas.emit('webglcontextrestored');b.nodes.get('#language').onclick();assert.equal(b.nodes.get('#viewer-status').textContent,status);assert.equal(b.pending.size,0);
});
test('ordinary unload during loading detaches loss listener and blocks late parse',async()=>{
  const b=await boot({hold:'parse'});b.dispatch('pagehide',false);lose(b);b.gate.resolve();await b.done;
  assert.equal(b.nodes.get('#canvas').listeners.get('webglcontextlost')?.size||0,0);assert.equal(b.metrics.renders,0);assert.equal(b.metrics.rendererDisposed,1);assert.deepEqual(b.metrics.revoked,b.metrics.created);
});
test('recovery action reloads only the live document and rejects detached old buttons',async()=>{
  const b=await boot();await b.done;lose(b);const old=b.nodes.get('#error').childNodes.at(-1);b.nodes.get('#language').onclick();old.emit('click');assert.equal(b.metrics.reloads,0);
  const current=b.nodes.get('#error').childNodes.at(-1);current.emit('click');assert.equal(b.metrics.reloads,1);b.dispatch('pagehide',false);current.emit('click');assert.equal(b.metrics.reloads,1);
});

test('failed model fetch does not invent a context-loss or verified-Blob state',async()=>{
  const b=await boot({hold:'fetchModel',staticEvidence:true});b.gate.reject(new Error('HTTP 404'));await b.done;
  const message=b.nodes.get('#error').textContent;b.element('#canvas').emit('webglcontextlost');assert.equal(b.nodes.get('#error').textContent,message);assert.equal(message,'HTTP 404');assert.deepEqual(b.metrics.created,[]);assert.equal(b.metrics.rendererDisposed,0);assert.equal(b.pending.size,0);assert.equal(b.element('#canvas').listeners.get('webglcontextlost')?.size||0,0);b.nodes.get('#language').onclick();assert.match(b.nodes.get('#viewer-status').textContent,/交互视图不可用/);assert.match(b.nodes.get('#fallback').innerHTML,/retained-static.png/);
});

test('a record without static images keeps the missing-evidence notice honest',async()=>{
  const b=await boot();await b.done;const fallback=b.nodes.get('#fallback').innerHTML;lose(b);unavailable(b);assert.equal(b.nodes.get('#fallback').innerHTML,fallback);assert.match(fallback,/No linked static evidence/);assert.match(b.nodes.get('#error').textContent,/any linked static evidence/);b.nodes.get('#language').onclick();assert.match(b.nodes.get('#error').textContent,/已关联的静态证据/);
});
