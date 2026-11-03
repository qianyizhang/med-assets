(async function () {
  'use strict';
  const $ = q => document.querySelector(q);
  const canvas = $('#model');
  const expected = '90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7';
  const colours = {enamel:[224,223,201],dentin:[211,168,80],pulp:[222,82,126],bone:[115,145,148]};
  const controls = [...document.querySelectorAll('button,input')];
  controls.forEach(e => e.disabled=true);
  let controller, parts, framePending=false;
  let camera={yaw:.35,pitch:1.15,zoom:1,center:[0,0,0],extent:1};
  function scene() {
    const byLabel = new Map(controller.resolve().map(x=>[x.label,x]));
    return parts.flatMap(part => {
      const resolved=byLabel.get(part.label);
      return resolved.visible ? part.primitives.map(pr=>({pos:transform(pr.pos,resolved.matrix),idx:pr.idx,color:colours[part.label],alpha:1,name:part.label})) : [];
    });
  }
  function render() {
    if (!controller) return;
    const selected=controller.snapshot();
    const total=rasterize(scene(),canvas,camera,false);
    $('#count').textContent=total.toLocaleString()+' source triangles';
    $('#amount').textContent=Math.round(selected.reveal*100)+'%';
    $('#reveal').value=String(Math.round(selected.reveal*100));
    document.querySelectorAll('[data-layer]').forEach(button=>button.setAttribute('aria-pressed',String(selected.isolate===button.dataset.layer)));
    const name=selected.isolate ? selected.isolate[0].toUpperCase()+selected.isolate.slice(1) : null;
    $('#selection').textContent=name ? name+' isolated · other layers hidden' : 'All four layers visible';
    $('#scene-status').textContent=(selected.reveal===0?'Source pose':Math.round(selected.reveal*100)+'% editorial separation')+' · '+(name?name+' only':'all four layers visible');
    window.__dentalControlEvidence={...selected,visible:controller.resolve().filter(x=>x.visible).map(x=>x.label),triangles:total,sourceSha256:expected,sourceChecked:true,camera:{...camera,center:[...camera.center]}};
  }
  function schedule() {
    if(framePending)return;
    framePending=true;
    requestAnimationFrame(()=>{framePending=false;render();});
  }
  function fitFixedEnvelope() {
    if (!controller || !canvas.clientWidth || !canvas.clientHeight) return;
    camera=fixedEnvelopeCamera(parts,canvas.clientWidth,canvas.clientHeight,DentalControls.OFFSETS);
    schedule();
  }

  try {
    const raw=atob($('#source-glb').textContent.trim());const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
    if(!crypto.subtle)throw new Error('Source checking needs a browser with Web Crypto support.');
    const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(actual!==expected)throw new Error('The embedded source does not match the expected specimen.');
    parts=parseGLB(bytes.buffer).map(p=>({...p,label:p.name.split('/').pop()}));
    controller=DentalControls.createController(parts.map(p=>({label:p.label,matrix:DentalControls.IDENTITY})));
    controls.forEach(e=>e.disabled=false);$('#load-status').textContent='';
    $('#reveal').addEventListener('input',event=>{controller.dispatch({type:'reveal',value:Number(event.target.value)/100});schedule();});
    document.querySelectorAll('[data-layer]').forEach(button=>button.addEventListener('click',()=>{controller.dispatch({type:'isolate',label:button.dataset.layer});schedule();}));
    $('#all').addEventListener('click',()=>{controller.dispatch({type:'all'});schedule();});
    $('#reset').addEventListener('click',()=>{controller.dispatch({type:'reset'});schedule();});
    new ResizeObserver(fitFixedEnvelope).observe(canvas);fitFixedEnvelope();
  } catch(error) {
    controls.forEach(e=>e.disabled=true);
    $('#load-status').textContent='Preview could not load: '+error.message;
    $('#scene-status').textContent='No geometry shown. Controls are disabled.';
  }
})();
