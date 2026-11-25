// Local modeled anatomy in the mid-gestation volume's millimetre coordinates.
// +y is anterior. The ventral wall forms an elliptical opening in x/z.
const neckZ = 11.5;
const neckAxes = [7.5, 5.7];
const wallY = 26.4;
const sacDepth = 13;
const bowelRadius = 1.78;
const cordRadius = 2.4;
const wallThickness = 1.1;
const apex = [0, wallY + sacDepth, neckZ];

function wallDepth(x, z) {
  return wallY - .024*x*x - .025*(z-neckZ)**2;
}

function wallPoint(radius, angle) {
  const x = neckAxes[0] * radius * Math.cos(angle);
  const z = neckZ + neckAxes[1] * radius * Math.sin(angle);
  return [x, wallDepth(x, z), z];
}

function sacRadiusSquared(t) {
  return (1-t) * (1+3.15*t);
}

function membranePoint(t, angle) {
  const [x, y, z] = wallPoint(Math.sqrt(sacRadiusSquared(t)), angle);
  return [x, y+t*sacDepth, z];
}

const neck = [wallPoint(1, Math.PI), wallPoint(1, 0)].map(([x,y]) => [x,y,neckZ]);
const target = [0, wallY + 2, neckZ];

function smoothTube(control, radius) {
  // Chord samples of a smooth centerline define both the capsules in the
  // tissue sampler and the ring stations shown in the 3D cutaway.
  const points = [];
  for (let i=0; i<control.length-1; i++) {
    const a=control[Math.max(0,i-1)], b=control[i], c=control[i+1], d=control[Math.min(i+2,control.length-1)];
    for (let step=0; step<3; step++) {
      const t=step/3;
      points.push(b.map((v,k) => v+.5*t*((c[k]-a[k])+t*((2*a[k]-5*v+4*c[k]-d[k])
        + t*(-a[k]+3*v-3*c[k]+d[k])))));
    }
  }
  points.push(control.at(-1));
  const rs=radius**2;
  const segments = points.slice(1).map((b,i) => {
    const a=points[i], delta=b.map((n,j)=>n-a[j]);
    return {
      a, delta, squared:delta.reduce((sum,n)=>sum+n*n,0),
      min:a.map((n,j)=>Math.min(n,b[j])-radius), max:a.map((n,j)=>Math.max(n,b[j])+radius),
    };
  });
  const contains = (x,y,z) => {
    for (const {a,delta,squared,min,max} of segments) {
      if (x<min[0] || x>max[0] || y<min[1] || y>max[1] || z<min[2] || z>max[2]) continue;
      const dx=x-a[0], dy=y-a[1], dz=z-a[2];
      const t=Math.max(0,Math.min(1,(dx*delta[0]+dy*delta[1]+dz*delta[2])/squared));
      if ((dx-t*delta[0])**2+(dy-t*delta[1])**2+(dz-t*delta[2])**2 < rs) return true;
    }
    return false;
  };
  return {points,radius,contains};
}

const bowel = smoothTube([
  [-3.1,19.5,10.4], [-3.4,26,10.2], [-3.5,31.6,9.7], [-2.6,35.5,10],
  [-.5,36.7,11.7], [1.25,34.1,13.6], [3.3,30.6,13.5], [3.1,27.4,12.7], [2.5,20,12.5],
],bowelRadius);

export function buildOmphalocele(nativeCord) {
  const cord = smoothTube([
    apex, [.1,42.8,11.5], [1.6,46.1,12.2], [4.8,48.2,14], [9.2,48.8,17.2],
    [18.7,42.7,20.8], ...nativeCord.slice(5,9),
  ],cordRadius);
  return {apex,neck,target, wallPoint, membranePoint, wallThickness, bowel, cord,
    tissue(x,y,z) {
      if (z<3 || z>36 || Math.abs(x)>40 || y<2 || y>52) return;
      if (cord.contains(x,y,z)) return 'cord';
      if (y<17) return;
      const depth=y-wallDepth(x,z);
      const t=depth/sacDepth;
      const r2=(x/neckAxes[0])**2+((z-neckZ)/neckAxes[1])**2;
      const inSac=t>=0 && t<=1 && r2<sacRadiusSquared(t);
      if (inSac || (r2<1 && depth<0 && depth>-7.5)) {
        if (bowel.contains(x,y,z)) return 'sac contents';
        if (inSac && r2>sacRadiusSquared(t)-.15) return 'sac membrane';
        if (depth>=0) return 'sac space';
        if (depth>=-wallThickness) return 'abdominal wall defect';
        return 'fetus';
      }
      if (r2 < 3.2 && Math.abs(depth) < 3.6) {
        if (depth>0) return 'amniotic_cavity';
        return depth>=-wallThickness ? 'abdominal skin' : 'fetus';
      }
    },
  };
}
