import test from 'node:test';
import assert from 'node:assert/strict';
import {boot} from './module-harness.mjs';

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
for(const hold of ['review','reviewJson','manifest','manifestBody','fetchModel','body','verifyTransport','decode','digest','imports','parse'])test('ordinary unload while awaiting '+hold+' prevents late startup',async()=>{
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
