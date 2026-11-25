import { add, cross, dot, mean, mul, sub, unit } from './playable-model.js';

const colors = {
  wall: '#d19b79', bowel: '#e2dd79', cord: '#5fdaa9', membrane: '#f698af', plane: '#b6d7ff',
};
const light = [.3,.42,.86];
const background = [7,24,33];
const channel = (value,base,amount)=>Math.round(value*amount+base*(1-amount));
const sectors = 36;
const angles = Array.from({length:sectors},(_,i)=>i*2*Math.PI/sectors);
const cache = new WeakMap();

function surface(faces, rings, color) {
  const rgb=color.slice(1).match(/../g).map(value=>parseInt(value,16));
  for(let i=1;i<rings.length;i++) for(let j=0;j<sectors;j++) {
    const k=(j+1)%sectors;
    const corners=[rings[i-1][j],rings[i-1][k],rings[i][k],rings[i][j]];
    const normal=unit(cross(sub(corners[1],corners[0]),sub(corners[3],corners[0])));
    const centre=mean(corners[0],corners[2]);
    const illumination=.36+.6*Math.abs(dot(normal,light));
    const fill=`rgb(${rgb.map((value,k)=>channel(value,background[k],illumination)).join(',')})`;
    faces.push({corners, centre, fill});
  }
}

function tubeRings({points,radius}) {
  return points.map((point,i)=>{
    const axis=unit(sub(points[Math.min(i+1,points.length-1)],points[Math.max(0,i-1)]));
    const u=unit(cross(axis,[0,0,1])), v=cross(axis,u);
    return angles.map(angle=>add(point,add(mul(u,radius*Math.cos(angle)),mul(v,radius*Math.sin(angle)))));
  });
}

function meshes(model) {
  if (cache.has(model)) return cache.get(model);
  const faces=[];
  const rim=angles.map(angle=>model.wallPoint(1,angle));
  const wall=Array.from({length:8},(_,i)=>angles.map(angle=>model.wallPoint(1+i*.23,angle)));
  const innerRim=rim.map(p=>sub(p,[0,model.wallThickness,0]));
  surface(faces,[innerRim, ...wall],colors.wall);
  surface(faces,tubeRings(model.bowel),colors.bowel);
  const cordEnd=model.cord.points.findIndex(point=>point[0]>16);
  surface(faces,tubeRings({...model.cord,points:model.cord.points.slice(0,cordEnd)}),colors.cord);
  const membrane=Array.from({length:17},(_,i)=>angles.map(angle=>
    model.membranePoint(Math.sin(i*Math.PI/32),angle)));
  const result={faces,rim,membrane};
  cache.set(model,result);
  return result;
}

function path(ctx,points,closed=false) {
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for(const point of points.slice(1)) ctx.lineTo(...point);
  if(closed) ctx.closePath();
}

function hull(points) {
  const sorted=[...points].sort(([x,y],[u,v])=>x-u||y-v);
  const turn=([x,y],[u,v],[a,b])=>(u-x)*(b-y)-(v-y)*(a-x);
  const chain=nodes=>{
    const result=[];
    for(const node of nodes) {
      while(result.length>1 && turn(result.at(-2),result.at(-1),node)<=0) result.pop();
      result.push(node);
    }
    return result.slice(0,-1);
  };
  return [...chain(sorted),...chain(sorted.reverse())];
}

export function drawOmphalocele(ctx,model,plane,yaw) {
  const {faces,rim,membrane}=meshes(model);
  const angle=yaw+.94, c=Math.cos(angle), s=Math.sin(angle);
  const aim=mean(model.target,model.apex);
  const elevation=.5, horizontal=Math.cos(elevation), vertical=Math.sin(elevation);
  const view=[-s*horizontal,c*horizontal,vertical];
  const project=point=>{
    const [x,y,z]=sub(point,aim);
    return [169+(c*x+s*y)*6.2, 146+((-s*x+c*y)*vertical-z*horizontal)*6.2];
  };
  // This frame is the local portion of the same sample plane as the inset crop.
  const section=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([u,v])=>
    project(add(add(plane.target,mul(plane.width,u*13.5)),mul(plane.beam,v*16))));
  path(ctx,section,true);
  ctx.fillStyle='#b6d7ff20';
  ctx.fill();

  for(const face of [...faces].sort((a,b)=>dot(a.centre,view)-dot(b.centre,view))) {
    path(ctx,face.corners.map(project),true);
    ctx.fillStyle=face.fill;
    ctx.fill();
    ctx.strokeStyle=face.fill;
    ctx.lineWidth=.8;
    ctx.stroke();
  }
  path(ctx,rim.map(project),true);
  ctx.strokeStyle='#f6c19f';
  ctx.lineWidth=1.6;
  ctx.stroke();

  // Show the covering as a translucent envelope so the enclosed bowel can be
  // followed in the same view. Its outline is projected from the sampled sac.
  const membraneRings=membrane.map(ring=>ring.map(project));
  path(ctx,hull(membraneRings.flat()),true);
  ctx.fillStyle='#f698af32';
  ctx.fill();
  ctx.lineWidth=2;
  ctx.strokeStyle=colors.membrane;
  ctx.stroke();
  path(ctx,membraneRings[6],true);
  ctx.lineWidth=1;
  ctx.strokeStyle='#f698af51';
  ctx.stroke();

  path(ctx,section,true);
  ctx.lineWidth=1.2;
  ctx.strokeStyle=colors.plane+'a0';
  ctx.setLineDash([4,4]);
  ctx.stroke();
  ctx.setLineDash([]);
}

export function drawOmphaloceleLegend(ctx) {
  const items=[
    [colors.wall,'Wall opening',15,254], [colors.membrane,'Covering membrane',139,254],
    [colors.bowel,'Herniated bowel',15,279], [colors.cord,'Cord',150,279],
    [colors.plane,'Scan plane',255,279],
  ];
  ctx.font='14px system-ui,sans-serif';
  for(const [color,label,x,y] of items) {
    ctx.fillStyle=color;
    ctx.fillRect(x,y-9,8,8);
    ctx.fillStyle='#e3ecef';
    ctx.fillText(label,x+14,y);
  }
}
