import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {focusStudyContext,restoreOverviewFocus} from './fixtures/navigation-focus.mjs';
import {captureComparisonState,restoreComparisonState} from './fixtures/comparison-state.mjs';
import {elbowLegendCorrection,captionHTML,selectEvidence} from './fixtures/evidence-view.mjs';

const updated = fs.readFileSync(new URL('fixtures/review.js', import.meta.url));
const source = updated.toString();
const statement = prefix => { const rows=source.split('\n').filter(line=>line.startsWith(prefix)); assert.equal(rows.length,1); return rows[0]; };
const data = JSON.parse(fs.readFileSync(new URL('fixtures/entries.json', import.meta.url)));
function harness(raw, lang) {
  const elements = new Map();
  const el = selector => {
    if (!elements.has(selector)) elements.set(selector, {innerHTML: '', textContent: '', value: ''});
    return elements.get(selector);
  };
  const esc = value => String(value ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  const context = {data: {...structuredClone(data), issues: []}, lang, overviewQuery: '', overviewView: 'baseline', $: el, esc,
    b: value => typeof value === 'string' ? value : value?.[lang] || value?.en || '',
    displayName: c => c.name[lang] || c.name.en, shortRemaining: () => '', t: x => x, applyStudyMode() {}};
  const source = raw.toString();
  const start = source.indexOf('function renderOverview(){');
  const end = source.indexOf('\nfunction applyStudyMode()', start);
  assert(start >= 0 && end > start);
  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  context.renderOverview();
  return {context, elements, html: () => el('#overview-rows').innerHTML};
}
function labels(html) {
  return [...html.matchAll(/<strong>.*?<\/strong><small>(.*?)<\/small>/g)].map(m => m[1]);
}
for (const lang of ['en', 'zh']) test(`actual renderer ${lang}: seven study-only rows, 62 originals and preserved destinations`, () => {
  const h = harness(updated, lang), actual = labels(h.html());
  assert.equal(data.assets.length, 69);
  assert.equal(data.candidates.length, 38);
  assert.equal(actual.length, 69);
  assert(h.elements.get('#review-overview').innerHTML.includes(lang === 'zh' ? '素材条目 · 69' : 'Asset entries · 69'));
  data.assets.forEach((asset, i) => {
    assert.equal(actual[i], asset.hasBaseline === false ? (lang === 'zh' ? '仅研究条目（无原始基线）' : 'Study-only entry (no baseline)') : (lang === 'zh' ? '原版' : 'Original'));
    assert(h.html().includes(`href="#asset-${encodeURIComponent(asset.id)}"`));
    assert(h.html().includes(`href="${asset.source.file.replace(/&/g, '&amp;')}" download`));
  });
  assert.equal(data.assets.filter(a => a.hasBaseline === false).length, 7);
  h.context.overviewView = 'current'; h.context.renderOverviewRows();
  assert.equal(labels(h.html()).length, 38);
  assert(labels(h.html()).every(x => x === (lang === 'zh' ? '更新版' : 'Updated version')));
  h.context.overviewView = 'all'; h.context.renderOverviewRows(); assert.equal(labels(h.html()).length, 107);
  h.context.overviewView = 'baseline'; h.context.overviewQuery = 'parotid_glands'; h.context.renderOverviewRows();
  assert.equal(labels(h.html()).length, 1);
  h.context.overviewQuery = 'no-matching-record-xyz'; h.context.renderOverviewRows(); assert.equal(labels(h.html()).length, 0);
});

test('native study selection updates only valid URLs and never pushes history',()=>{
 const choice={value:''}, replaced=[], shown=[];
 const context={data:{candidates:[{id:'aorta study'},{id:'adrenals'}]},$:()=>choice,
   history:{replaceState:(_state,_title,url)=>replaced.push(url),pushState:()=>assert.fail('unexpected new history')},showStudy:id=>shown.push(id)};
 vm.runInNewContext(statement("$('#candidate-choice').onchange="),context);
 for(const id of ['aorta study','adrenals','','unknown']){choice.value=id;choice.onchange();}
 assert.deepEqual(replaced,['#candidate-aorta%20study','#candidate-adrenals']);
 assert.deepEqual(shown,['aorta study','adrenals']);
});

test('evidence ordering is independent of locale with explicit label fallbacks',()=>{
 const evidence=[{id:'base',file:'base.webp',reviewPhase:'baseline',label:{en:'Baseline',zh:'基线'}},
   {id:'front',file:'front.webp',label:{en:'front',zh:'前视'}},
   {id:'contact',file:'contact.webp',label:{en:'contact',zh:'完整与切开'}}];
 const candidate={beforeEvidenceIds:['base'],evidenceIds:['front','contact']};
 for(const fallback of ['en','zh','empty']){
  const items=structuredClone(evidence);
  if(fallback==='zh'){delete items[2].label.en;items[2].label.zh='多视图';}
  if(fallback==='empty')for(const item of items)item.label={};
  for(const lang of ['en','zh','en']){
   const context={data:{evidence:items},lang,selectEvidence,captionHTML,
     esc:x=>x,b:x=>x?.[lang]||x?.en||''};
   vm.createContext(context);vm.runInContext(statement('function galleryEvidence('),context);
   const html=context.galleryEvidence(candidate);
   const ids=[...html.matchAll(/data-evidence-id="([^"]+)"/g)].map(m=>m[1]);
   assert.deepEqual(ids,fallback==='empty'?['base','front','contact']:['base','contact','front']);
  }
 }
});

test('supplement links retain their own asset owner in either locale',()=>{
 for(const lang of ['en','zh']){
  const host={innerHTML:''},asset={id:'blood',name:{en:'Blood',zh:'血液'},topicIds:[],source:{file:'baseline.glb'},issueIds:[],history:[],gates:{}};
  const context={lang,$:()=>host,esc:x=>x,b:x=>x?.[lang]||x?.en||'',t:x=>x,badges:()=>'',
    supplementalChecks:()=>'',negativeEvidenceHTML:()=>'',contextSupplementsHTML:()=>'',teachingEvidenceHTML:()=>'',runtimeEvidenceHTML:()=>'',
    data:{assets:[asset],candidates:[{id:'cell-study',assetId:'blood-cell-study',logicalSupplementFor:'blood',reviewable:true,name:{en:'Cells',zh:'细胞'}}],topics:[]}};
  vm.runInNewContext(statement("$('#assets').innerHTML="),context);
  assert(host.innerHTML.includes('candidate.html?asset=blood-cell-study&candidate=cell-study'));
  assert(!host.innerHTML.includes('candidate.html?asset=blood&candidate=cell-study'));
 }
});

test('elbow correction requires all three identities and precedes the caption',()=>{
 const proof=JSON.parse(fs.readFileSync(new URL('../../gallery/elbow-legend-source.json',import.meta.url)));
 const item={id:proof.contactEvidence.id,sha256:proof.contactEvidence.imageSHA256,assetBinding:proof.artifactSHA256,label:{en:'Elbow',zh:'肘'}};
 for(const lang of ['en','zh']){
  const notice=elbowLegendCorrection(item,lang);assert(notice.includes('data-elbow-legend-correction'));
  assert.match(notice,lang==='en'?/articular capsule/:/关节囊/);
  assert(captionHTML(item,lang).startsWith(notice));assert(!notice.includes('<details'));
 }
 for(const key of ['id','sha256','assetBinding'])assert.equal(elbowLegendCorrection({...item,[key]:'wrong'}),'');
 assert.equal(elbowLegendCorrection(null),'');
});

function focusNode(id,visible=true){return {id,isConnected:visible,hidden:false,dataset:{},closest(){return this.hidden?{}:null},focus(options){this.focused=options}};}
test('Compare and Back focus only visible unique targets, with safe fallback',()=>{
 const study=focusNode('study-focus'),search=focusNode('overview-search'),origin=focusNode('origin');origin.dataset.study='aorta';
 const overview=focusNode('review-overview');let links=[origin];overview.querySelectorAll=()=>links;
 const document={getElementById:id=>({'study-focus':study,'overview-search':search,'review-overview':overview}[id])};
 focusStudyContext(document);assert.deepEqual(study.focused,{preventScroll:true});
 restoreOverviewFocus(document,'aorta');assert.deepEqual(origin.focused,{preventScroll:true});
 for(const kind of ['missing','hidden','duplicate']){
  delete search.focused;links=kind==='missing'?[]:[origin];origin.hidden=kind==='hidden';if(kind==='duplicate')links.push(origin);
  restoreOverviewFocus(document,'aorta');assert.deepEqual(search.focused,{preventScroll:true});
 }
 delete study.focused;study.hidden=true;focusStudyContext(document);assert.equal(study.focused,undefined);
 delete search.focused;overview.hidden=true;restoreOverviewFocus(document,'missing');assert.equal(search.focused,undefined);
});

test('comparison disclosure and layout state restore independently without controlling study roots',()=>{
 const first={id:'evidence-one',open:true},second={id:'evidence-two',open:false},candidate={id:'candidate',open:true,parentElement:{id:'candidates'}};
 let single=true;const layout={id:'comparison',classList:{contains:()=>single,toggle:(_name,value)=>single=value}};
 let disclosures=[first,second,candidate];
 const document={querySelectorAll:selector=>selector==='details'?disclosures:[layout]};
 const state=captureComparisonState(document);
 first.open=false;second.open=true;candidate.open=false;single=false;
 const added={id:'new-evidence',open:true};disclosures.push(added);
 restoreComparisonState(document,state);
 assert.equal(first.open,true);assert.equal(second.open,false);assert.equal(candidate.open,false);assert.equal(added.open,true);assert.equal(single,true);
});
