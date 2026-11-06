import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
import {eligible as kneeEligible,createKneeInspection,inspectionText,HIDDEN} from '../public/review/knee-inspection.mjs';
import {createViewerLifecycle} from '../public/review/viewer-lifecycle.mjs';
import {watchContextLoss} from '../public/review/context-loss.mjs';
import {cameraSpec} from '../public/review/candidate-contract.mjs';
const source=fs.readFileSync(new URL('../public/review/candidate.js',import.meta.url),'utf8');
const data=JSON.parse(fs.readFileSync(new URL('../public/review/review-data.json',import.meta.url)));
function harness(id='joints__z-knee-r01'){
 const record=data.candidates.find(c=>c.id===id),nodes=HIDDEN.map(name=>({isMesh:true,visible:true,userData:{source_object_name:name}})),root={traverse(f){nodes.forEach(f)}};
 const elements=new Map();function el(){return {style:{},hidden:false,textContent:'',attrs:{},children:[],setAttribute(k,v){this.attrs[k]=v},append(...x){this.children.push(...x)},after(x){elements.set('#'+x.id,x)},querySelector(t){return this.children.find(x=>x.tag===t)}};}
 for(const s of ['#controls','#viewport','#error','[data-view=fit]'])elements.set(s,el());
 const doc={querySelector:s=>elements.get(s),createElement(tag){return Object.assign(el(),{tag})}};
 const target=new EventTarget(),canvas=new EventTarget(),lifecycle=createViewerLifecycle(target);
 const vector=()=>({fromArray(a){this.value=[...a];return this},toArray(){return this.value}});const camera={position:vector(),up:vector(),updateProjectionMatrix(){},lookAt(){}};const controls={target:vector(),update(){}};
 const c={scene:{},canvas,watchContextLoss,record,model:{scene:root},document:doc,$:s=>doc.querySelector(s),lifecycle,kneeEligible,createKneeInspection,inspectionText,cameraSpec,framing:cameraSpec(record),camera,controls,wrap:{clientWidth:800,clientHeight:600},renderer:{setSize(){},render(){}},clearPendingOrbit(){},ResizeObserver:class{observe(){}disconnect(){}},requestAnimationFrame:()=>1,cancelAnimationFrame(){},contextGuard:{check(){}},modes:null,paintEye(){},paint(){},lang:'en',state:'loading',knee:null,fit:null};
 const paint=source.slice(source.indexOf('function paintKnee(){'),source.indexOf('\nconst lifecycle='));
 const start=source.indexOf('let originalVisibility=new Map();'),end=source.indexOf("contextGuard.check();state='ready';paint();",start)+"contextGuard.check();state='ready';paint();".length;
 vm.createContext(c);const guard=source.slice(source.indexOf('contextGuard=watchContextLoss('),source.indexOf('});scene.add(new THREE.HemisphereLight')+3);vm.runInContext(paint+'\n'+guard+'\n'+source.slice(start,end),c);return {c,nodes,elements,lifecycle,target,canvas};
}
test('actual candidate composition: deep → language → reset / exterior',()=>{const h=harness(),{c,nodes,elements}=h;assert(nodes.every(n=>n.visible));elements.get('#knee-inspection').querySelector('button').onclick();assert(nodes.every(n=>!n.visible));assert(c.knee.active);c.lang='zh';c.paintKnee();assert(elements.get('#knee-inspection').querySelector('p').textContent.includes('髌下脂肪垫'));assert(c.knee.active);c.fit('fit');assert(nodes.every(n=>n.visible));assert(!c.knee.active);c.fit('deep');c.fit('back');assert(nodes.every(n=>n.visible));});
function dispatch(target,type,persisted){const event=new Event(type);if(persisted!==undefined)Object.defineProperty(event,'persisted',{value:persisted});target.dispatchEvent(event);}
test('real lifecycle BFCache and context-loss events restore visibility and disable controls',()=>{const h=harness(),{c,nodes,elements,lifecycle}=h;c.fit('deep');dispatch(h.target,'pagehide',true);assert(lifecycle.suspended);assert(nodes.every(n=>n.visible));assert(elements.get('#knee-inspection').hidden);elements.get('#knee-inspection').querySelector('button').onclick();assert(nodes.every(n=>n.visible));dispatch(h.target,'pageshow',true);assert(!lifecycle.suspended);assert(nodes.every(n=>n.visible));assert(!c.knee.active);c.fit('deep');dispatch(h.canvas,'webglcontextlost');assert(lifecycle.failed);assert(c.contextGuard.lost);assert(nodes.every(n=>n.visible));assert(elements.get('#knee-inspection').hidden);assert(elements.get('#controls').hidden);assert(elements.get('#viewport').hidden);});
test('real terminal pagehide restores original visibility',()=>{const h=harness();h.c.fit('deep');dispatch(h.target,'pagehide',false);assert(h.lifecycle.disposed);assert(h.nodes.every(n=>n.visible));assert(h.elements.get('#knee-inspection').hidden);});
test('actual non-knee composition creates no inspection UI and preserves generic views',()=>{const h=harness('joints__z-elbow-r01');assert.equal(h.c.knee,null);assert(!h.elements.has('#knee-inspection'));h.c.fit('back');assert(h.nodes.every(n=>n.visible));});
