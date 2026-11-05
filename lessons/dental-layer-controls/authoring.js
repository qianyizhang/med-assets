/* Source-bound JSON scripts for this CPU viewer, not glTF animation export. */
(function(root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else root.DentalAuthoring = factory(root.DentalControls, fixedEnvelopeCamera);
})(typeof globalThis === 'object' ? globalThis : this, function(C, fitCamera) {
  'use strict';
  const freeze = value => { Object.values(value).forEach(x => { if(x && typeof x === 'object') freeze(x); }); return Object.freeze(value); };
  const SOURCE = freeze({sha256:'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7',bytes:2052220,
    path:'models/swirendo_fdi31/exports/balanced-20261028/FDI31-balanced.glb',
    frame:'native specimen coordinates in metres; parser bakes source node transforms',
    licence:'CC BY-SA 4.0',attribution:'SWIRendo A_1_31_T2_SEG_na; Benz, Heck and Walter (2024)',doi:'https://doi.org/10.5282/ubm/data.477'});
  const PRESENTATION = freeze({camera:'fixed-envelope-v1',target:'full source-and-reveal envelope midpoint',
    materials:'opaque editorial RGB; source glTF materials are not imported',
    colours:{enamel:[224,223,201],dentin:[211,168,80],pulp:[222,82,126],bone:[115,145,148]}});
  const SHOT = freeze([
    {time:0,reveal:0,isolate:null},{time:1000,reveal:0,isolate:null},
    {time:3000,reveal:1,isolate:null},{time:4000,reveal:1,isolate:'pulp'},
    {time:5000,reveal:1,isolate:null},{time:7000,reveal:0,isolate:null},{time:8000,reveal:0,isolate:null}
  ]);
  // Structural equality ignores JSON object key ordering, but rejects missing/extra keys.
  function equal(a,b) {
    if(a === b) return true;
    if(!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a)!==Array.isArray(b)) return false;
    const keys=Object.keys(a);
    return keys.length===Object.keys(b).length && keys.every(k=>Object.hasOwn(b,k)&&equal(a[k],b[k]));
  }
  const VIEW_DEFAULT = freeze({camera:{yaw:.35,pitch:1.15,zoom:1,target:[0,0,0]},colours:PRESENTATION.colours});
  const clone = value => JSON.parse(JSON.stringify(value));
  const keysAre = (value, keys) => value && !Array.isArray(value) && equal(Object.keys(value).sort(), [...keys].sort());
  function validateView(value) {
    if(!keysAre(value,['camera','colours']) || !keysAre(value.camera,['yaw','pitch','zoom','target']) || !keysAre(value.colours,C.LABELS)) throw Error('Invalid presentation fields.');
    const c=value.camera;
    const bounded=(v,min,max)=>Number.isFinite(v)&&v>=min&&v<=max;
    if(!bounded(c.yaw,-Math.PI,Math.PI)||!bounded(c.pitch,-Math.PI/2,Math.PI/2)||!bounded(c.zoom,.5,1.5)||
      !Array.isArray(c.target)||c.target.length!==3||!equal(Object.keys(c.target),['0','1','2'])||!Array.from(c.target).every(v=>bounded(v,-.25,.25))) throw Error('Camera outside bounded editorial range.');
    for(const label of C.LABELS) {
      const rgb=value.colours[label];
      if(!Array.isArray(rgb)||rgb.length!==3||!equal(Object.keys(rgb),['0','1','2'])||!Array.from(rgb).every(v=>Number.isInteger(v)&&bounded(v,0,255))) throw Error('Palette requires opaque integer RGB channels 0–255.');
    }
    return clone(value);
  }
  function fresh(parts, clock) {
    const base=C.createController(parts.map(p=>({label:p.label,matrix:C.IDENTITY})),undefined,clock);
    const baseline=clone(VIEW_DEFAULT);
    let view=clone(baseline);
    return Object.freeze({...base,
      view:()=>clone(view),
      editView:value=>{
        const candidate=validateView(value); // Reject completely before pausing or changing state.
        base.dispatch({type:'reveal',value:base.snapshot().reveal});
        view=candidate;
        return clone(view);
      },
      dispatch:action=>{
        const result=base.dispatch(action);
        if(action.type==='reset') view=clone(baseline);
        return result;
      }
    });
  }
  function recordedView(parts, width, height, view=VIEW_DEFAULT) {
    if(!Number.isFinite(width)||!Number.isFinite(height)||width<1||height<1||width>16384||height>16384) throw Error('Invalid recorded viewport.');
    const state=validateView(view),camera=fitCamera(parts,width,height,C.OFFSETS);
    camera.center=camera.center.map((v,i)=>v+state.camera.target[i]*camera.extent);
    Object.assign(camera,{yaw:state.camera.yaw,pitch:state.camera.pitch,zoom:state.camera.zoom});
    return {width,height,camera};
  }
  function serialize(controller, parts, width, height) {
    const data={format:'dental-editorial-script',version:2,source:SOURCE,
      labels:C.LABELS,offsets:C.OFFSETS,presentation:PRESENTATION,
      viewState:controller.view(),recordedView:recordedView(parts,width,height,controller.view()),timeline:controller.timeline(),
      state:controller.snapshot(),position:controller.playback().position};
    // Save committed controller state, never wall-clock anchors or auto-play authority.
    return JSON.stringify(data,null,2)+'\n';
  }
  function load(text, parts, clock) {
    if(typeof text!=='string'||text.length>1048576) throw Error('Script must be JSON text under 1 MiB.');
    const data=JSON.parse(text);
    const keys=['format','version','source','labels','offsets','presentation','recordedView','timeline','state','position'];
    if(data && data.version===2) keys.push('viewState');
    if(!data||!equal(Object.keys(data).sort(),keys.sort())||data.format!=='dental-editorial-script'||![1,2].includes(data.version)) throw Error('Unsupported script format.');
    const viewState=data.version===1?clone(VIEW_DEFAULT):validateView(data.viewState);
    if(!equal(data.source,SOURCE)||!equal(data.labels,C.LABELS)||!equal(data.offsets,C.OFFSETS)||!equal(data.presentation,PRESENTATION)) throw Error('Script source or fixed presentation mismatch.');
    const view=data.recordedView;
    if(!view||!equal(view,recordedView(parts,view.width,view.height,viewState))) throw Error('Recorded camera/target mismatch.');
    if(!data.state||!equal(Object.keys(data.state).sort(),['isolate','reveal'])) throw Error('Invalid script state.');
    // Validate everything on a new controller before a caller replaces its live one.
    const controller=fresh(parts,clock);
    if(!Array.isArray(data.timeline)||data.timeline.some(frame=>!frame||!equal(Object.keys(frame).sort(),['isolate','reveal','time']))) throw Error('Unsupported keyframe fields.');
    controller.setTimeline(data.timeline);
    controller.editView(viewState);
    controller.scrub(data.position);
    controller.dispatch({type:'reveal',value:data.state.reveal});
    controller.dispatch(data.state.isolate===null?{type:'all'}:{type:'isolate',label:data.state.isolate});
    return controller;
  }
  return Object.freeze({SOURCE,PRESENTATION,VIEW_DEFAULT,SHOT,fresh,recordedView,serialize,load,validateView});
});
