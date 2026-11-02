import fs from 'node:fs';import assert from 'node:assert/strict';
const dep=process.env.HAPPY_DOM_MODULE;if(!dep)throw Error('Set HAPPY_DOM_MODULE to an existing installed happy-dom module; no download.');const {Window}=await import(dep);
const root=process.env.GALLERY_ROOT?new URL('file://'+process.env.GALLERY_ROOT.replace(/\/$/,'')+'/'):new URL('../../',import.meta.url);const w=new Window({url:'http://fixture.invalid/review/'+(process.env.INITIAL_HASH||''),settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,disableJavaScriptEvaluation:true,enableFileSystemHttpRequests:false}}),d=w.document;
d.write(fs.readFileSync(new URL('public/review/index.html',root),'utf8').replace(/<script[\s\S]*?<\/script>/g,''));let scroll=[];
for(const[k,v]of Object.entries({window:w,document:d,location:w.location,history:w.history,scrollY:37,scrollTo:(...x)=>scroll.push(x),requestAnimationFrame:f=>f()}))globalThis[k]=v;
const calls=[];globalThis.fetch=async u=>{calls.push(u);assert.equal(u,'review-data.json');return{ok:true,json:async()=>JSON.parse(fs.readFileSync(new URL('public/review/review-data.json',root)))}};
await import(new URL('public/review/review.js',root));assert.equal(d.querySelector('#error').textContent,'');assert.equal(d.activeElement,d.body);
if(process.env.INITIAL_HASH){assert.equal(d.querySelector('#review-overview').hidden,true);assert.equal(d.querySelector('#candidate-choice').value,decodeURIComponent(process.env.INITIAL_HASH.slice('#candidate-'.length)));assert.equal(d.activeElement,d.body);console.log('PASS initial deep link selects exact hash and leaves focus untouched');await w.happyDOM.abort();process.exit(0);}
const link=id=>[...d.querySelectorAll('#review-overview [data-study]')].find(x=>x.dataset.study===id), first='adrenals__source-candidate-01', second='aortic_tree_z__r02', third='thymus__source-candidate-01';
link(first).click(); const initialLength=w.history.length; const choice=d.querySelector('#candidate-choice'); choice.focus();
function selected(id){choice.value=id;choice.dispatchEvent(new w.Event('change'));assert.equal(w.location.hash,'#candidate-'+encodeURIComponent(id));assert.equal(d.activeElement,choice);assert.equal(d.querySelector('#candidate-'+id).hidden,false);assert.equal(d.querySelector('#candidate-'+id).open,true);assert.equal(w.history.length,initialLength);}
selected(second); selected(third); selected(second);
// Reopening the serialized route selects the same study; no reload network simulation.
w.dispatchEvent(new w.HashChangeEvent('hashchange'));assert.equal(choice.value,second);assert.equal(d.querySelector('#candidate-'+second).hidden,false);
d.querySelector('#lang').click();assert.equal(choice.value,second);assert.equal(w.location.hash,'#candidate-'+second);choice.focus();selected(third);
d.querySelector('#lang').click();assert.equal(choice.value,third);assert.equal(w.location.hash,'#candidate-'+third);choice.focus();selected(second);selected(third);
// Invalid native selection must not write a malformed route or change the shown study.
const invalid=d.createElement('option');invalid.value='not-a-study';choice.append(invalid);choice.value=invalid.value;choice.dispatchEvent(new w.Event('change'));assert.equal(w.location.hash,'#candidate-'+third);assert.equal(d.querySelector('#candidate-'+third).hidden,false);
choice.value='';choice.dispatchEvent(new w.Event('change'));assert.equal(w.location.hash,'#candidate-'+third);assert.equal(d.querySelector('#candidate-'+third).hidden,false);assert.equal(w.history.length,initialLength);
// Filtered overview origin and hidden-origin fallback are additionally covered by tests/navigation-focus/dom.mjs.
// Back still returns to the originating overview link, retaining filters and no extra entries.
d.querySelector('#back-overview').click();assert.equal(w.location.hash,'#overview');assert.equal(d.activeElement,link(first));assert.equal(w.history.length,initialLength);
assert.deepEqual(calls,['review-data.json']);console.log('PASS actual-source DOM: repeated dropdown, EN/中文, serialized hash reopen, invalid ID, selector focus, Back origin, stable history and no asset fetch');await w.happyDOM.abort();
