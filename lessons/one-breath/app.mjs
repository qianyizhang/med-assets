import * as THREE from './.local/vendor/build/three.module.js';
import {initialState,reduce,breath,COPY,fallbackFrame,lessonStatus} from './state.mjs';
import {createLessonScene,applyLessonState,sceneLabels,CAMERAS} from './scene.mjs';
import {exchangeSVG} from './exchange.mjs';
import {loadModels} from './asset-loader.mjs';
const $=id=>document.getElementById(id);let state=initialState(),view,renderer,manifest,last=performance.now(),uiKey='',generation=0;
const camera=new THREE.OrthographicCamera(-.2,.2,.2,-.2,.001,10),look=new THREE.Vector3(...CAMERAS.mechanics.target);camera.position.set(...CAMERAS.mechanics.position);camera.lookAt(look);let cameraHeight=CAMERAS.mechanics.height;
const dispatch=action=>{state=reduce(state,action);renderUI();};
function renderStatus(previewLoaded=false){const status=lessonStatus(state,Boolean(renderer),previewLoaded);$('phase').textContent=status.phase;$('cue').textContent=status.cue;}
function renderUI(){const c=COPY[state.language],b=breath(state),key=[state.stage,state.language,state.playing,state.assets,state.phase>=1,state.gas,b.phaseName].join('|');if(key===uiKey)return;uiKey=key;
 document.documentElement.lang=state.language==='zh'?'zh-CN':'en';$('subtitle').textContent=c.sub;$('language').textContent=c.language;$('reset').textContent=c.reset;$('sources').textContent=c.receipt;
 if(!$('stages').children.length){for(let i=0;i<3;i++){const button=document.createElement('button');button.type='button';button.dataset.stage=i;button.innerHTML=`<span>0${i+1}</span><b></b>`;button.addEventListener('click',()=>dispatch({type:'stage',value:i}));$('stages').append(button);}}
 $('stages').querySelectorAll('button').forEach((button,i)=>{button.querySelector('b').textContent=c.stages[i];button.setAttribute('aria-current',i===state.stage?'step':'false');});
 for(const [id,value] of Object.entries({kicker:c.kicker[state.stage],heading:c.heading[state.stage],explanation:c.body[state.stage],limit:c.limit,'view-label':state.stage===2?c.diagram:c.source,'teaching-note':state.stage===2?c.exchangeNote:state.stage===1?c.routeNote:c.limit,'gas-title':c.action[2]}))$(id).textContent=value;
 renderStatus();
 $('breath-control').hidden=state.stage===2;$('gas-control').hidden=state.stage!==2;$('breath-control').disabled=state.assets!=='ready'||!renderer;
 $('breath-control').textContent=state.playing?c.pause:state.phase>=1?c.again:state.phase>0?c.resume:c.action[state.stage];
 document.querySelectorAll('[data-gas]').forEach(el=>{el.textContent=el.dataset.gas==='oxygen'?c.oxygen:c.co2;el.setAttribute('aria-pressed',String(el.dataset.gas===state.gas));});
 document.querySelector('.progress').hidden=!renderer&&state.stage!==2;
 $('exchange').hidden=state.stage!==2;$('labels').hidden=state.stage===2;document.querySelector('canvas').hidden=state.stage===2;
 if(state.stage===2){$('notice').replaceChildren();return;}
 if(state.assets==='error'){$('notice').replaceChildren(document.createTextNode(c.error));const detail=document.createElement('small');detail.textContent=state.error;$('notice').append(detail);const retry=document.createElement('button');retry.textContent=c.retry;retry.onclick=boot;$('notice').append(retry);}
 else if(state.assets==='loading')$('notice').textContent=c.loading;
 else if(!renderer){$('notice').replaceChildren();const image=document.createElement('img');image.src=`./.local/previews/${fallbackFrame(state)}.png`;image.alt=state.language==='en'?'Offline assembly preview':'离线构图预览';image.onload=()=>{if(image.isConnected)renderStatus(true);};image.onerror=()=>{if(!image.isConnected)return;$('notice').replaceChildren(document.createTextNode(c.fallbackMissing));};$('notice').append(image,document.createTextNode(c.fallback));}
 else $('notice').replaceChildren();
}
$('language').onclick=()=>dispatch({type:'language',value:state.language==='en'?'zh':'en'});$('reset').onclick=()=>dispatch({type:'reset'});$('breath-control').onclick=()=>dispatch({type:'play'});document.querySelectorAll('[data-gas]').forEach(b=>b.onclick=()=>dispatch({type:'gas',value:b.dataset.gas}));
async function boot(){const current=++generation;dispatch({type:'retry'});try{manifest=await (await fetch('./assets.json')).json();const models=await loadModels(manifest);if(current!==generation)return;view=createLessonScene(models,manifest);dispatch({type:'loaded'});}catch(e){if(current===generation)dispatch({type:'failed',message:e.message});}}
try{renderer=new THREE.WebGLRenderer({canvas:document.querySelector('canvas'),antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;}catch(e){console.info('No WebGL renderer:',e.message);}
renderUI();boot();
function frame(now){const dt=(now-last)/1000;last=now;state=reduce(state,{type:'tick',dt});renderUI();$('progress').style.width=`${state.phase*100}%`;
 if(state.stage===2){$('exchange').innerHTML=exchangeSVG(state);}else if(view&&renderer){
  applyLessonState(view,state);const config=state.stage===1?CAMERAS.airway:CAMERAS.mechanics;const mix=matchMedia('(prefers-reduced-motion: reduce)').matches?1:Math.min(1,dt*8);camera.position.lerp(new THREE.Vector3(...config.position),mix);look.lerp(new THREE.Vector3(...config.target),mix);cameraHeight+=(config.height-cameraHeight)*mix;camera.lookAt(look);
  const box=$('scene').getBoundingClientRect();renderer.setSize(box.width,box.height,false);const aspect=box.width/box.height;camera.left=-cameraHeight*aspect/2;camera.right=cameraHeight*aspect/2;camera.top=cameraHeight/2;camera.bottom=-cameraHeight/2;camera.updateProjectionMatrix();renderer.render(view.scene,camera);
  $('labels').replaceChildren(...sceneLabels(state,manifest).map(label=>{const point=new THREE.Vector3(...label.position).project(camera),el=document.createElement('span');el.className='label';el.textContent=label.text;el.dataset.port=label.id;el.style.left=`${(point.x+1)*50}%`;el.style.top=`${(1-point.y)*50}%`;return el;}));
 }
 requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
