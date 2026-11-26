import {cut, endpoints, plane, sectionContour} from './playable-geometry.js';

const W = 800;
const H = 440;
const C = 396;
const TOP = 48;
const labels = '#96e6c8';
const amber = '#ffd37c';
const palette = ['#ff9c93','#ffc27c','#d4da86','#71dec0','#93baff','#d2a5ee','#eda8c5','#73d5ee','#b7d58a'];

const namedColors = {
  'Solid hypoechoic nodule':'#f889a9',
  'Anechoic simple cyst':'#78e6cc',
  'Mobile calculus':'#fff1a1',
  'Dilated renal pelvis':'#64d3f6',
  'Upper calyx':'#75c8ff',
  'Lower calyx':'#85e2e8',
  'Bowel gas':'#e5e8ea',
  'Pancreatic head':'#eab296',
  'Pancreatic body':'#edc079',
  'Pancreatic tail':'#e3d395',
  'Gallbladder wall':'#eda8c5',
  'Gallbladder lumen':'#89d7c0',
  'Fibroglandular tissue':'#d2a5ee',
  'Chest wall':'#81a8cb',
  'Retromammary fat':'#eab274',
  'Pectoral fascia':'#d6e3ed',
};

function tissueColor(id) {
  if (namedColors[id]) return namedColors[id];
  let index = 0;
  for (const letter of id) index = (index * 31 + letter.charCodeAt(0)) >>> 0;
  return palette[index % palette.length];
}

function tint(gray, color) {
  const weight = .58;
  const channels = [1,3,5].map(start => parseInt(color.slice(start,start+2),16));
  return `rgb(${channels.map(value=>Math.round(gray*(1-weight)+value*weight)).join(',')})`;
}

function inAcousticField(x,y,chapter,sc) {
  const u = Math.abs(x*sc.scale), v = y*sc.scale;
  if (v<0 || u>sc.half) return false;
  if (chapter.linear) return v<=sc.height;
  const edge = 62+(sc.half-62)*Math.min(1,v/(sc.height-21));
  return u<=edge && v<=sc.height-21*(u/sc.half)**2;
}

function contains(section,x,y) {
  if (section.spanAt) {
    if (Math.abs(x-section.x)>section.w) return false;
    const [front,back]=section.spanAt(x);
    return y>=front&&y<=back;
  }
  return ((x-section.x)/section.w)**2 + ((y-section.y)/section.h)**2 <= 1;
}

function inDeepShadow(x,y,entry,chapter) {
  const {shape,section}=entry;
  if (!(shape.shadow>.7 && y>section.y && y<=chapter.depth)) return false;
  const half = section.w*(.92+.40*(y-section.y)/(chapter.depth-section.y));
  return Math.abs(section.x-x)<half;
}

// Pick an anchor on pixels that this contour owns after painter-order clipping and attenuation.
function visibleSections(shapes,chapter,sc) {
  return shapes.flatMap((entry,index)=>{
    const {section,shape}=entry;
    const other=shapes.slice(index+1);
    const point = (x,y) => {
      if (!contains(section,x,y) || !inAcousticField(x,y,chapter,sc) || other.some(({section: layer})=>contains(layer,x,y))
          || shapes.some(blocker=>blocker!==entry && inDeepShadow(x,y,blocker,chapter))) return null;
      return {shape,section,x,y,color:tissueColor(shape.id)};
    };
    const center=point(section.x,section.y);
    if(center) return [center];
    for (const radial of [.55,.80,.93,.985]) {
      for (let step=0;step<24;step++) {
        const angle=Math.PI*(step/12-0.5);
        const anchor=point(section.x+section.w*radial*Math.cos(angle),
          section.y+section.h*radial*Math.sin(angle));
        if(anchor) return [anchor];
      }
    }
    return [];
  });
}

const line = (ctx,x1,y1,x2,y2) => {
  ctx.beginPath();
  ctx.moveTo(x1,y1);
  ctx.lineTo(x2,y2);
  ctx.stroke();
};
const text = (ctx, value, x, y, color='#c7d0d5', size=14) => {
  ctx.fillStyle = color;
  ctx.font = `${size}px system-ui, sans-serif`;
  ctx.fillText(value,x,y);
};
function ellipse(ctx,x,y,rx,ry) {
  ctx.beginPath();
  ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);
}
function sectionPath(ctx,section,sc) {
  const {x,y,w,h,spanAt}=section;
  if (!spanAt) {
    ellipse(ctx,sc.x(x),sc.y(y),sc.scale*w,sc.scale*h);
    return;
  }
  ctx.beginPath();
  for (const [i,[lateral,depth]] of sectionContour(section).entries()) {
    if (i===0) ctx.moveTo(sc.x(lateral),sc.y(depth));
    else ctx.lineTo(sc.x(lateral),sc.y(depth));
  }
  ctx.closePath();
}

function layout(chapter) {
  const height = chapter.spectral ? 242 : 365;
  const scale = height/chapter.depth;
  const half = chapter.linear
    ? Math.min(335, (chapter.aperture ?? (chapter.depth < 50 ? 66 : 105))*scale/2)
    : 322;
  return {height, scale, half, x:mm=>C+mm*scale, y:mm=>TOP+mm*scale};
}

function background(ctx, chamber, shape) {
  const g = ctx.createLinearGradient(0,TOP,0,TOP+shape.height);
  g.addColorStop(0,chamber.linear?'#4b4e4b':'#686b65');
  g.addColorStop(.41,'#393c38');
  g.addColorStop(1,'#1c201e');
  ctx.fillStyle = g;
  ctx.fillRect(52,TOP,689,shape.height);
  ctx.strokeStyle = 'rgba(211,216,209,.24)';
  ctx.lineWidth = 2;
  for (let i = 0; i < 3; ++i) {
    ctx.beginPath();
    ctx.moveTo(C-shape.half,TOP+6+i*5);
    ctx.quadraticCurveTo(C,TOP+15+i*8,C+shape.half,TOP+6+i*5);
    ctx.stroke();
  }
}

function acousticField(ctx, chapter, sc) {
  ctx.beginPath();
  if (chapter.linear) {
    ctx.rect(C-sc.half,TOP,sc.half*2,sc.height);
  } else {
    // A finite curvilinear footprint and diverging outer beams.
    ctx.moveTo(C-62,TOP);
    ctx.lineTo(C+62,TOP);
    ctx.lineTo(C+sc.half,TOP+sc.height-21);
    ctx.quadraticCurveTo(C,TOP+sc.height+21,C-sc.half,TOP+sc.height-21);
    ctx.closePath();
  }
}

function shadow(ctx, section, sc, strength, enhance=false) {
  const cx = sc.x(section.x), half = sc.scale*section.w;
  const y = sc.y(enhance ? (section.spanAt?.(section.x)[1] ?? section.y+section.h) : section.y);
  const spread = enhance ? half : half*1.32;
  const deep = TOP+sc.height;
  // Attenuation is applied after all tissue, so it removes information in deeper structures.
  ctx.fillStyle = enhance ? `rgba(216,216,204,${strength})` : `rgba(4,7,8,${strength})`;
  ctx.beginPath();
  ctx.moveTo(cx-half*.92,y);
  ctx.lineTo(cx+half*.92,y);
  ctx.lineTo(cx+spread,deep);
  ctx.lineTo(cx-spread,deep);
  ctx.closePath();
  ctx.fill();
}

function scatter(ctx, sc, level) {
  // World-locked deterministic speckle. The integer depth level selects the sampled texture.
  let state = (Math.round(level*5) + 8192) >>> 0;
  for (let tone=0; tone<4; tone++) {
    ctx.fillStyle = ['rgba(3,4,5,.22)','rgba(238,240,226,.21)',
      'rgba(235,241,229,.1)','rgba(4,7,5,.28)'][tone];
    for (let i=0;i<805;i++) {
      state=(1664525*state+1013904223)>>>0;
      const x=C-sc.half+state/4294967296*2*sc.half;
      state=(1664525*state+1013904223)>>>0;
      const y=TOP+state/4294967296*sc.height;
      ctx.fillRect(x,y,.7+state%4,.6+state%3*.50);
    }
  }
}

function spectrum(ctx, kind, frame, frames) {
  const left = 135, right = 670, top = 309, height = 92, baseline = 375;
  ctx.fillStyle='#141c22';
  ctx.fillRect(left,top,right-left,height);
  ctx.strokeStyle='#829299';
  line(ctx,left,baseline,right,baseline);
  text(ctx,'Illustrative spectral trace',left+10,top+17,'#a8c5c3',12);
  text(ctx,'Time',right-38,top+height-8,'#a8c5c3',11);
  const step = right-left;
  const limit = left+step*(frame+1)/frames;
  ctx.strokeStyle='#eee4c5';
  ctx.lineWidth=2;
  ctx.beginPath();
  ctx.moveTo(left,baseline);
  for(let x=left+1;x<limit;x++) {
    const phase = ((x-left)/step)*Math.PI*8;
    const y = kind === 'portal' ? 23 + 4*Math.sin(phase) : 18+16*Math.sin(phase)+12*Math.sin(2*phase);
    ctx.lineTo(x,baseline-y);
  }
  ctx.stroke();
}

function callouts(ctx, visible, sc, chapter, overlay) {
  const priority = item => {
    const {shape,section} = item;
    return Number(chapter.marks?.some(mark=>mark.id===shape.id) || false)*90 +
      Number(Boolean(shape.shadow>.7 || shape.enhance || /nodule|calculus|dilated/.test(shape.id.toLowerCase())))*60 +
      Number(chapter.colorIds?.includes(shape.id) || false)*45 +
      Number(chapter.layerLabels?.includes(shape.id) || false)*88 -
      Math.abs(section.x) - Math.abs(section.y-chapter.target[1])*.2;
  };
  const chosen = [...visible].sort((first, second)=>priority(second)-priority(first))
    .filter(({shape}, index, list) => list.findIndex(x=>x.shape.id===shape.id)===index).slice(0,3);
  ctx.lineWidth=1;
  for (let i=0;i<chosen.length;i++) {
    const item=chosen[i];
    const {shape}=item;
    const px=sc.x(item.x), py=sc.y(item.y);
    const color=overlay ? item.color : labels;
    const x = i===0 || i===2 ? 84 : 530;
    const y = chapter.spectral ? 83+i*60 : 88+i*98;
    ctx.strokeStyle=color;
    line(ctx,px,py,x+12,y+4);
    ctx.fillStyle=color;
    ellipse(ctx,px,py,2.5,2.5);
    ctx.fill();
    ctx.font='13px system-ui, sans-serif';
    ctx.fillStyle='rgba(17,23,28,.89)';
    ctx.fillRect(x-5,y-15,ctx.measureText(shape.label ?? shape.id).width+12,21);
    text(ctx,shape.label ?? shape.id,x,y,color,13);
  }
}

function calipers(ctx, chapter, sc, model, slice) {
  ctx.strokeStyle=amber;
  ctx.lineWidth=1.6;
  for (const mark of chapter.marks ?? []) {
    const pair = endpoints(model,slice,mark);
    if (!pair?.every(point=>point.every(Number.isFinite))) continue;
    const [[ax,ay],[bx,by]]=pair.map(([x,y])=>[sc.x(x),sc.y(y)]);
    ctx.setLineDash([5,4]);
    line(ctx,ax,ay,bx,by);
    ctx.setLineDash([]);
    for (const [x,y] of [[ax,ay],[bx,by]]) {
      line(ctx,x-5,y,x+5,y);
      line(ctx,x,y-5,x,y+5);
    }
    const length = Math.hypot(pair[0][0]-pair[1][0],pair[0][1]-pair[1][1]);
    const precision = Math.abs(length-Math.round(length)) < .05 ? 0 : 1;
    const str = `${length.toFixed(precision)} mm`;
    const vertical = ax===bx;
    const tx = (ax+bx)/2 + (vertical ? 9 : -22);
    const ty = vertical && Math.abs(ay-by)>25 ? Math.min(ay,by)+14 : (ay+by)/2 - 7;
    ctx.fillStyle='#222729';
    ctx.fillRect(tx-4,ty-13,51,17);
    text(ctx,str,tx,ty,amber,12);
  }
}

export function drawSection(ctx, chapter, frame, model, overlay=false) {
  const slice = plane(chapter,frame), sc = layout(chapter);
  ctx.save();
  ctx.fillStyle='#11191f';
  ctx.fillRect(0,0,W,H);
  text(ctx,'MODELED ULTRASOUND',37,29,'#e1eae9',13);
  text(ctx,`${chapter.linear ? 'Linear' : 'Curvilinear'} · ${chapter.axis===0 ? 'Transverse' : 'Longitudinal'}`,551,29,'#b1c4c8',12);
  const shapes = model.map(shape=>({shape,section:cut(shape,slice)})).filter(item=>item.section);
  const visible=visibleSections(shapes,chapter,sc);
  ctx.save();
  acousticField(ctx,chapter,sc);
  ctx.clip();
  background(ctx,chapter,sc);
  for (const {shape,section} of shapes) {
    const gray = shape.shade;
    const color=tissueColor(shape.id);
    ctx.fillStyle=overlay ? tint(gray,color) : `rgb(${gray},${gray},${Math.max(0,gray-4)})`;
    sectionPath(ctx,section,sc);
    ctx.fill();
    if (gray>30) {
      ctx.strokeStyle=overlay ? color : 'rgba(228,229,211,.28)';
      ctx.lineWidth=1.2;
      ctx.stroke();
    }
  }
  for (const {shape,section} of shapes) {
    if (shape.enhance) shadow(ctx,section,sc,shape.enhance,true);
    if (!chapter.colorIds?.includes(shape.id)) continue;
    const n = Math.sin(frame*.5);
    ctx.fillStyle=shape.flow==='hepatic' || shape.flow==='peripheral' ? '#ea7759' : '#6895ed';
    ellipse(ctx,sc.x(section.x),sc.y(section.y),sc.scale*section.w*(.62+n*.14),sc.scale*section.h*(.54+n*.15));
    ctx.fill();
  }
  scatter(ctx,sc,slice.level);
  for (const {shape,section} of shapes) {
    if (shape.shadow) shadow(ctx,section,sc,shape.shadow);
  }
  ctx.restore();
  ctx.strokeStyle='#748990';
  ctx.lineWidth=1;
  acousticField(ctx,chapter,sc);
  ctx.stroke();
  const tick=chapter.depth>70 ? 20 : 10;
  for(let depth=tick;depth<chapter.depth;depth+=tick) {
    const y=sc.y(depth);
    line(ctx,738,y,746,y);
    text(ctx,String(depth),754,y+4,'#bfd0d1',11);
  }
  text(ctx,'mm',751,52,'#bfd0d1',11);
  if (chapter.spectral) spectrum(ctx,chapter.spectral,frame,chapter.frames);
  callouts(ctx,visible,sc,chapter,overlay);
  if(frame===chapter.evidenceFrame) calipers(ctx,chapter,sc,model,slice);
  ctx.restore();
  if (!overlay) return [];
  const legend = new Map();
  for (const {shape,color} of visible) legend.set(shape.label ?? shape.id,color);
  return [...legend].map(([label,color])=>({label,color}));
}

const maps = {
  abdomen: {scale:.83,centerZ:-20, body:[123,157], regions:['Right upper quadrant','Left upper quadrant']},
  thyroid: {scale:2.35,centerZ:0, body:[47,45], regions:['Right neck','Left neck']},
  breast: {scale:1.22,centerZ:0, body:[137,80], regions:['Right breast','Left breast']},
};

function projectedEllipsoid(ctx, project, shape) {
  const [x,y]=project(...shape.center);
  const origin=project(0,0,0);
  const projected=shape.radii.map((radius,axis)=>{
    const basis=[0,0,0];
    basis[axis]=radius;
    return project(...basis).map((value,i)=>value-origin[i]);
  });
  const xx=projected.reduce((sum,[u])=>sum+u*u,0);
  const xy=projected.reduce((sum,[u,v])=>sum+u*v,0);
  const yy=projected.reduce((sum,[,v])=>sum+v*v,0);
  const discriminant=Math.hypot(xx-yy,2*xy);
  const rotation=.5*Math.atan2(2*xy,xx-yy);
  const major=Math.sqrt((xx+yy+discriminant)/2);
  const minor=Math.sqrt(Math.max(0,(xx+yy-discriminant)/2));
  ctx.beginPath();
  ctx.ellipse(x,y,major,minor,rotation,0,Math.PI*2);
}

export function drawPose(ctx, chapter, frame, record, model, yaw=0) {
  const map=maps[record.family], sc=layout(chapter), slice=plane(chapter,frame);
  const cos=Math.cos(yaw), sin=Math.sin(yaw);
  const project=(x,y,z)=>{
    const lateral=x*cos-y*sin, anterior=x*sin+y*cos;
    return [200+map.scale*(lateral*.9+anterior*.37),
      156+map.scale*(-(z-map.centerZ)*.71+anterior*.32)];
  };
  ctx.save();
  ctx.fillStyle='#161f26';
  ctx.fillRect(0,0,400,300);
  text(ctx,'PROBE AND IMAGING PLANE',18,23,'#e0ebec',12);
  text(ctx,chapter.position ?? 'Supine',18,284,'#c0d5d4',13);
  projectedEllipsoid(ctx,project,{center:[0,22,map.centerZ],radii:[map.body[0],46,map.body[1]]});
  ctx.fillStyle='#233943';
  ctx.fill();
  ctx.strokeStyle='#67888e';
  ctx.stroke();
  text(ctx,map.regions[0],26,49,'#b6c7c7',11);
  text(ctx,map.regions[1],273,49,'#b6c7c7',11);
  const relevant=model.filter(shape=> {
    if (/cyst|calculus|nodule|node|pelvis/i.test(shape.id)) return true;
    return shape.shade>=72 && !/wall|skin|septum|fascia|lumen/i.test(shape.id);
  });
  for (const shape of relevant) {
    projectedEllipsoid(ctx,project,shape);
    ctx.globalAlpha=cut(shape,slice) ? .36 : .14;
    ctx.fillStyle=tissueColor(shape.id);
    ctx.fill();
    ctx.globalAlpha=.54;
    ctx.strokeStyle=tissueColor(shape.id);
    ctx.lineWidth=.6;
    ctx.stroke();
  }
  ctx.globalAlpha=1;
  if (chapter.coverage) {
    ctx.strokeStyle='#749a96';
    ctx.setLineDash([3,5]);
    for (const center of [-53,53]) {
      for (const band of [-35,0,35]) {
        line(ctx,...project(center-60,0,band),...project(center+60,0,band));
      }
    }
    ctx.setLineDash([]);
  }
  const coordinates = (span, depth) => {
    const point=[0,depth,0];
    point[slice.axis]=slice.center+span;
    point[slice.normal]=slice.level;
    return project(...point);
  };
  const deep=(sc.height-(chapter.linear ? 0 : 21))/sc.scale;
  const far=sc.half/sc.scale;
  const near=chapter.linear ? far : 62/sc.scale;
  const vertices=[coordinates(-near,0),coordinates(near,0),coordinates(far,deep),coordinates(-far,deep)];
  ctx.fillStyle='rgba(67,200,180,.23)';
  ctx.strokeStyle='#72d6bd';
  ctx.lineWidth=1.5;
  ctx.beginPath();
  ctx.moveTo(...vertices[0]);
  ctx.lineTo(...vertices[1]);
  ctx.lineTo(...vertices[2]);
  if(chapter.linear) ctx.lineTo(...vertices[3]);
  else ctx.quadraticCurveTo(...coordinates(0,(sc.height+21)/sc.scale),...vertices[3]);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.lineWidth=7;
  ctx.lineCap='round';
  ctx.strokeStyle='#e2e8db';
  line(ctx,...vertices[0],...vertices[1]);
  ctx.lineWidth=1;
  const [tx,ty]=project(...chapter.target);
  ctx.strokeStyle=amber;
  ellipse(ctx,tx,ty,5.5,5.5);
  ctx.stroke();
  const set = chapter.spectral ? ['Sample target','Imaging field'] : ['Anatomical target','Imaging field'];
  text(ctx,set[0],248,246,amber,11);
  text(ctx,set[1],248,263,'#84d9c7',11);
  ctx.restore();
}
