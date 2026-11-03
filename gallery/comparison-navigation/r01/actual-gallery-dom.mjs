import fs from 'node:fs';import assert from 'node:assert/strict';
const dep=process.env.HAPPY_DOM_MODULE;if(!dep)throw Error('Set HAPPY_DOM_MODULE to an existing installed happy-dom module; no download.');const {Window}=await import(dep);
const root=process.env.GALLERY_ROOT?new URL('file://'+process.env.GALLERY_ROOT.replace(/\/$/,'')+'/'):new URL('../../',import.meta.url);const w=new Window({url:'http://fixture.invalid/review/'+(process.env.INITIAL_HASH||''),settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,disableJavaScriptEvaluation:true,enableFileSystemHttpRequests:false}}),d=w.document;
d.write(fs.readFileSync(new URL('public/review/index.html',root),'utf8').replace(/<script[\s\S]*?<\/script>/g,''));let scroll=[];
for(const[k,v]of Object.entries({window:w,document:d,location:w.location,history:w.history,scrollY:37,scrollTo:(...x)=>scroll.push(x),requestAnimationFrame:f=>f()}))globalThis[k]=v;
const calls=[];globalThis.fetch=async u=>{calls.push(u);assert.equal(u,'review-data.json');return{ok:true,json:async()=>JSON.parse(fs.readFileSync(new URL('public/review/review-data.json',root)))}};
await import(new URL('public/review/review.js',root));assert.equal(d.querySelector('#error').textContent,'');assert.equal(d.activeElement,d.body);
if(process.env.INITIAL_HASH){assert.equal(d.querySelector('#review-overview').hidden,true);assert.equal(d.activeElement,d.body);console.log('PASS initial deep link leaves focus untouched');await w.happyDOM.abort();process.exit(0);}
const link=id=>[...d.querySelectorAll('#review-overview [data-study]')].find(x=>x.dataset.study===id),id='adrenals__source-candidate-01';
function open(){const a=link(id);a.focus();a.click();assert.equal(d.activeElement.id,'study-focus');assert.equal(d.activeElement.getAttribute('tabindex'),'-1');assert.ok(d.activeElement.textContent);assert.equal(d.activeElement.closest('[hidden]'),null);assert.equal(w.location.hash,'#candidate-'+id);}
function back(expected){const a=d.querySelector('#back-overview');a.focus();a.click();assert.equal(d.activeElement,expected());assert.equal(d.activeElement.closest('[hidden]'),null);assert.equal(w.location.hash,'#overview');}
open();back(()=>link(id));open();back(()=>link(id));
open();link(id).remove();back(()=>d.querySelector('#overview-search'));
d.querySelector('#lang').click();open();link(id).hidden=true;back(()=>d.querySelector('#overview-search'));
d.querySelector('#lang').click();open();const search=d.querySelector('#overview-search');search.value='no-match-xyz';search.dispatchEvent(new w.Event('input'));back(()=>d.querySelector('#overview-search'));search.value='';search.dispatchEvent(new w.Event('input'));
// Re-render restores overview rows; duplicate destinations use safe fallback.
d.querySelector('#lang').focus();d.querySelector('#lang').click();assert.equal(d.activeElement.id,'lang');
open();link(id).after(link(id).cloneNode(true));back(()=>d.querySelector('#overview-search'));
d.querySelector('#lang').click();open();
const choice=d.querySelector('#candidate-choice');choice.focus();choice.value='thymus__source-candidate-01';choice.dispatchEvent(new w.Event('change'));assert.equal(d.activeElement,choice);
// An external hash route does not impose a focus move.
d.querySelector('#lang').focus();w.location.hash='#overview';w.dispatchEvent(new w.Event('hashchange'));assert.equal(d.activeElement.id,'lang');
assert.deepEqual(calls,['review-data.json']);console.log('PASS actual-source DOM: initial, repeated Compare/Back, missing/duplicate origins, native select, language and hash focus; no asset requests');await w.happyDOM.abort();
