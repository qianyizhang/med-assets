export { chapters } from './playable-chapters.js';
import {
  add, cross, dot, landmarks, mul, patientEnvelope, probeContact, sampler, sub, unit, volumeFor,
} from './playable-model.js';

const paper = '#e3ecef';
const muted = '#aac1cb';
const marker = '#f0cc7f';
const teal = '#a9dfda';
const contexts = new Map();
const buffers = new WeakMap();
const baseNames = {
  maternal_bladder: 13, fetal_bladder: 17, amniotic_fluid: 11, amniotic_cavity: 11,
  uterus: 68, placenta: 91, cervix: 55, cervical_canal: 31, cord: 109, umbilical_cord: 106,
  fetus: 82, embryo: 118, cardiac_region: 103, gestational_sac: 11, gestational_rim: 146,
  amnion: 147, yolk_sac: 181, calvarium: 205, nasal_bone: 229, spine: 203, spinal_echoes: 203,
  hands: 206, feet: 199, femur: 218, falx: 198, ventricles: 29, choroid: 170,
  choroid_plexus: 180, cavum: 29, thalami: 105, cerebellum: 133, cisterna_magna: 18,
  orbits: 25, upper_lip: 146, nares: 29, lungs: 108, heart: 76, diaphragm: 177,
  stomach: 14, kidneys: 123, renal_pelves: 29,
  right_atrium: 28, left_atrium: 31, right_ventricle: 28, left_ventricle: 29,
  aortic_outflow: 30, pulmonary_outflow: 31, superior_vena_cava: 25,
  trachea: 35, umbilical_vein: 39, umbilical_arteries: 43,
  'adnexal follicles': 16, ovary: 94, 'tubal sac': 13, 'tubal wall': 187,
  'ectopic yolk sac': 215, 'cul-de-sac fluid': 9, 'NT space': 10,
  'posterior skin': 223, 'amnion fold': 183, 'abdominal skin': 215,
  'calvarial contour': 219, 'ossified shaft': 229, 'abdominal wall defect': 18,
  'sac contents': 130, 'sac membrane': 196, 'nearest fluid': 10, 'maternal interface': 210,
  'forearm / lower-leg bones': 218, 'model heart': 36, 'first stomach': 12,
};
const labelNames = {
  right_atrium:'RA',left_atrium:'LA',right_ventricle:'RV',left_ventricle:'LV',
  aortic_outflow:'Aortic outflow',pulmonary_outflow:'Pulmonary outflow',superior_vena_cava:'SVC',
  cavum:'Cavum septi pellucidi', amniotic_fluid:'Amniotic cavity', amniotic_cavity:'Amniotic cavity',
  gestational_rim:'Gestational sac rim', 'first stomach':'Stomach', cardiac_region:'Cardiac interface',
  'tubal sac':'Tubal sac fluid', 'tubal wall':'Tubal sac rim', 'ectopic yolk sac':'Ectopic yolk-sac rim',
  'nearest fluid':'Amniotic fluid pocket', 'model heart':'Fetal heart', 'maternal interface':'Fluid pocket boundary',
};
const cap = name => {
  const t=labelNames[name] ?? name.replaceAll('_',' ');
  return t[0].toUpperCase()+t.slice(1);
};

const palette = [
  '#53cdd9','#bd9af2','#efae66','#6cda91','#f18fa9','#7eaff2','#d6df6d','#e07483',
  '#59d6bd','#efa37e','#abacef','#89bf83','#d997da','#90df9c','#e7c867','#6dbad8',
];
const anatomyColors = {
  uterus:'#df95b3', placenta:'#c5a1f1', fetus:'#e5bc7b', cord:'#5fdaa9', umbilical_cord:'#5fdaa9',
  amniotic_fluid:'#67b7e7', amniotic_cavity:'#67b7e7',
  'tubal sac':'#70adf0', 'tubal wall':'#ef9c78', 'ectopic yolk sac':'#d7e572',
  'NT space':'#60cce8', 'posterior skin':'#f2af74', 'amnion fold':'#bda1eb',
  'abdominal wall defect':'#82b1e8', 'sac contents':'#e2dd79', 'sac membrane':'#f698af',
  'nearest fluid':'#5bc7e2', 'maternal interface':'#e5d67b', 'calvarial contour':'#eedb82',
  right_atrium:'#6eaafa', left_atrium:'#a9db72', right_ventricle:'#5bdeca', left_ventricle:'#efab75',
  aortic_outflow:'#f38d97', pulmonary_outflow:'#6de3ca', trachea:'#d8df7e', superior_vena_cava:'#b9a0f2',
};
function overlayColor(name) {
  const label=cap(name);
  const index=[...label].reduce((total,letter)=>(total*31+letter.charCodeAt(0))>>>0,0)%palette.length;
  const color=anatomyColors[name]??palette[index];
  return {label,color,rgb:color.slice(1).match(/../g).map(value=>parseInt(value,16))};
}


function caseModel(chapter) {
  const key = chapter.stage+'-'+chapter.kind;
  if (!contexts.has(key)) {
    const l = landmarks(chapter.stage,chapter.kind);
    const model = sampler(chapter.stage,chapter.kind,l);
    contexts.set(key,{
      ...model, l, tones:model.names.map(name=>name===null?26:baseNames[name] ?? 56),
      overlay:model.names.map(name=>name===null?null:overlayColor(name)),
    });
  }
  return contexts.get(key);
}

export function planeAt(chapter,frame) {
  const phase = chapter.signal
    ? Math.min(1,frame/Math.max(1,Math.floor(chapter.frames*.26)))
    : frame/(chapter.frames-1);
  const travel = chapter.signal ? phase-1 : 2*phase-1;
  const arc = chapter.signal ? .12 : .28;
  const nominalBeam = unit(chapter.beam);
  const nominalWidth = unit(sub(chapter.width,mul(nominalBeam,dot(chapter.width,nominalBeam))));
  const nominalNormal = unit(cross(nominalWidth,nominalBeam));
  const range = chapter.sweep ?? (chapter.stage==='early'?14:chapter.stage==='first'?10:19);
  const target = add(chapter.target,add(mul(nominalNormal,travel*range*.5),
    mul(nominalWidth,Math.abs(travel)*range*.19)));
  const aimed = unit(add(nominalBeam,mul(nominalNormal,travel*arc)));
  const contact = probeContact(chapter.stage,target,aimed,chapter.vaginal);
  // Seat the vaginal approach along the central ray from the cervical canal.
  const beam = chapter.vaginal ? unit(sub(target,contact)) : aimed;
  let width = sub(nominalWidth,mul(beam,dot(nominalWidth,beam)));
  if (Math.hypot(...width)<.15) width = cross(nominalNormal,beam);
  width = unit(width);
  return { phase, target, contact, beam, width, normal: unit(cross(width,beam)) };
}

function obscured(chapter,plane,x,y,z) {
  if (!chapter.shadow) return false;
  const h = chapter.shadow;
  const dx=x-h.target[0],dy=y-h.target[1],dz=z-h.target[2];
  const along = dx*plane.beam[0]+dy*plane.beam[1]+dz*plane.beam[2];
  const lateral = dx*plane.width[0]+dy*plane.width[1]+dz*plane.width[2]-h.shift;
  return along > -chapter.span*.30 &&
    Math.abs(lateral) < (h.width+Math.max(0,along)*.19);
}

export function sampleRaster(chapter,frame,columns=280,rows=160) {
  const source = caseModel(chapter);
  const plane = planeAt(chapter,frame);
  const spanX = chapter.span;
  const spanY = chapter.signal || chapter.chart ? spanX*.77 : spanX*.68;
  const stepX = spanX/columns,stepY = spanY/rows;
  const smooth = chapter.id==='first-cord';
  const { target, beam, width } = plane;
  const left = sub(target,mul(width,spanX/2));
  const top = sub(left,mul(beam,spanY/2));
  const movingWall = chapter.signal?.mode === 'M-mode';
  const motion = movingWall ? (sampledTrace(chapter, recordedFraction(chapter,frame))-.51)
    * (chapter.stage==='early'?3.2:8.8) : 0;
  const reach = chapter.stage==='early'?3.1:chapter.stage==='first'?6.0:11;
  const pixels = new Uint8Array(columns*rows);
  const labels = new Uint8Array(pixels.length);
  let position = 0;
  for (let row=0;row<rows;row++) {
    const y0=top[1]+row*beam[1]*stepY;
    const z0=top[2]+row*beam[2]*stepY;
    const x0=top[0]+row*beam[0]*stepY;
    for (let col=0;col<columns;col++,position++) {
      const x=x0+col*width[0]*stepX,y=y0+col*width[1]*stepX,z=z0+col*width[2]*stepX;
      const wall = movingWall ? motion*Math.max(0,1-(
        (x-chapter.target[0])**2+(y-chapter.target[1])**2+(z-chapter.target[2])**2)/reach**2) : 0;
      let tissue=source.scan(x-wall*beam[0],y-wall*beam[1],z-wall*beam[2]);
      const dx=x-plane.contact[0],dy=y-plane.contact[1],dz=z-plane.contact[2];
      const depth=dx*beam[0]+dy*beam[1]+dz*beam[2];
      const across=dx*width[0]+dy*width[1]+dz*width[2];
      const sector=depth>=0 && Math.abs(across)<13+depth*.83;
      if (!sector) continue;
      const shadowed = obscured(chapter,plane,x,y,z);
      if (shadowed) tissue=0;
      labels[position]=tissue;
      const seed = (Math.imul(Math.round(x*5),73856093)^Math.imul(Math.round(y*5),19349663)^Math.imul(Math.round(z*5),83492791)) >>> 0;
      const noise=(seed%997/997)-.5;
      const brightness = shadowed ? 9 : smooth
        ? source.interpolated(x,y,z,source.tones) : source.tones[tissue];
      const shade = shadowed ? noise*7 : noise*(brightness<35?9:30)
        + (!tissue? Math.sin(y*.53+x*.22+z*.15)*5:0);
      const edge = !smooth && row>0 && tissue && labels[position-columns]!==tissue && brightness>40 ? 27 : 0;
      pixels[position] = Math.max(4,Math.min(255,brightness+shade+edge));
    }
  }
  return { columns,rows,spanX,spanY,pixels,labels,plane };
}

function text(ctx,content,x,y,colour=paper,font='16px system-ui,sans-serif') {
  ctx.fillStyle=colour;
  ctx.font=font;
  ctx.fillText(content,x,y);
}

function stroke(ctx,a,b,colour=teal,width=1.5) {
  ctx.strokeStyle=colour;
  ctx.lineWidth=width;
  ctx.beginPath();
  ctx.moveTo(...a);
  ctx.lineTo(...b);
  ctx.stroke();
}

function dotAt(ctx,x,y,radius,colour) {
  ctx.fillStyle=colour;
  ctx.beginPath();
  ctx.arc(x,y,radius,0,2*Math.PI);
  ctx.fill();
}

// Both images use the same scalar samples, visibility mask and crop. Only the
// displayed RGB changes when an anatomy label is present.
export function paintRaster(chapter,raster,data,overlay) {
  const source=caseModel(chapter);
  const visible=new Set();
  for (let i=0;i<raster.pixels.length;i++) {
    const channel=raster.pixels[i];
    const tissue=overlay?source.overlay[raster.labels[i]]:null;
    const red=Math.round(channel*.94), blue=Math.min(255,channel+Math.ceil(channel*.047));
    if (tissue) {
      const [r,g,b]=tissue.rgb;
      const gain=.18+.72*channel/255;
      data[i*4]=Math.round(red*.53+r*gain*.47);
      data[i*4+1]=Math.round(channel*.53+g*gain*.47);
      data[i*4+2]=Math.round(blue*.53+b*gain*.47);
      visible.add(raster.labels[i]);
    } else {
      data[i*4]=red;
      data[i*4+1]=channel;
      data[i*4+2]=blue;
    }
    data[i*4+3]=255;
  }
  const highlighted=(chapter.labels??[]).map(name=>source.ids[name]).filter(id=>visible.has(id));
  const ordered=new Set([...highlighted,...visible]);
  return [...ordered].map(id=>{
    const {label,color}=source.overlay[id];
    return {label,color};
  }).filter((item,index,all)=>all.findIndex(other=>other.label===item.label)===index);
}

function rasterToCanvas(ctx,chapter,raster,box,overlay) {
  if (!buffers.has(ctx)) {
    const canvas = ctx.canvas.ownerDocument.createElement('canvas');
    canvas.width=raster.columns;
    canvas.height=raster.rows;
    const buffer=canvas.getContext('2d');
    buffers.set(ctx,{canvas,buffer,rgba:buffer.createImageData(raster.columns,raster.rows)});
  }
  const {canvas,buffer,rgba}=buffers.get(ctx);
  const legend=paintRaster(chapter,raster,rgba.data,overlay);
  buffer.putImageData(rgba,0,0);
  ctx.drawImage(canvas,box.x,box.y,box.w,box.h);
  return legend;
}

function projector(raster,box) {
  const {plane,spanX,spanY}=raster;
  return point => {
    const delta=sub(point,plane.target);
    return [box.x+box.w*(.5+dot(delta,plane.width)/spanX),
      box.y+box.h*(.5+dot(delta,plane.beam)/spanY)];
  };
}

export function landmarkAnchors(chapter,raster) {
  const source=caseModel(chapter);
  const wanted=(chapter.labels??[]).map(name=>({name,id:source.ids[name],n:0,x:0,y:0}));
  const lookup=Object.fromEntries(wanted.filter(entry=>entry.id).map(entry=>[entry.id,entry]));
  for (let row=0;row<raster.rows;row++) for (let col=0;col<raster.columns;col++) {
    const entry=lookup[raster.labels[row*raster.columns+col]];
    if (!entry) continue;
    entry.n++;
    entry.x+=col;
    entry.y+=row;
  }
  const seen=wanted.filter(entry=>entry.n>5);
  for (const entry of seen) {
    entry.meanX=entry.x/entry.n;
    entry.meanY=entry.y/entry.n;
    entry.distance=Infinity;
  }
  // A centroid of a ring or two separated structures can lie in a void.
  // Put the leader at the nearest actual pixel for that tissue class.
  for (let row=0;row<raster.rows;row++) for (let col=0;col<raster.columns;col++) {
    const entry=lookup[raster.labels[row*raster.columns+col]];
    if (!entry?.n || entry.n<=5) continue;
    const distance=(col-entry.meanX)**2+(row-entry.meanY)**2;
    if(distance>=entry.distance) continue;
    entry.x=col;
    entry.y=row;
    entry.distance=distance;
  }
  return seen;
}

function annotate(ctx,chapter,raster,box) {
  const visible=landmarkAnchors(chapter,raster);
  visible.forEach((entry,i)=>{
    const x=box.x+entry.x/raster.columns*box.w,y=box.y+entry.y/raster.rows*box.h;
    const right=i%2===0;
    const tagX=right?box.x+box.w+14:10;
    const tagY=box.y+47+Math.floor(i/2)*64;
    const stem=right?tagX-9:box.x-7;
    stroke(ctx,[x,y],[stem,tagY-4],'#8ad1d0',1);
    dotAt(ctx,x,y,2.4,'#b9efec');
    ctx.font='14px system-ui,sans-serif';
    const words=cap(entry.name).split(' ');
    let line='', offset=0;
    for (const word of words) {
      const trial=line?line+' '+word:word;
      if (ctx.measureText(trial).width>112 && line) {
        text(ctx,line,tagX,tagY+offset,teal,'14px system-ui,sans-serif');
        line=word;
        offset+=15;
      } else line=trial;
    }
    text(ctx,line,tagX,tagY+offset,teal,'14px system-ui,sans-serif');
  });
}

function drawMeasurements(ctx,chapter,raster,box) {
  let set=chapter.measure;
  if (!set) return;
  if (!Array.isArray(set)) set=[set];
  const project=projector(raster,box);
  for (const [index,measure] of set.entries()) {
    if (measure.type==='line') {
      const a=project(measure.a),b=project(measure.b);
      stroke(ctx,a,b,marker,1.4);
      for (const [x,y] of [a,b]) {
        stroke(ctx,[x-5,y],[x+5,y],marker);
        stroke(ctx,[x,y-5],[x,y+5],marker);
      }
    } else if (measure.type==='ellipse') {
      ctx.beginPath();
      for (let i=0;i<=64;i++) {
        const angle=i/64*2*Math.PI;
        const [x,y]=project(add(measure.centre,[measure.radii[0]*Math.cos(angle),measure.radii[1]*Math.sin(angle),0]));
        if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
      }
      ctx.strokeStyle=marker;
      ctx.lineWidth=1.3;
      ctx.stroke();
    }
    text(ctx,measure.label,box.x+12,box.y+box.h-14-index*23,marker);
  }
}

function scaleBar(ctx,box,raster) {
  const interval=raster.spanX>110?20:raster.spanX>65?10:5;
  const length=interval/raster.spanX*box.w;
  const x=box.x+box.w-length-12,y=box.y+box.h-18;
  stroke(ctx,[x,y],[x+length,y],paper,2);
  stroke(ctx,[x,y-4],[x,y+4],paper,2);
  stroke(ctx,[x+length,y-4],[x+length,y+4],paper,2);
  text(ctx,`${interval} mm`,x,y-8,paper,'13px system-ui,sans-serif');
}

function recordedFraction(chapter,frame) {
  const first=Math.floor(chapter.frames*.26);
  return Math.max(0,(frame-first)/(chapter.frames-1-first));
}

export function sampledTrace(chapter,t) {
  const { mode, cycles, peak, edv, interrupted }=chapter.signal;
  const phase=(t*cycles)%1;
  if (mode==='M-mode') {
    return .51-.24*Math.cos(phase*2*Math.PI)+.055*Math.sin(phase*4*Math.PI);
  }
  if (interrupted && (phase>.62 || (t>.30 && t<.41))) return null;
  // A rapid upstroke and smooth diastolic decay of the sampled envelope.
  const rise=.14;
  const f=phase<rise ? Math.sin(phase/rise*Math.PI/2)
    : ((1-phase)/(1-rise))**2.3;
  return edv+(peak-edv)*f;
}

function signalPanel(ctx,chapter,frame,raster,box) {
  const mapped=projector(raster,box);
  const [x,y]=mapped(chapter.target);
  stroke(ctx,[x,box.y+8],[x,box.y+box.h-9],teal,1);
  stroke(ctx,[x-7,y-6],[x+7,y-6],marker,2);
  stroke(ctx,[x-7,y+6],[x+7,y+6],marker,2);
  text(ctx,chapter.signal.mode==='M-mode'?'M-line':'Sample gate',box.x+12,box.y+24,teal);
  const left=468,right=763,top=91,bottom=338;
  const s=chapter.signal;
  const bmode=s.mode==='M-mode';
  text(ctx,s.mode,left,73,teal,'bold 16px system-ui,sans-serif');
  text(ctx,bmode?'Depth':'cm/s',left-1,105,muted,'13px system-ui,sans-serif');
  for (let i=0;i<=4;i++) {
    const yy=top+i*(bottom-top)/4;
    stroke(ctx,[left,yy],[right,yy],i===4?'#bbcacc':'#32454e',1);
    if (!bmode) text(ctx,String(60-i*15),left-24,yy+4,muted,'12px system-ui,sans-serif');
  }
  stroke(ctx,[left,top],[left,bottom],'#a3b8bd',1);
  const max=recordedFraction(chapter,frame);
  const step=1/300;
  for (let i=0;i<=s.cycles;i++) {
    const xx=left+(right-left)*i/s.cycles;
    stroke(ctx,[xx,top+4],[xx,bottom],i===0||i===s.cycles?'#52656c':'#334950',1);
  }
  let previous=null;
  for (let i=0;i<=Math.round(300*max);i++) {
    const t=i*step;
    const value=sampledTrace(chapter,t);
    if (value===null) {
      previous=null;
      continue;
    }
    const yy=bmode?top+(bottom-top)*value:bottom-(bottom-top)*value/60;
    const xx=left+(right-left)*t;
    if (!bmode) {
      stroke(ctx,[xx,bottom],[xx,yy],'#668397',1.25);
      if (i%4===0) dotAt(ctx,xx,yy+(i%9),1.2,'#b0c8d2');
    } else {
      stroke(ctx,[xx,top+28],[xx,top+28],'#607079',2);
      stroke(ctx,[xx,yy+15],[xx,yy+21],'#677985',1.2);
    }
    if (previous) stroke(ctx,previous,[xx,yy],bmode?'#eceff4':'#a7dbe7',2);
    previous=[xx,yy];
  }
  text(ctx,'0 s',left,bottom+24,muted,'13px system-ui,sans-serif');
  text(ctx,`${s.seconds.toFixed(2)} s`,right-43,bottom+24,muted,'13px system-ui,sans-serif');
  if (frame===chapter.evidenceFrame) text(ctx,bmode?`${s.cycles} cardiac cycles`
    :s.interrupted?'End-diastolic envelope obscured'
    :`PSV ${s.peak} cm/s   EDV ${s.edv} cm/s`,left,bottom+51,marker);
}

function growthChart(ctx,chapter) {
  const data=chapter.growth;
  const x1=507,x2=688;
  const y=weight=>350-(weight-800)*.19;
  text(ctx,'Estimated fetal weight',466,83,teal,'bold 16px system-ui,sans-serif');
  text(ctx,'Hadlock 1991 centiles',466,105,muted);
  for (const [w28,w32,name] of [[908,1465,'3rd'],[1004,1621,'10th'],[1210,1953,'50th'],[1416,2285,'90th']]) {
    stroke(ctx,[x1,y(w28)],[x2,y(w32)],'#556f7a',1.3);
    text(ctx,name,x2+13,y(w32)+4,muted,'14px system-ui,sans-serif');
  }
  dotAt(ctx,x1,y(data[0]),5,marker);
  text(ctx,`${data[0]} g`,x1-22,y(data[0])-13,marker,'13px system-ui,sans-serif');
  if (data[1]===null) text(ctx,'Current weight withheld',x2-122,206,marker,'14px system-ui,sans-serif');
  else {
    stroke(ctx,[x1,y(data[0])],[x2,y(data[1])],marker,2);
    dotAt(ctx,x2,y(data[1]),5,marker);
    text(ctx,`${data[1]} g`,x2-48,y(data[1])-16,marker,'13px system-ui,sans-serif');
  }
  text(ctx,'28 weeks',x1-18,380,paper,'14px system-ui,sans-serif');
  text(ctx,'32 weeks',x2-18,380,paper,'14px system-ui,sans-serif');
}

export function render(ctx,chapter,frame,_record,{overlay=false}={}) {
  ctx.fillStyle='#070c12';
  ctx.fillRect(0,0,800,440);
  const raster=sampleRaster(chapter,frame);
  const dual=chapter.signal||chapter.chart;
  const box=dual?{x:24,y:59,w:393,h:314}:{x:128,y:53,w:544,h:352};
  ctx.save();
  const legend=rasterToCanvas(ctx,chapter,raster,box,overlay);
  scaleBar(ctx,box,raster);
  if (chapter.signal) signalPanel(ctx,chapter,frame,raster,box);
  else if (chapter.chart) growthChart(ctx,chapter);
  else {
    annotate(ctx,chapter,raster,box);
    if (frame===chapter.evidenceFrame) drawMeasurements(ctx,chapter,raster,box);
  }
  ctx.restore();
  const mode=chapter.vaginal?'TRANSVAGINAL':'TRANSABDOMINAL';
  text(ctx,`${mode}  /  ${chapter.name}`,24,32,teal,'bold 15px system-ui,sans-serif');
  text(ctx,overlay?'MODELED ANATOMY OVERLAY':'MODELED ACQUISITION',593,32,muted,'13px system-ui,sans-serif');
  if (chapter.shadow) text(ctx,'Acoustic shadow across the sampled field',131,426,marker,'14px system-ui,sans-serif');
  return legend;
}

export function locatorProject(stage,yaw=0) {
  const {centre,radii}=patientEnvelope(stage);
  const field=Math.max(radii[0]*2.4,radii[2]*2.35);
  const axis=unit(volumeFor(stage).axes?.[2]??[0,0,1]);
  const c=Math.cos(yaw),s=Math.sin(yaw);
  return point=>{
    const delta=sub(point,centre);
    const [x,y,z]=add(add(mul(delta,c),mul(cross(axis,delta),s)),mul(axis,dot(axis,delta)*(1-c)));
    return [198+(x*.91+y*.56)*205/field,151+(-z+x*.18-y*.20)*217/field];
  };
}

export function projectedShell(stage,project) {
  const {centre,radii}=patientEnvelope(stage);
  const origin=project(centre);
  const vectors=radii.map((radius,i)=>
    project(centre.map((n,j)=>n+(i===j?radius:0))).map((n,j)=>n-origin[j]));
  const xx=vectors.reduce((sum,[x])=>sum+x*x,0);
  const yy=vectors.reduce((sum,[,y])=>sum+y*y,0);
  const xy=vectors.reduce((sum,[x,y])=>sum+x*y,0);
  const discriminant=Math.hypot(xx-yy,2*xy);
  return {
    origin, radii:[Math.sqrt((xx+yy+discriminant)/2),Math.sqrt((xx+yy-discriminant)/2)],
    rotation:.5*Math.atan2(2*xy,xx-yy),
  };
}

const poseCache=new WeakMap();
function drawSilhouette(ctx,chapter,project) {
  const model=caseModel(chapter);
  let points=poseCache.get(model);
  if (!points) {
    const {centre,radii}=patientEnvelope(chapter.stage);
    const target=model.l;
    const fetal=[
      model.ids.fetus,model.ids.embryo,model.ids.spine,model.ids.calvarium,
      model.ids['calvarial contour'],model.ids['abdominal skin'],model.ids['ossified shaft'],
      model.ids.ovary,model.ids['tubal wall'],model.ids.gestational_rim,
    ];
    const access=[
      model.ids.uterus,model.ids.placenta,model.ids.cervical_canal,model.ids.maternal_bladder,
    ];
    const granularity=chapter.stage==='early'?4:chapter.stage==='first'?5:9;
    points=[];
    for(let z=centre[2]-radii[2];z<centre[2]+radii[2];z+=granularity) {
      for(let x=-radii[0];x<=radii[0];x+=granularity) for(let y=centre[1]-radii[1];y<centre[1]+radii[1];y+=granularity) {
        const tissue=model.scan(x,y,z);
        if(fetal.includes(tissue)) points.push([x,y,z,'#27919d']);
        if(access.includes(tissue)) points.push([x,y,z,'#53476c']);
      }
    }
    if (chapter.stage==='early'&&chapter.kind==='abnormal') points.push([...(target.ectopic),'#e8b778']);
    poseCache.set(model,points);
  }
  for(const [x,y,z,colour] of points) {
    const p=project([x,y,z]);
    ctx.fillStyle=colour;
    ctx.fillRect(p[0],p[1],2,2);
  }
}

export function pose(ctx,chapter,frame,_record,{yaw=0}={}) {
  ctx.fillStyle='#071821';
  ctx.fillRect(0,0,400,300);
  const plane=planeAt(chapter,frame);
  const project=locatorProject(chapter.stage,yaw);
  const shell=projectedShell(chapter.stage,project);
  ctx.strokeStyle='#49606a';
  ctx.fillStyle='#11222c';
  ctx.lineWidth=1.5;
  ctx.beginPath();
  ctx.ellipse(...shell.origin,...shell.radii,shell.rotation,0,2*Math.PI);
  ctx.fill();
  ctx.stroke();
  drawSilhouette(ctx,chapter,project);
  const {target,contact,width,beam}=plane;
  const crop=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>project(add(add(target,mul(width,a*chapter.span/2)),
    mul(beam,b*chapter.span*((chapter.signal || chapter.chart ? .77 : .68))/2))));
  const head=project(contact);
  ctx.beginPath();
  ctx.moveTo(...head);
  ctx.lineTo(...crop[2]);
  ctx.lineTo(...crop[3]);
  ctx.closePath();
  ctx.fillStyle='#78a4d231';
  ctx.fill();
  for (let i=0;i<crop.length;i++) stroke(ctx,crop[i],crop[(i+1)%crop.length],'#9ccbe3',1.3);
  const centreBeam=project(target);
  stroke(ctx,head,centreBeam,'#b6cae5',1.7);
  const footprint=mul(width,chapter.vaginal?8:13);
  stroke(ctx,project(sub(contact,footprint)),project(add(contact,footprint)),marker,5);
  dotAt(ctx,...centreBeam,3,teal);
  text(ctx,chapter.vaginal?'Vaginal approach':'External probe',16,28,marker,'bold 14px system-ui,sans-serif');
  text(ctx,'Fetal / adnexal anatomy',16,258,'#83c8cb','14px system-ui,sans-serif');
  text(ctx,'Imaging plane and sample crop',16,279,'#b0c6eb','14px system-ui,sans-serif');
}
