import {breastProfiles} from './playable-breast-profiles.js';

export const tissue = (id, center, radii, shade, options = {}) => ({id, center, radii, shade, ...options});
export const measure = (id, axis, inner = null, lateralOffset = 0) => ({id, axis, inner, lateralOffset});

export function plane(chapter, frame) {
  const {axis, target, sweep, evidenceFrame, frames} = chapter;
  const normal = axis === 0 ? 2 : 0;
  const offset = frame <= evidenceFrame
    ? sweep[0] * (1 - frame / evidenceFrame)
    : sweep[1] * ((frame - evidenceFrame) / (frames - 1 - evidenceFrame));
  return {axis, normal, center: target[axis], level: target[normal] + offset};
}

export function footprintScale(shape, x, z) {
  const profile=breastProfiles[shape.footprint];
  if (!profile) return 1;
  const angle=Math.atan2(z,x*(Math.sign(shape.center[0]) || 1));
  const {radii}=profile;
  const exact=(angle/(2*Math.PI)+1)*radii.length;
  const index=Math.floor(exact);
  const mix=exact-index;
  return (1-mix)*radii[index%radii.length]+mix*radii[(index+1)%radii.length];
}

function footprintValue(shape,u,v) {
  return Math.hypot(u,v)/footprintScale(shape,u,v)-1;
}

function sectionLimits(shape,slice,distance) {
  const slope=offset=>slice.axis===0 ? footprintValue(shape,offset,distance) : footprintValue(shape,distance,offset);
  let lo=null,hi=null;
  const limit=1.4, step=limit/30;
  for (let i=-30;i<=30;i++) {
    const value=i*step;
    if (slope(value)>0) continue;
    if (lo===null) lo=value;
    hi=value;
  }
  if (lo===null) return null;
  const finish=(inside,outside)=>{
    for (let i=0;i<13;i++) {
      const next=(inside+outside)/2;
      if (slope(next)<=0) inside=next;
      else outside=next;
    }
    return inside;
  };
  return [finish(lo,lo-step),finish(hi,hi+step)];
}

function glandDepth(shape,u,v,remaining) {
  const y=shape.center[1], radius=shape.radii[1];
  const model=breastProfiles[shape.footprint].depth;
  const angle=Math.atan2(v,u*(Math.sign(shape.center[0]) || 1));
  const count=model.mid[0].length;
  const azimuth=(angle/(2*Math.PI)+1)*count;
  const low=Math.floor(azimuth), mix=azimuth-low;
  const distance=Math.hypot(u,v);
  const r=Math.min(model.radii.length-1,distance/.94*(model.radii.length-1));
  const ring=Math.floor(r), next=Math.min(ring+1,model.radii.length-1);
  const f=r-ring;
  const interpolate=values=>{
    const at=i=>values[i][low%count]*(1-mix)+values[i][(low+1)%count]*mix;
    return at(ring)*(1-f)+at(next)*f;
  };
  const shift=Math.max(-.38,Math.min(.38,interpolate(model.mid)*.78))*radius;
  const fade=Math.min(1,Math.sqrt(remaining)/.42);
  const half=Math.min(radius*(1.02-Math.abs(shift)/radius),radius*interpolate(model.half)*fade);
  return [y+shift-half,y+shift+half];
}

// Depth envelopes modify authored teaching shapes in their native case
// coordinates. x and z stay fixed, so the same two physical bounds can drive
// a solid, an arbitrary section, and an outer-wall caliper.
export function depthSpan(shape, u, v) {
  const x=shape.center[0]+u*shape.radii[0], z=shape.center[2]+v*shape.radii[2];
  const scale=footprintScale(shape,u,v);
  u/=scale;
  v/=scale;
  const remaining = Math.max(0, 1-u*u-v*v);
  const radius = shape.radii[1];
  const h = radius*Math.sqrt(remaining);
  const y = shape.center[1];
  switch (shape.depthProfile) {
    case 'fibroglandular': {
      const [front,back]=glandDepth(shape,u,v,remaining);
      const limit=shape.posteriorLimit;
      const a=(x-limit.center[0])/limit.radii[0], b=(z-limit.center[2])/limit.radii[2];
      if (footprintValue(limit,a,b)>=0) return [front,back];
      const ceiling=depthSpan(limit,a,b)[0]-.15;
      return [Math.min(front,ceiling),Math.min(back,ceiling)];
    }
    case 'retromammary-fat':
    case 'pectoral-fascia': {
      const depth = y+1.7*u*u+2.8*v*v-2.2*u*v;
      const envelope = radius*remaining**.28;
      const fascia = depth-envelope;
      return shape.depthProfile==='retromammary-fat'
        ? [fascia-1.4*remaining**.3,fascia]
        : [fascia,depth+envelope];
    }
    case 'chest-wall': {
      const depth = y+3.1*u*u+2.6*v*v;
      const envelope = radius*remaining**.32;
      return [depth-envelope,depth+envelope];
    }
    case 'axillary-cortex': {
      // The standalone authored axilla uses a shallow hilar indentation and
      // bow. Make the visible posterior notch lateral to the saved AP chord.
      const lateral = u*u/(u*u+.12);
      const notch = 1.12*lateral*Math.exp(-(((v+.12)/.43)**2))*remaining**1.1;
      return [y-h,y+h-notch];
    }
    default:
      return [y-h,y+h];
  }
}

export function cut(shape, slice) {
  const distance = (slice.level - shape.center[slice.normal]) / shape.radii[slice.normal];
  const factor=Math.sqrt(Math.max(0,1-distance*distance));
  const range=shape.footprint ? sectionLimits(shape,slice,distance) : factor ? [-factor,factor] : null;
  if (!range) return null;
  const center=shape.center[slice.axis]-slice.center;
  const width=shape.radii[slice.axis];
  const [left,right]=range.map(offset=>center+width*offset);
  const x=(left+right)/2,w=(right-left)/2;
  const section={x,y:shape.center[1],w,h:shape.radii[1]*factor};
  if (!shape.depthProfile) return section;
  const spanAt = (lateral) => {
    const offset=(lateral-center)/width;
    return slice.axis===0 ? depthSpan(shape,offset,distance) : depthSpan(shape,distance,offset);
  };
  const [front,back]=spanAt(x);
  return {...section,y:(front+back)/2,h:(back-front)/2,spanAt};
}

export function sectionContour({x,y,w,h,spanAt}) {
  return [0,1].flatMap(side=>Array.from({length:41},(_,i)=>{
    const radial=(side===0 ? -1 : 1)*Math.cos(i*Math.PI/40);
    const lateral=x+w*radial;
    const depth=spanAt?.(lateral)[side] ?? y+(side===0 ? -1 : 1)*h*Math.sqrt(Math.max(0,1-radial*radial));
    return [lateral,depth];
  }));
}

export function clipSectionEdge(a,b,half,depth) {
  let start=0,end=1;
  for (const [axis,min,max] of [[0,-half,half],[1,0,depth]]) {
    const delta=b[axis]-a[axis];
    if (!delta) {
      if (a[axis]<min || a[axis]>max) return null;
      continue;
    }
    const first=(min-a[axis])/delta,last=(max-a[axis])/delta;
    start=Math.max(start,Math.min(first,last));
    end=Math.min(end,Math.max(first,last));
    if (start>=end) return null;
  }
  return [start,end].map(t=>a.map((point,i)=>point+t*(b[i]-point)));
}

export function endpoints(model, slice, mark) {
  const shape = model.find(item => item.id === mark.id);
  const section = shape && cut(shape, slice);
  if (!section) return null;
  const {x, y, w, h} = section;
  if (mark.axis === 'width') {
    return [[x-w, section.spanAt?.(x-w)[0] ?? y], [x+w, section.spanAt?.(x+w)[0] ?? y]];
  }
  if (mark.axis === 'depth') {
    const [front,back]=section.spanAt?.(x) ?? [y-h,y+h];
    return [[x,front],[x,back]];
  }
  const other = model.find(item => item.id === mark.inner);
  const inner = other && cut(other, slice);
  if (!inner) return null;
  const u = inner.x + mark.lateralOffset;
  const anterior = (center, width, depth, height) => depth-height*Math.sqrt(1-((u-center)/width)**2);
  return [[u, section.spanAt?.(u)[0] ?? anterior(x,w,y,h)],
    [u, inner.spanAt?.(u)[0] ?? anterior(inner.x,inner.w,inner.y,inner.h)]];
}

export function chapterFor(record, key, settings) {
  const viewImage = `images/${key}.svg`;
  const view = record.views.find(item => item.image === viewImage);
  if (!view) throw new Error(`Unknown organ view ${record.id}/${viewImage}`);
  const frames = settings.frames ?? 25;
  return {
    id: key, title: view.title, viewImage, frames, evidenceFrame: Math.floor(frames/2),
    observation: view.caption, measurement: view.measurement,
    axis: 0, sweep: [-16,16], ...settings,
  };
}
