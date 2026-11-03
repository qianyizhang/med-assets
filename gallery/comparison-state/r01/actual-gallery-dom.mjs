// Actual gallery renderer with local recorded data. DOM simulation, not WebGL/browser QA.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const root=process.env.SITE_SOURCE_ROOT;
if(!root)throw Error('Set SITE_SOURCE_ROOT to the guarded patched canonical Site source copy.');
const happyDOM=process.env.HAPPY_DOM_MODULE;
if(!happyDOM)throw Error('Set HAPPY_DOM_MODULE to the installed happy-dom module path; no download required.');
const {Window}=await import(happyDOM);
const window=new Window({url:'http://fixture.invalid/review/',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,disableJavaScriptEvaluation:true,enableFileSystemHttpRequests:false}});
const document=window.document;
document.write(fs.readFileSync(`${root}/public/review/index.html`,'utf8').replace(/<script[\s\S]*?<\/script>/g,''));
const scrollCalls=[];
for(const [k,v] of Object.entries({window,document,location:window.location,history:window.history,scrollY:713,scrollTo:(...args)=>scrollCalls.push(args),requestAnimationFrame:f=>f()}))globalThis[k]=v;
const calls=[];
const original=JSON.parse(fs.readFileSync(`${root}/public/review/review-data.json`));
globalThis.fetch=async u=>{calls.push(u);assert.equal(u,'review-data.json');return{ok:true,json:async()=>structuredClone(original)}};
await import(`${root}/public/review/review.js`);
assert.equal(document.querySelector('#error').textContent,'');
const candidate=()=>document.getElementById('candidate-adrenals__source-candidate-01');
const disclosures=()=>[...candidate().querySelectorAll('figure details')];
const layouts=()=>[...document.querySelectorAll('#assets .comparison')];
const sources=()=>[...candidate().children].find(x=>x.classList.contains('detail')).querySelector(':scope > details');
assert.ok(disclosures().length>=2);assert.ok(layouts().length>=2);
disclosures()[0].open=true;disclosures()[1].open=false;sources().open=true;
layouts()[0].classList.add('single');layouts()[1].classList.remove('single');
const choice=document.querySelector('#candidate-choice').value;
document.querySelector('#search').value='adrenal';document.querySelector('#gate').value='visual';document.querySelector('#status').value='failed';
for(const lang of ['zh','en']){
 document.querySelector('#lang').click();
 assert.equal(document.documentElement.lang,lang);
 assert.equal(disclosures()[0].open,true);assert.equal(disclosures()[1].open,false);assert.equal(sources().open,true);
 assert.equal(layouts()[0].classList.contains('single'),true);assert.equal(layouts()[1].classList.contains('single'),false);
 assert.equal(document.querySelector('#candidate-choice').value,choice);
 assert.equal(document.querySelector('#search').value,'adrenal');assert.equal(document.querySelector('#gate').value,'visual');assert.equal(document.querySelector('#status').value,'failed');
 assert.deepEqual(scrollCalls.at(-1),[0,713]);
}
// Explicitly closed state must survive after it was previously open.
disclosures()[0].open=false;sources().open=false;layouts()[0].classList.remove('single');
document.querySelector('#lang').click();
assert.equal(disclosures()[0].open,false);assert.equal(sources().open,false);assert.equal(layouts()[0].classList.contains('single'),false);
// Same evidence repeated in candidate/baseline/priority contexts must remain independent.
const figures=[...document.querySelectorAll('figure[data-evidence-id]')];
const duplicate=figures.find(f=>figures.some(g=>g!==f&&g.dataset.evidenceId===f.dataset.evidenceId&&g.closest('[id]')!==f.closest('[id]')));
assert.ok(duplicate,'real gallery has repeated evidence in independent contexts');
const repeated=figures.filter(f=>f.dataset.evidenceId===duplicate.dataset.evidenceId);
const contextIds=repeated.map(f=>f.closest('[id]').id);
repeated.forEach((f,i)=>{f.querySelector('details').open=i===0});
document.querySelector('#lang').click();
contextIds.forEach((id,i)=>{const f=[...document.getElementById(id).querySelectorAll('figure[data-evidence-id]')].find(f=>f.dataset.evidenceId===duplicate.dataset.evidenceId);assert.equal(f.querySelector('details').open,i===0)});
assert.deepEqual(calls,['review-data.json']);
assert.equal(document.querySelectorAll('img[src]').length,0,'fixture never activates lazy media');
assert.equal(window.localStorage.length,0);assert.equal(window.sessionStorage.length,0);
// Exhaustive current-gallery state coverage catches collisions between nested contexts.
const eligible=()=>[...document.querySelectorAll('details')].filter(x=>x.parentElement.id!=='candidates');
const allLayouts=()=>[...document.querySelectorAll('.comparison')];
const {captureComparisonState,restoreComparisonState}=await import(`${root}/public/review/comparison-state.mjs`);
eligible().forEach((x,i)=>x.open=i%3===0);allLayouts().forEach((x,i)=>x.classList.toggle('single',i%2===0));
const state=captureComparisonState(document);
assert.equal(state.disclosures.size,eligible().length,'no current disclosure key collision');
assert.equal(state.layouts.size,allLayouts().length,'no current layout key collision');
for(let i=0;i<4;i++){document.querySelector('#lang').click();assert.deepEqual(captureComparisonState(document),state)}
// Unit fixture supplements actual-source coverage: repeated same evidence in ONE context.
const host=document.createElement('section');host.id='same-context-test';document.body.append(host);
const fragment='<div class="comparison" data-evidence-group="same"><figure data-evidence-id="same"><details><summary>Source</summary></details></figure></div>';
host.innerHTML=fragment+fragment;
host.querySelectorAll('details')[0].open=true;host.querySelectorAll('details')[1].open=false;
host.querySelectorAll('.comparison')[0].classList.add('single');
const duplicateState=captureComparisonState(document);
host.innerHTML=fragment+fragment+'<details open><summary>New default</summary></details>';
restoreComparisonState(document,duplicateState);
assert.equal(host.querySelectorAll('details')[0].open,true);assert.equal(host.querySelectorAll('details')[1].open,false);
assert.deepEqual([...host.querySelectorAll('.comparison')].map(x=>x.classList.contains('single')),[true,false]);
assert.equal(host.querySelectorAll('details')[2].open,true,'new unmatched item keeps default');
host.remove();restoreComparisonState(document,duplicateState); // removed saved items safely ignored
console.log(JSON.stringify({pass:true,method:'Actual source Happy DOM simulation; not rendered browser/WebGL',languages:['en','zh','en'],fetchCalls:calls,duplicateContexts:contextIds,scrollPreserved:true}));
await window.happyDOM.abort();
