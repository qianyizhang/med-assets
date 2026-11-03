import fs from 'node:fs';import assert from 'node:assert/strict';
const dep=process.env.HAPPY_DOM_MODULE;if(!dep)throw Error('Set HAPPY_DOM_MODULE to an existing installed happy-dom module; no download.');const {Window}=await import(dep);
const root=process.env.GALLERY_ROOT?new URL('file://'+process.env.GALLERY_ROOT.replace(/\/$/,'')+'/'):new URL('../../',import.meta.url);const w=new Window({url:'http://fixture.invalid/review/'+(process.env.INITIAL_HASH||''),settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,disableJavaScriptEvaluation:true,enableFileSystemHttpRequests:false}}),d=w.document;
d.write(fs.readFileSync(new URL('public/review/index.html',root),'utf8').replace(/<script[\s\S]*?<\/script>/g,''));let scroll=[];
for(const[k,v]of Object.entries({window:w,document:d,location:w.location,history:w.history,scrollY:37,scrollTo:(...x)=>scroll.push(x),requestAnimationFrame:f=>f()}))globalThis[k]=v;
const calls=[];globalThis.fetch=async u=>{calls.push(u);assert.equal(u,'review-data.json');return{ok:true,json:async()=>JSON.parse(fs.readFileSync(new URL('public/review/review-data.json',root)))}};
await import(new URL('public/review/review.js',root));assert.equal(d.querySelector('#error').textContent,'');assert.equal(d.activeElement,d.body);
const {selectRecord}=await import(new URL('public/review/candidate-contract.mjs',root));
const data=JSON.parse(fs.readFileSync(new URL('public/review/review-data.json',root)));
function check(){
 const links=[...d.querySelectorAll('#assets a[href^="candidate.html?"]')];assert.equal(links.length,40);
 let supplements=0;
 for(const a of links){const q=new URL(a.href,w.location.href).searchParams;const id=q.get('candidate');const expected=data.candidates.find(c=>c.id===id);assert.ok(expected);assert.equal(q.get('asset'),expected.assetId);const actual=selectRecord(data,q.get('asset'),id);assert.equal(actual.id,expected.id);assert.deepEqual(actual.source,expected.source);assert.deepEqual(actual.gates,expected.gates);
 const parent=a.closest('[data-asset]').dataset.asset;assert.ok(parent===expected.assetId||parent===expected.logicalSupplementFor);if(parent!==expected.assetId){supplements++;assert.throws(()=>selectRecord(data,parent,id),/Unknown candidate ID/);}
 }
 assert.equal(supplements,3);
}
check();d.querySelector('#lang').click();check();d.querySelector('#lang').click();check();
assert.throws(()=>selectRecord(data,'not-an-asset',data.candidates[0].id),/Unknown asset ID/);
assert.throws(()=>selectRecord(data,data.candidates[0].assetId,'not-a-candidate'),/Unknown candidate ID/);
assert.deepEqual(calls,['review-data.json']);console.log('PASS 40 archive links × EN/中文/EN; 3 supplement associations; exact source/gates; invalid-owner rejection; zero media requests');await w.happyDOM.abort();
