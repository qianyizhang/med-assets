(async function () {
  'use strict';
  const $ = q => document.querySelector(q);
  const canvas = $('#model');
  const expected = '90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7';
  const controls = [...document.querySelectorAll('button,input')];
  controls.forEach(e => e.disabled=true);
  let controller, parts, framePending=false;
  let camera={yaw:.35,pitch:1.15,zoom:1,center:[0,0,0],extent:1};
  function scene() {
    const colours=controller.view().colours;
    const byLabel = new Map(controller.resolve().map(x=>[x.label,x]));
    return parts.flatMap(part => {
      const resolved=byLabel.get(part.label);
      return resolved.visible ? part.primitives.map(pr=>({pos:transform(pr.pos,resolved.matrix),idx:pr.idx,color:colours[part.label],alpha:1,name:part.label})) : [];
    });
  }
  function render() {
    if (!controller) return;
    const selected=controller.snapshot(), playback=controller.playback(), view=controller.view();
    const syncNumber=(id,value)=>{const input=$(id);if(document.activeElement!==input)input.value=String(value);};
    for(const key of ['yaw','pitch','zoom']) syncNumber('#camera-'+key,view.camera[key]);
    for(let i=0;i<3;i++) syncNumber('#target-'+i,view.camera.target[i]);
    for(const label of DentalControls.LABELS) $('#colour-'+label).value='#'+view.colours[label].map(v=>v.toString(16).padStart(2,'0')).join('');
    const seconds=value=>(value/1000).toFixed(2)+' s';
    $('#timeline').max=String(playback.duration);
    $('#timeline').value=String(playback.position);
    $('#timeline').setAttribute('aria-valuetext',seconds(playback.position)+' of '+seconds(playback.duration));
    $('#time').textContent=seconds(playback.position)+' / '+seconds(playback.duration);
    $('#play').disabled=playback.playing;
    $('#pause').disabled=!playback.playing;
    const status=playback.playing?'Playing editorial sequence':playback.position===playback.duration?'Sequence finished':'Paused';
    if ($('#playback-status').textContent!==status) $('#playback-status').textContent=status;
    const total=rasterize(scene(),canvas,camera,false);
    $('#count').textContent=total.toLocaleString()+' source triangles';
    $('#amount').textContent=Math.round(selected.reveal*100)+'%';
    $('#reveal').value=String(Math.round(selected.reveal*100));
    document.querySelectorAll('[data-layer]').forEach(button=>button.setAttribute('aria-pressed',String(selected.isolate===button.dataset.layer)));
    const name=selected.isolate ? selected.isolate[0].toUpperCase()+selected.isolate.slice(1) : null;
    const selection=name ? name+' isolated · other layers hidden' : 'All four layers visible';
    if ($('#selection').textContent!==selection) $('#selection').textContent=selection;
    $('#scene-status').textContent=(selected.reveal===0?'Source pose':Math.round(selected.reveal*100)+'% editorial separation')+' · '+(name?name+' only':'all four layers visible');
    window.__dentalControlEvidence={...selected,playback,visible:controller.resolve().filter(x=>x.visible).map(x=>x.label),triangles:total,sourceSha256:expected,sourceChecked:true,presentation:DentalAuthoring.PRESENTATION,viewState:controller.view(),camera:{...camera,center:[...camera.center]}};
  }
  function schedule() {
    if(framePending)return;
    framePending=true;
    requestAnimationFrame(()=>{
      framePending=false;
      // Sample live controller state, not a captured frame. Reset/pause are final.
      controller.tick();
      render();
      if(controller.playback().playing)schedule();
    });
  }
  function fitFixedEnvelope() {
    if (!controller || !canvas.clientWidth || !canvas.clientHeight) return;
    camera=DentalAuthoring.recordedView(parts,canvas.clientWidth,canvas.clientHeight,controller.view()).camera;
    schedule();
  }

  try {
    const raw=atob($('#source-glb').textContent.trim());const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
    if(!crypto.subtle)throw new Error('Source checking needs a browser with Web Crypto support.');
    const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(actual!==expected)throw new Error('The embedded source does not match the expected specimen.');
    parts=parseGLB(bytes.buffer).map(p=>({...p,label:p.name.split('/').pop()}));
    controller=DentalAuthoring.fresh(parts, () => performance.now());
    controller.setTimeline(DentalAuthoring.SHOT);
    const saved=$('#authoring-script').textContent.trim();
    if(saved) controller=DentalAuthoring.load(new TextDecoder().decode(Uint8Array.from(atob(saved),c=>c.charCodeAt(0))),parts,()=>performance.now());
    controls.forEach(e=>e.disabled=false);$('#load-status').textContent='';
    $('#play').addEventListener('click',()=>{controller.play();schedule();});
    $('#pause').addEventListener('click',()=>{controller.pause();schedule();});
    $('#timeline').addEventListener('input',event=>{controller.scrub(Number(event.target.value));schedule();});
    $('#reveal').addEventListener('input',event=>{controller.dispatch({type:'reveal',value:Number(event.target.value)/100});schedule();});
    document.querySelectorAll('[data-layer]').forEach(button=>button.addEventListener('click',()=>{controller.dispatch({type:'isolate',label:button.dataset.layer});schedule();}));
    $('#all').addEventListener('click',()=>{controller.dispatch({type:'all'});schedule();});
    $('#reset').addEventListener('click',()=>{controller.dispatch({type:'reset'});$('#presentation-error').textContent='';fitFixedEnvelope();schedule();});
    function editView(update) {
      const candidate=controller.view();
      try {
        update(candidate);controller.editView(candidate);
        $('#presentation-error').textContent='';fitFixedEnvelope();
      } catch(error) {
        $('#presentation-error').textContent=error.message;
        // Restore controls to committed values without advancing playback.
        render();
      }
    }
    for(const key of ['yaw','pitch','zoom']) $('#camera-'+key).addEventListener('change',event=>editView(view=>{
      if(!event.target.value.trim())throw Error('Enter a finite camera value.');
      view.camera[key]=Number(event.target.value);
    }));
    for(let i=0;i<3;i++) $('#target-'+i).addEventListener('change',event=>editView(view=>{
      if(!event.target.value.trim())throw Error('Enter a finite target value.');
      view.camera.target[i]=Number(event.target.value);
    }));
    for(const label of DentalControls.LABELS) $('#colour-'+label).addEventListener('input',event=>editView(view=>{
      if(!/^#[0-9a-f]{6}$/i.test(event.target.value))throw Error('Choose an opaque RGB colour.');
      view.colours[label]=[1,3,5].map(i=>parseInt(event.target.value.slice(i,i+2),16));
    }));
    new ResizeObserver(fitFixedEnvelope).observe(canvas);fitFixedEnvelope();
    window.dentalAuthoring=Object.freeze({
      save:()=>DentalAuthoring.serialize(controller,parts,canvas.clientWidth,canvas.clientHeight),
      load:text=>{
        const candidate=DentalAuthoring.load(text,parts,()=>performance.now());
        controller=candidate;fitFixedEnvelope();schedule();
      }
    });
  } catch(error) {
    controls.forEach(e=>e.disabled=true);
    $('#load-status').textContent='Preview could not load: '+error.message;
    $('#scene-status').textContent='No geometry shown. Controls are disabled.';
  }
})();
