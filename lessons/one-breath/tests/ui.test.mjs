import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import * as stateModule from '../state.mjs';
import {exchangeSVG} from '../exchange.mjs';

// Execute the real app body with small DOM/renderer/loader doubles. This checks
// event wiring and stale callbacks, not browser layout, image decoding or WebGL.
const source=await fs.readFile(new URL('../app.mjs',import.meta.url),'utf8');
const html=await fs.readFile(new URL('../index.html',import.meta.url),'utf8');
class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.style={};this.attributes={};this.text='';}
  get isConnected(){return this.root||Boolean(this.parent?.isConnected);}
  get textContent(){return this.text+this.children.map(child=>child.textContent).join('');}
  set textContent(value){this.replaceChildren();this.text=value;}
  set innerHTML(value){this.textContent=value;if(this.tag==='button'){this.bold=new Element('b');this.append(this.bold);}}
  get innerHTML(){return this.text;}
  append(...children){for(const child of children){child.parent=this;this.children.push(child);}}
  replaceChildren(...children){for(const child of this.children)child.parent=null;this.children=[];this.text='';this.append(...children);}
  setAttribute(name,value){this.attributes[name]=value;}
  addEventListener(type,callback){this['on'+type]=callback;}
  querySelector(selector){return selector==='b'?this.bold:null;}
  querySelectorAll(selector){return this.children.filter(child=>child.tag===selector);}
  click(){if(!this.disabled)this.onclick?.();}
}
async function harness(hasRenderer=false){
  const elements=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(([,id])=>[id,new Element()]));
  for(const element of Object.values(elements))element.root=true;
  const gases=['oxygen','carbon-dioxide'].map(gas=>{const element=new Element('button');element.dataset.gas=gas;return element;});
  const canvas=new Element('canvas'),progress=new Element();
  const document={documentElement:{},getElementById:id=>elements[id],createElement:tag=>new Element(tag),
    createTextNode:text=>{const node=new Element('text');node.text=text;return node;},
    querySelector:selector=>selector==='canvas'?canvas:progress,querySelectorAll:()=>gases};
  class Vector3 {set(){} }
  class OrthographicCamera {position=new Vector3();lookAt(){} }
  class WebGLRenderer {constructor(){if(!hasRenderer)throw Error('Test: no WebGL');}setPixelRatio(){} }
  const pending=[];let frame;
  vm.runInNewContext(source.replace(/^import .*;\n/gm,''),{
    ...stateModule,document,THREE:{Vector3,OrthographicCamera,WebGLRenderer},
    CAMERAS:{mechanics:{target:[0,0,0],position:[0,0,1],height:1}},
    createLessonScene:()=>({}),loadModels:()=>new Promise((resolve,reject)=>pending.push({resolve,reject})),
    fetch:async()=>({json:async()=>({})}),exchangeSVG,devicePixelRatio:1,
    performance:{now:()=>0},requestAnimationFrame:callback=>{frame=callback;},console:{info(){}},
  },{filename:'app.mjs'});
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  await settle();
  return {elements,gases,settle,pending,step:()=>frame(100),
    status:()=>({phase:elements.phase.textContent,cue:elements.cue.textContent}),
    stage:index=>elements.stages.children[index].click(),
    image:()=>elements.notice.children.find(child=>child.tag==='img'),
    retry:async()=>{elements.notice.children.find(child=>child.tag==='button').click();await settle();},
    load:async(error)=>{const next=pending.shift();assert.ok(next,'expected a pending model load');error?next.reject(Error(error)):next.resolve({});await settle();},
  };
}

for(const hasRenderer of [false,true]) {
  test(`app events: availability, language, stages, reset and retry (renderer=${hasRenderer})`,async()=>{
    const app=await harness(hasRenderer),{elements:e}=app;
    assert.deepEqual(app.status(),{phase:'Loading models',cue:'Loading the teaching models…'});
    assert.equal(e['breath-control'].disabled,true);
    await app.load('HTTP 404');
    assert.deepEqual(app.status(),{phase:'Models unavailable',cue:'Retry assets'});
    assert.match(e.notice.textContent,/HTTP 404/);
    e.language.click();
    assert.deepEqual(app.status(),{phase:'模型不可用',cue:'重试加载'});
    app.stage(1);
    assert.equal(e.cue.textContent,'重试加载');
    app.stage(2);app.gases[1].click();app.step();
    assert.deepEqual(app.status(),{phase:'气体交换',cue:'血液 → 空气'});
    assert.equal(e.notice.textContent,'');
    assert.equal(e['breath-control'].hidden,true);
    assert.equal(e['gas-control'].hidden,false);
    assert.match(e.exchange.innerHTML,/CO₂/);
    e.reset.click();
    assert.deepEqual(app.status(),{phase:'模型不可用',cue:'重试加载'});
    await app.retry();
    assert.deepEqual(app.status(),{phase:'正在加载模型',cue:'正在加载教学模型…'});
    app.stage(1);e.language.click();e.reset.click();
    assert.deepEqual(app.status(),{phase:'Loading models',cue:'Loading the teaching models…'});
    await app.load('size mismatch');
    assert.deepEqual(app.status(),{phase:'Models unavailable',cue:'Retry assets'});
    await app.retry();await app.load();
    assert.equal(e['breath-control'].disabled,!hasRenderer);
    assert.deepEqual(app.status(),hasRenderer?{phase:'At rest',cue:'Ready for one breath'}:{phase:'3D unavailable',cue:'Breath motion unavailable'});
  });
}

test('preview load/error callbacks cannot overwrite a later language, stage or reset',async()=>{
  const app=await harness(),{elements:e}=app;
  await app.load();
  const first=app.image();
  first.onload();
  assert.deepEqual(app.status(),{phase:'Static preview',cue:'Offline composition · motion unavailable'});
  e.language.click();
  first.onload();first.onerror();
  assert.deepEqual(app.status(),{phase:'三维视图不可用',cue:'呼吸运动不可用'});
  const chinese=app.image();
  chinese.onload();
  assert.deepEqual(app.status(),{phase:'静态预览',cue:'离线静态构图 · 未运行运动'});
  app.stage(1);const airway=app.image();
  assert.match(airway.src,/airway\.png$/);
  airway.onerror();
  assert.deepEqual(app.status(),{phase:'三维视图不可用',cue:'呼吸运动不可用'});
  assert.match(e.notice.textContent,/离线预览不可用/);
  app.stage(0);const pending=app.image();
  app.stage(2);pending.onload();pending.onerror();app.step();
  assert.deepEqual(app.status(),{phase:'气体交换',cue:'空气 → 血液'});
  assert.equal(e.notice.textContent,'');
  e.reset.click();
  assert.deepEqual(app.status(),{phase:'三维视图不可用',cue:'呼吸运动不可用'});
  assert.match(app.image().src,/mechanics-rest\.png$/);
  assert.equal(e['breath-control'].disabled,true);
});
