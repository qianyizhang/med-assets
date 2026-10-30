import test from 'node:test';import assert from 'node:assert/strict';
import {initialState,reduce,breath,COPY,fallbackFrame,lessonStatus} from '../state.mjs';
test('initial state is paused with no airflow and exchange directions remain defined',()=>{const s=initialState();assert.equal(s.playing,false);assert.equal(breath(s).flow,0);assert.equal(breath(s).oxygenDirection,'air-to-blood');});
test('one shared phase reverses airflow while lung expansion rises then falls',()=>{const s={...initialState(),phase:.25,playing:true};assert.equal(breath(s).phaseName,'in');assert.equal(breath({...s,phase:.75}).phaseName,'out');assert.ok(breath({...s,phase:.5}).amplitude>breath(s).amplitude);assert.equal(breath({...s,phase:1}).amplitude,0);});
test('one play completes once and clamps oversized timing steps',()=>{let s=reduce(reduce(initialState(),{type:'loaded'}),{type:'play'});s=reduce(s,{type:'tick',dt:999});assert.ok(s.phase<.02);for(let i=0;i<65;i++)s=reduce(s,{type:'tick',dt:.1});assert.equal(s.phase,1);assert.equal(s.playing,false);assert.equal(reduce(s,{type:'play'}).phase,0);});
test('stage switch preserves breath progress, gas and language',()=>{const s={...initialState('zh'),phase:.34,playing:true,gas:'carbon-dioxide'};const n=reduce(s,{type:'stage',value:2});assert.equal(n.phase,.34);assert.equal(n.playing,true);assert.equal(n.language,'zh');assert.equal(n.gas,'carbon-dioxide');assert.equal(reduce(s,{type:'stage',value:7}),s);});
test('reset returns to mechanics and rest without losing language or availability',()=>{const n=reduce({...initialState('zh'),stage:2,phase:.8,elapsed:99,playing:true,gas:'carbon-dioxide',assets:'ready'},{type:'reset'});assert.deepEqual(n,{...initialState('zh'),assets:'ready'});});
test('failure stops the lesson and retry cannot start before assets load',()=>{let s=reduce({...initialState(),assets:'ready',playing:true},{type:'failed',message:'HTTP 404'});assert.equal(s.playing,false);assert.equal(s.error,'HTTP 404');s=reduce(s,{type:'retry'});assert.equal(s.assets,'loading');assert.equal(s.error,'');assert.equal(reduce(s,{type:'play'}).playing,false);});
test('diffusion directions do not reverse during exhalation or stop at rest',()=>{for(const phase of [0,.25,.5,.75,1]){const b=breath({...initialState(),phase});assert.equal(b.oxygenDirection,'air-to-blood');assert.equal(b.carbonDioxideDirection,'blood-to-air');}const s=reduce(initialState(),{type:'tick',dt:.1});assert.ok(breath(s).exchangeProgress>0);assert.equal(s.phase,0);});
test('English and Chinese contain the same complete control and stage vocabulary',()=>{assert.deepEqual(Object.keys(COPY.en).sort(),Object.keys(COPY.zh).sort());for(const lang of ['en','zh']){const c=COPY[lang];assert.equal(c.stages.length,3);assert.equal(c.heading.length,3);assert.equal(c.action.length,3);assert.ok(c.retry&&c.fallback&&c.diagram&&c.exchangeNote);}});

test('pause freezes airway clock and mechanics while exchange clock continues',()=>{const s={...initialState(),assets:'ready',phase:.25,breathClock:2,elapsed:2,playing:false};const n=reduce(s,{type:'tick',dt:.1});assert.equal(n.phase,s.phase);assert.equal(n.breathClock,s.breathClock);assert.equal(breath(n).flow,0);assert.ok(n.elapsed>s.elapsed);assert.equal(breath(n).phaseName,'paused');});
test('end inspiration is not labeled as the initial resting state',()=>{assert.equal(breath({...initialState(),phase:.5}).phaseName,'peak');for(const language of ['en','zh'])assert.notEqual(COPY[language].phase.peak,COPY[language].phase.rest);});

test('fallback uses the resting frame after reset and labels missing previews in both languages',()=>{assert.equal(fallbackFrame(initialState()),'mechanics-rest');assert.equal(fallbackFrame({...initialState(),phase:.4}),'mechanics-in');assert.equal(fallbackFrame({...initialState(),stage:1}),'airway');for(const c of Object.values(COPY))assert.ok(c.preview&&c.fallbackMissing&&c.snapshot);});

for(const language of ['en','zh']) {
  test(`${language}: loading, failure, retry and recovery status follows availability`,()=>{
    const c=COPY[language];
    let s=initialState(language);
    for(const hasRenderer of [false,true]) {
      assert.deepEqual(lessonStatus(s,hasRenderer),{phase:c.phase.loading,cue:c.loading});
      const failed=reduce(s,{type:'failed',message:'HTTP 404'});
      assert.deepEqual(lessonStatus(failed,hasRenderer),{phase:c.phase.error,cue:c.retry});
      assert.equal(reduce(failed,{type:'play'}).playing,false);
      assert.deepEqual(lessonStatus(reduce(failed,{type:'reset'}),hasRenderer),lessonStatus(failed,hasRenderer));
      assert.deepEqual(lessonStatus(reduce(failed,{type:'retry'}),hasRenderer),lessonStatus(s,hasRenderer));
    }
    s=reduce(reduce(reduce(s,{type:'failed'}),{type:'retry'}),{type:'loaded'});
    assert.deepEqual(lessonStatus(s,true),{phase:c.phase.rest,cue:c.cue.rest});
    assert.deepEqual(lessonStatus(s,false),{phase:c.phase.unavailable,cue:c.cue.unavailable});
    assert.deepEqual(lessonStatus(s,false,true),{phase:c.preview,cue:c.snapshot});
  });

  test(`${language}: stage, language and reset cannot restore readiness while unavailable`,()=>{
    const other=language==='en'?'zh':'en';
    for(const assets of ['loading','error','ready']) {
      for(const phase of [0,.25,.5,.75,1]) {
        let s={...initialState(language),assets,phase};
        const expected=lessonStatus(s,false);
        assert.notEqual(expected.cue,COPY[language].cue.rest);
        s=reduce(s,{type:'stage',value:1});
        assert.deepEqual(lessonStatus(s,false),expected);
        s=reduce(s,{type:'stage',value:2});
        assert.deepEqual(lessonStatus(s,false),{phase:COPY[language].phase.exchange,cue:COPY[language].oxygenPath});
        s=reduce(s,{type:'gas',value:'carbon-dioxide'});
        assert.equal(lessonStatus(s,false).cue,COPY[language].co2Path);
        s=reduce(s,{type:'language',value:other});
        assert.deepEqual(lessonStatus(s,false),{phase:COPY[other].phase.exchange,cue:COPY[other].co2Path});
        s=reduce(s,{type:'reset'});
        assert.equal(s.language,other);
        assert.equal(s.assets,assets);
        assert.deepEqual(lessonStatus(s,false),lessonStatus({...initialState(other),assets},false));
      }
    }
  });

  test(`${language}: available motion retains breath cues and interrupted progress recovers paused`,()=>{
    const c=COPY[language];
    for(const [phase,playing,name] of [[0,false,'rest'],[.25,true,'in'],[.5,true,'peak'],[.75,true,'out'],[.25,false,'paused'],[1,false,'rest']]) {
      const s={...initialState(language),assets:'ready',phase,playing};
      assert.deepEqual(lessonStatus(s,true),{phase:c.phase[name],cue:c.cue[name]});
      for(const type of ['failed','retry'])assert.notEqual(lessonStatus(reduce(s,{type}),true).cue,c.cue[name]);
    }
    let s={...initialState(language),assets:'ready',phase:.25,playing:true};
    for(const type of ['failed','retry','loaded'])s=reduce(s,{type});
    assert.deepEqual(lessonStatus(s,true),{phase:c.phase.paused,cue:c.cue.paused});
    assert.deepEqual(lessonStatus(reduce(s,{type:'reset'}),true),{phase:c.phase.rest,cue:c.cue.rest});
  });
}
