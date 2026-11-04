/* Mandatory real bytes for this suite; no fixture fallback or skip. */
'use strict';
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const C=require('./controller.js'),{readSource,source}=require('./bp3d-source.cjs');
if(!process.env.BP3D_SOURCE)throw Error('BP3D_SOURCE must name the hydrated pinned GLB.');
const path=process.env.BP3D_SOURCE,bytes=fs.readFileSync(path),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const input=readSource(bytes);
test('actual BP3D identities and native coordinates agree with manifest and parser',()=>{
 assert.equal(input.parts.length,30);assert.equal(input.parts.filter(p=>p.label.endsWith('tooth')).length,28);
 assert.deepEqual(input.doc.nodes.map(n=>n.extras.source_frame),Array(30).fill(source.frame));
 const ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,DataView};vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8')+';this.parse=parseGLB;',ctx);
 const real=ctx.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
 assert.deepEqual(Array.from(real,p=>p.name),input.contract.labels);assert(real.every(p=>p.primitives.length>0));
 const arrays=()=>real.flatMap(p=>p.primitives.flatMap(pr=>[hash(Buffer.from(pr.pos.buffer)),hash(Buffer.from(pr.idx.buffer))]));const before=arrays();
 const c=C.createController(input.parts,input.contract),base=c.resolve();
 for(const part of input.parts){for(let i=0;i<3;i++){c.dispatch({type:'isolate',label:part.label});assert.deepEqual(c.resolve().filter(p=>p.visible).map(p=>p.label),[part.label]);}c.dispatch({type:'reset'});assert.deepEqual(c.resolve(),base);}
 assert.deepEqual(arrays(),before);assert.equal(hash(fs.readFileSync(path)),source.sha256);
});
test('BP3D repeated selection interrupted by reset returns all source matrices without geometry edits',()=>{
 const c=C.createController(input.parts,input.contract),base=c.resolve(),doc=JSON.stringify(input.doc);
 for(let i=0;i<90;i++){c.dispatch({type:'reveal',value:(i%11)/10});c.dispatch({type:'isolate',label:input.parts[i%30].label});c.dispatch({type:'all'});c.dispatch({type:'isolate',label:input.parts[(i+1)%30].label});c.dispatch({type:'reset'});assert.deepEqual(c.resolve(),base);}
 assert.equal(JSON.stringify(input.doc),doc);assert.equal(hash(bytes),source.sha256);
});
test('actual source parts reject omitted duplicated renamed and invalid transforms',()=>{
 for(const mutate of [p=>p.pop(),p=>p[1]=p[0],p=>p[0].label='invented tooth',p=>p[0].matrix[0]=NaN]){const parts=structuredClone(input.parts);mutate(parts);assert.throws(()=>C.createController(parts,input.contract));}
});
test('missing truncated corrupt or replacement source fails closed',()=>{
 for(const b of [Buffer.alloc(0),bytes.subarray(0,100),Buffer.from('version https://git-lfs.github.com/spec/v1'),Buffer.from(bytes)]){if(b.length===bytes.length)b[b.length-1]^=1;assert.throws(()=>readSource(b));}
});
