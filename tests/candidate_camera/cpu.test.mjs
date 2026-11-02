import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {clearPendingOrbit} from '../../gallery/candidate-camera/r01/camera-reset.mjs';

assert.ok(process.env.CAMERA_VENDOR_STAGE && process.env.CAMERA_SOURCE, 'Use run_cpu.py');
const THREE=await import(pathToFileURL(process.env.CAMERA_VENDOR_STAGE+'/three.module.js'));
const {OrbitControls}=await import(pathToFileURL(process.env.CAMERA_VENDOR_STAGE+'/OrbitControls.js'));
const source=fs.readFileSync(process.env.CAMERA_SOURCE,'utf8');
const witness=JSON.parse(fs.readFileSync(new URL('./witness.json',import.meta.url)));
const start=source.indexOf('let direction=framing?'),end=source.indexOf(';const resize=()=>');
assert.ok(start>=0 && end>start, 'Actual candidate Fit function is required');
const segment=source.slice(start,end);

class DOM {
  constructor(){this.handlers=new Map();this.style={};this.clientHeight=640;this.clientWidth=640;}
  addEventListener(type,fn){const list=this.handlers.get(type)||new Set();list.add(fn);this.handlers.set(type,list);}
  removeEventListener(type,fn){this.handlers.get(type)?.delete(fn);}
  getRootNode(){return this;}
  setPointerCapture(){} releasePointerCapture(){}
  getBoundingClientRect(){return {left:0,top:0,width:640,height:640};}
  emit(type,extra={}){
    const event={type,pointerType:'mouse',pointerId:1,button:0,clientX:100,clientY:100,
      ctrlKey:false,shiftKey:false,metaKey:false,deltaMode:0,deltaY:-120,preventDefault(){},...extra};
    for(const fn of this.handlers.get(type)||[])fn(event);
  }
  drag(button=0){this.emit('pointerdown',{button});this.emit('pointermove',{button,clientX:180});this.emit('pointerup',{button,clientX:180});}
}
function setup(recorded=true,damping=true){
  const camera=recorded?new THREE.OrthographicCamera(-5.8,5.8,5.8,-5.8,.001,1000):new THREE.PerspectiveCamera(38,1,.001,1000);
  const dom=new DOM(),controls=new OrbitControls(camera,dom);controls.enableDamping=damping;
  const scene=new THREE.Group(),a=new THREE.Object3D(),b=new THREE.Object3D();a.name='context-a';b.name='context-b';a.position.set(1,2,3);b.position.set(-2,0,1);scene.add(a,b);
  const originalVisibility=new Map();scene.traverse(o=>originalVisibility.set(o,o.visible));
  const framing=recorded?{initial:'front',span:11.6,sourceViews:true,views:{front:witness}}:null;
  const center=new THREE.Vector3(-.15,-.35,0),size=new THREE.Vector3(2,3,1);
  const resize=()=>{camera.left=-framing.span/2;camera.right=framing.span/2;camera.top=framing.span/2;camera.bottom=-framing.span/2;camera.updateProjectionMatrix();};
  // Exact original/patched Fit body. Only its environmental bindings are supplied.
  const fit=new Function('THREE','camera','controls','model','framing','center','size','originalVisibility','resize','clearPendingOrbit',segment+';return fit;')(
    THREE,camera,controls,{scene},framing,center,size,originalVisibility,resize,clearPendingOrbit);
  fit('front');return {camera,dom,controls,fit,scene,framing};
}
function snapshot(x){return {position:x.camera.position.clone(),target:x.controls.target.clone(),up:x.camera.up.clone(),quaternion:x.camera.quaternion.clone(),zoom:x.camera.zoom};}
function error(x,wanted){return {angle:THREE.MathUtils.radToDeg(x.camera.quaternion.angleTo(wanted.quaternion)),position:x.camera.position.distanceTo(wanted.position),target:x.controls.target.distanceTo(wanted.target)};}
function exact(x,wanted){const e=error(x,wanted);assert.ok(e.angle<1e-5,JSON.stringify(e));assert.ok(e.position<1e-9,JSON.stringify(e));assert.ok(e.target<1e-9,JSON.stringify(e));assert.ok(x.camera.up.distanceTo(wanted.up)<1e-12);assert.equal(x.camera.zoom,wanted.zoom);}
function advance(x){for(let i=0;i<60;i++)x.controls.update();}

test('exact current core revision and no-drag source Front stay unchanged',()=>{
  assert.equal(THREE.REVISION,'180');const x=setup();const wanted=snapshot(x);x.fit('front');exact(x,wanted);advance(x);exact(x,wanted);x.controls.dispose();
});
for(const recorded of [true,false])for(const [kind,button]of [['rotation',0],['pan',2]])for(const action of ['front','fit']){
  test(`${recorded?'recorded source':'generic'} ${action} discards prior real-handler ${kind}`,()=>{
    const x=setup(recorded);const wanted=snapshot(x);x.dom.drag(button);x.fit(action);exact(x,wanted);advance(x);exact(x,wanted);assert.equal(x.controls.enableDamping,true);x.controls.dispose();
  });
}
test('wheel zoom then source Front restores zoom/span/pose and remains stable',()=>{
  const x=setup();const wanted=snapshot(x);x.dom.emit('wheel');assert.notEqual(x.camera.zoom,1);x.fit('front');exact(x,wanted);assert.equal(x.camera.top-x.camera.bottom,11.6);advance(x);exact(x,wanted);x.controls.dispose();
});
test('repeated generic front/back/left Fit changes do not retain old input',()=>{
  const x=setup(false),clean=setup(false);
  for(const direction of ['back','left','front','left','back','front']){
    clean.fit(direction);const wanted=snapshot(clean);x.dom.drag(direction==='left'?2:0);x.fit(direction);exact(x,wanted);advance(x);exact(x,wanted);
  }
  x.controls.dispose();clean.controls.dispose();
});
test('ordinary rotation and pan damping still work after reset',()=>{
  const x=setup();x.dom.drag();x.fit('front');const before=snapshot(x);x.dom.drag();const immediate=snapshot(x);assert.ok(error(x,before).angle>.01);x.controls.update();assert.ok(error(x,immediate).angle>.01);x.fit('front');const start=x.controls.target.clone();x.dom.drag(2);const one=x.controls.target.clone();assert.ok(one.distanceTo(start)>0);x.controls.update();assert.ok(x.controls.target.distanceTo(one)>0);assert.equal(x.controls.enableDamping,true);x.controls.dispose();
});
test('disabled damping stays disabled after a deliberate reset',()=>{
  const x=setup(true,false);const wanted=snapshot(x);x.dom.drag();x.fit('front');exact(x,wanted);advance(x);exact(x,wanted);assert.equal(x.controls.enableDamping,false);x.controls.dispose();
});
test('source visibility and node transforms survive drag/reset cycles',()=>{
  const x=setup();const before=x.scene.children.map(o=>({position:o.position.toArray(),quaternion:o.quaternion.toArray(),scale:o.scale.toArray(),visible:o.visible}));
  for(let i=0;i<3;i++){x.scene.children[0].visible=false;x.dom.drag(2);x.fit('front');}
  assert.deepEqual(x.scene.children.map(o=>({position:o.position.toArray(),quaternion:o.quaternion.toArray(),scale:o.scale.toArray(),visible:o.visible})),before);x.controls.dispose();
});
