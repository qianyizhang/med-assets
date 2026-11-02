import fs from 'node:fs';import assert from 'node:assert/strict';
const dep=process.env.HAPPY_DOM_MODULE;if(!dep)throw Error('Set HAPPY_DOM_MODULE to an existing installed happy-dom module; no download.');const {Window}=await import(dep);
const root=process.env.GALLERY_ROOT?new URL('file://'+process.env.GALLERY_ROOT.replace(/\/$/,'')+'/'):new URL('../../',import.meta.url);const w=new Window({url:'http://fixture.invalid/review/'+(process.env.INITIAL_HASH||''),settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,disableJavaScriptEvaluation:true,enableFileSystemHttpRequests:false}}),d=w.document;
d.write(fs.readFileSync(new URL('public/review/index.html',root),'utf8').replace(/<script[\s\S]*?<\/script>/g,''));let scroll=[];
for(const[k,v]of Object.entries({window:w,document:d,location:w.location,history:w.history,scrollY:37,scrollTo:(...x)=>scroll.push(x),requestAnimationFrame:f=>f()}))globalThis[k]=v;
const data=JSON.parse(fs.readFileSync(new URL('public/review/review-data.json',root)));
if(process.env.LABEL_FIXTURE){for(const e of data.evidence){if(process.env.LABEL_FIXTURE==='no-en')delete e.label.en;else e.label={};}}
const calls=[];globalThis.fetch=async u=>{calls.push(u);assert.equal(u,'review-data.json');return {ok:true,json:async()=>data}};
await import(new URL('public/review/review.js',root));assert.equal(d.querySelector('#error').textContent,'');
const {selectEvidence}=await import(new URL('public/review/evidence-view.mjs',root));
const snapshot=()=>Object.fromEntries(data.candidates.map(c=>{const node=d.getElementById('candidate-'+c.id);return[c.id,{hero:[...node.querySelectorAll('.visual-panel:first-of-type [data-evidence-id]')].map(n=>n.dataset.evidenceId),all:[...node.querySelectorAll('.visual-panel [data-evidence-id]')].map(n=>[n.dataset.evidenceId,n.querySelector('img').dataset.evidenceSrc]),captions:[...node.querySelectorAll('.visual-panel figcaption strong')].map(n=>n.textContent)}]}));
const en=snapshot();
for(const c of data.candidates){const items=selectEvidence([...new Set([...(c.beforeEvidenceIds||[]),...(c.evidenceIds||[])])],data),current=items.filter(e=>e.reviewPhase!=='baseline'),label=e=>e.label?.en||e.label?.zh||'',preferred=current.find(e=>/contact|多视图/.test(label(e)))||current.find(e=>/front|前视/.test(label(e)))||current[0],hero=[items.find(e=>e.reviewPhase==='baseline'),preferred].filter(Boolean);assert.deepEqual(en[c.id].hero,hero.map(e=>e.id));assert.deepEqual(en[c.id].all.map(x=>x[0]),[...hero,...items.filter(e=>!hero.includes(e))].map(e=>e.id));}
d.querySelector('#lang').click();const zh=snapshot();
for(const c of data.candidates){assert.deepEqual(zh[c.id].hero,en[c.id].hero);assert.deepEqual(zh[c.id].all,en[c.id].all);assert.notDeepEqual(zh[c.id].captions,en[c.id].captions);}
d.querySelector('#lang').click();assert.deepEqual(snapshot(),en);assert.deepEqual(calls,['review-data.json']);
console.log('PASS actual-source DOM '+data.candidates.length+' studies: stable primary/rest IDs and files, translated captions, EN→中文→EN; fixture='+(process.env.LABEL_FIXTURE||'original'));
await w.happyDOM.abort();
