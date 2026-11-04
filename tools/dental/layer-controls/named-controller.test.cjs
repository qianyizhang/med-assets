'use strict';
const assert=require('node:assert/strict'),test=require('node:test');
const C=require('./controller.js');
const labels=['named tooth A','named tooth B','gingiva'];
const contract=()=>({labels:[...labels],offsets:Object.fromEntries(labels.map((n,i)=>[n,[i*.01,0,0]]))});
const parts=()=>labels.map((label,i)=>({label,matrix:C.IDENTITY.map((v,k)=>k===12?i*.1:v)}));
test('same controller supports arbitrary contracted identities and canonical order',()=>{
 const c=C.createController(parts().reverse(),contract());assert.deepEqual(c.resolve().map(p=>p.label),labels);
 for(const label of labels){c.dispatch({type:'isolate',label});assert.deepEqual(c.resolve().filter(p=>p.visible).map(p=>p.label),[label]);}
});
test('generic contract rejects missing duplicate unknown and invalid identities',()=>{
 for(const ps of [[],parts().slice(1),[...parts(),parts()[0]],[parts()[0],parts()[0],parts()[2]],[...parts().slice(1),{label:'unknown'}],[null,...parts().slice(1)]])assert.throws(()=>C.createController(ps,contract()));
 for(const ls of [[],['a','a'],[''],[null],Array(2)])assert.throws(()=>C.createController(parts(),{...contract(),labels:ls}));
});
test('offsets and transforms reject nonfinite sparse missing and extra inputs',()=>{
 for(const value of [null,[1],Array(3),[0,NaN,0],[0,Infinity,0]]){const k=contract();k.offsets[labels[0]]=value;assert.throws(()=>C.createController(parts(),k));}
 for(const value of [null,Array(16),Array(16).fill(NaN)]){const p=parts();p[0].matrix=value;assert.throws(()=>C.createController(p,contract()));}
 const k=contract();delete k.offsets[labels[0]];assert.throws(()=>C.createController(parts(),k));k.offsets.unknown=[0,0,0];assert.throws(()=>C.createController(parts(),k));
});
test('captured contract and source cannot be changed by callers',()=>{
 const p=parts(),k=contract(),c=C.createController(p,k);c.dispatch({type:'reveal',value:1});const b=c.resolve();k.labels.reverse();k.offsets[labels[1]][0]=99;p[0].matrix[12]=99;assert.deepEqual(c.resolve(),b);
});
test('repeated and interrupted manual sequences reset exactly and reject atomically',()=>{
 const c=C.createController(parts(),contract()),base=c.resolve();
 for(let i=0;i<100;i++){c.dispatch({type:'reveal',value:(i%9)/8});c.dispatch({type:'isolate',label:labels[i%3]});c.dispatch({type:'reset'});c.dispatch({type:'reset'});assert.deepEqual(c.resolve(),base);const state=c.snapshot();assert.throws(()=>c.dispatch({type:'isolate',label:'missing'}));assert.deepEqual(c.snapshot(),state);}
});
test('default FDI31 contract retains its labels offsets and reveal behavior',()=>{
 const c=C.createController(C.LABELS.map(label=>({label})));c.dispatch({type:'reveal',value:.5});
 assert.deepEqual(c.resolve().map(p=>p.matrix.slice(12,15)),C.LABELS.map(l=>C.OFFSETS[l].map(v=>v*.5)));
});
