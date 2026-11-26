import * as early from './playable-volume-early.js';
import * as first from './playable-volume-first.js';
import * as mid from './playable-volume-mid.js';
import * as late from './playable-volume-late.js';
import { buildOmphalocele } from './playable-omphalocele-model.js';

const volumes = { early, first, mid, late };
export const ectopicYolk = { centre: [57, -13, -3], outer: 2.45, inner: 1.55 };
export const fluidPocketRadius = 11;
export const nativeBiometryAxes = {
  mid: { head: [22.6, 28.1], abdomen: [22.8, 22.2] },
  late: { head: [40.8, 53.2], abdomen: [44, 44.5] },
};
const decoded = new Map();
export const add = (a, b) => a.map((n, i) => n + b[i]);
export const sub = (a, b) => a.map((n, i) => n - b[i]);
export const mul = (a, s) => a.map(n => n * s);
export const dot = (a, b) => a.reduce((sum, n, i) => sum + n * b[i], 0);
export const unit = a => mul(a, 1 / Math.hypot(...a));
export const cross = (a, b) => [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]];
export const mean = (a, b) => mul(add(a, b), .5);

export function volumeFor(stage) {
  if (decoded.has(stage)) return decoded.get(stage);
  const { geometry, runs } = volumes[stage];
  const compressed = atob(runs);
  const bytes = new Uint8Array(geometry.size.reduce((a, b) => a * b));
  let position = 0;
  for (let i = 0; i < compressed.length; i += 3) {
    const count = compressed.charCodeAt(i) + 256 * compressed.charCodeAt(i + 1);
    bytes.fill(compressed.charCodeAt(i + 2), position, position + count);
    position += count;
  }
  if (position !== bytes.length) throw new Error('Incomplete pregnancy volume');
  const result = { ...geometry, bytes };
  decoded.set(stage, result);
  return result;
}

// These shells position the probe in the locator. The internal anatomy comes
// from the stage volumes, and transvaginal probe motion starts in the canal.
const patient = {
  early: { centre: [0, -6, -16], radii: [80, 91, 100], anatomy: [0, -15, -15] },
  first: { centre: [0, 0, 8], radii: [80, 91, 102], anatomy: [0, 4, 20] },
  mid: { centre: [0, 6, 51], radii: [95, 106, 140], anatomy: [0, 2, 57] },
  late: { centre: [0, 11, 45], radii: [124, 150, 208], anatomy: [0, 1, 61] },
};

export function calibratedShape(stage, kind) {
  if (stage === 'early') return { crl: 10 };
  if (stage === 'first') return {
    crl: { normal: 60, abnormal: 62, limited: 59 }[kind],
    nt: kind === 'abnormal' ? 4.5 : 1.5,
  };
  if (stage === 'mid') return {
    bpd: { normal: 47, abnormal: 46, limited: 48 }[kind],
    hc: { normal: 178, abnormal: 173, limited: 180 }[kind],
    ac: { normal: 153, abnormal: 146, limited: 156 }[kind],
    fl: { normal: 33, abnormal: 32, limited: 34 }[kind],
    dvp: 45,
  };
  return {
    hc: { normal: 292, abnormal: 279, limited: 286 }[kind],
    ac: { normal: 284, abnormal: 239, limited: 270 }[kind],
    fl: { normal: 63, abnormal: 55, limited: 61 }[kind],
    dvp: { normal: 46, abnormal: 17, limited: 37 }[kind],
  };
}

export const softNames = [
  'adnexal follicles', 'ovary', 'tubal sac', 'tubal wall', 'ectopic yolk sac', 'cul-de-sac fluid',
  'NT space', 'posterior skin', 'amnion fold', 'abdominal skin', 'calvarial contour', 'ossified shaft',
  'abdominal wall defect', 'sac contents', 'sac membrane', 'nearest fluid', 'maternal interface',
  'forearm / lower-leg bones', 'model heart', 'first stomach',
  'sac space',
];

function perimeter(a, b) {
  return Math.PI * (3 * (a + b) - Math.sqrt((3*a + b) * (a + 3*b)));
}

function axesForCircumference(circumference, width) {
  const a = width / 2;
  let b = a * 1.2;
  for (let i = 0; i < 16; i++) b += (circumference - perimeter(a, b)) / 3.4;
  return [a, b];
}

export function landmarks(stage, kind) {
  const model = volumeFor(stage);
  const shape = calibratedShape(stage, kind);
  if (stage === 'early') return {
    shape, uterus: [0, -18, -13], heart: [3.6, -8, 1.65], crown: [3.6, -8.5, 6.35],
    rump: [3.6, -8.5, -3.65], right: [39, -17, -10], left: [-39, -17, -10],
    ectopic: [56, -13, -4], pouch: [0, -43, -44], cervix: [0, -33, -48],
  };
  if (stage === 'first') {
    const scale = shape.crl / 63;
    return {
      shape, scale, crown: [0, 2.6, 47.4*scale], rump: [0, 2.6, -15.6*scale],
      nuchal: [0, -10.9, 21.5*scale], heart: [0, -1.2, 11.7*scale],
      limbs: [
        [[8,0,14], [14,2,5], [15,12,11], [13,15,15]],
        [[-8,0,14], [-14,5,7], [-13,14,12], [-10,17,16]],
        [[6,1,-7], [10,10,-13], [12,14,-18], [10,18,-15]],
        [[-6,0,-7], [-10,9,-12], [-14,13,-17], [-13,18,-15]],
      ].map(limb => limb.map(([x,y,z]) => [x,y,z*scale])),
    };
  }
  const isLate = stage === 'late';
  const head = isLate ? [0, -2, 156] : [0, -1.6, 105.8];
  const abdomen = isLate ? [0, 4.6, 30.8] : [0, 2.4, 16.1];
  const hcAxes = axesForCircumference(shape.hc, shape.bpd ?? shape.hc / Math.PI * .88);
  const acAxes = axesForCircumference(shape.ac, shape.ac / Math.PI * .97);
  const [hip, knee] = model.limbs[2];
  const femur = { centre: mean(hip, knee), direction: unit(sub(knee, hip)), length: shape.fl };
  const fluid = model.fluid ? mean(...model.fluid) : [32, -9, 41];
  // In local space the maternal AP axis is the world Y row of the rotation.
  const vertical = model.axes[1];
  const omphalocele = stage === 'mid' && kind === 'abnormal' ? buildOmphalocele(model.cord) : undefined;
  return { shape, head, abdomen, hcAxes, acAxes, femur, fluid, vertical,
    limbs: model.limbs, cervix: model.cervix, placentalCord: model.placentalCord,
    placenta: model.placenta, cord: model.cord, omphalocele };
}

function inside(x, y, z, centre, radii) {
  return ((x-centre[0])/radii[0])**2 + ((y-centre[1])/radii[1])**2 + ((z-centre[2])/radii[2])**2 < 1;
}
function distanceToTube(x, y, z, a, b) {
  const dx = b[0]-a[0], dy = b[1]-a[1], dz = b[2]-a[2];
  const u = Math.max(0, Math.min(1, ((x-a[0])*dx+(y-a[1])*dy+(z-a[2])*dz)/(dx*dx+dy*dy+dz*dz)));
  return (x-a[0]-dx*u)**2+(y-a[1]-dy*u)**2+(z-a[2]-dz*u)**2;
}

export function sampler(stage, kind, l) {
  const v = volumeFor(stage);
  const { origin, spacing, names, bytes, size: [nx, ny, nz] } = v;
  const ids = Object.fromEntries([...names, ...softNames].map((name, i) => [name, i + 1]));
  const native = nativeBiometryAxes[stage];
  const voxel = (i,j,k) =>
    i>=0 && i<nx && j>=0 && j<ny && k>=0 && k<nz ? bytes[(k*ny+j)*nx+i] : 0;
  const raw = (x,y,z) => {
    const tissue = voxel(Math.round((x-origin[0])/spacing),
      Math.round((y-origin[1])/spacing),Math.round((z-origin[2])/spacing));
    // The case-specific model supplies the proximal cord for the abnormal visit.
    if (l.omphalocele && tissue===ids.cord && z<29.5 && y>17) return ids.amniotic_cavity;
    return tissue;
  };
  const interpolated = (x,y,z,tones) => {
    const px=(x-origin[0])/spacing,py=(y-origin[1])/spacing,pz=(z-origin[2])/spacing;
    const i = Math.floor(px),j = Math.floor(py),k = Math.floor(pz);
    const fi=px-i,fj=py-j,fk=pz-k;
    const mix=(a,b,w)=>a*(1-w)+b*w;
    const scalar=(dx,dy,dz)=>tones[voxel(i+dx,j+dy,k+dz)];
    const slice=dz=>mix(mix(scalar(0,0,dz),scalar(1,0,dz),fi),
      mix(scalar(0,1,dz),scalar(1,1,dz),fi),fj);
    return mix(slice(0),slice(1),fk);
  };
  const earlySample = (x, y, z) => {
    if (kind === 'abnormal' && inside(x,y,z,l.ectopic,[9,7,7.5])) {
      if (inside(x,y,z,l.ectopic,[6.5,5.2,5.5])) {
        const [a, b, c] = ectopicYolk.centre;
        const radiusSquared = (x - a)**2 + (y - b)**2 + (z - c)**2;
        if (radiusSquared >= ectopicYolk.outer**2 || radiusSquared < ectopicYolk.inner**2) {
          return ids['tubal sac'];
        }
        return ids['ectopic yolk sac'];
      }
      return ids['tubal wall'];
    }
    for (const centre of [l.right,l.left]) {
      if (inside(x,y,z,centre,[10,6,7])) {
        return inside(x,y,z,[centre[0]-2,centre[1],centre[2]+1],[3.4,2.6,3.4])
          || inside(x,y,z,[centre[0]+3,centre[1],centre[2]-2],[2.1,2.5,2.2])
          ? ids['adnexal follicles'] : ids.ovary;
      }
    }
    if (kind === 'abnormal' && inside(x,y,z,l.pouch,[19,4,9])) return ids['cul-de-sac fluid'];
    const t = raw(x,y,z);
    if (kind !== 'normal' && [ids.gestational_rim, ids.gestational_sac, ids.amnion,
      ids.yolk_sac, ids.embryo, ids.cardiac_region].includes(t)) return ids.uterus;
    if (kind === 'normal' && (t === ids.embryo || t === ids.cardiac_region)) {
      const scaled = raw(x,y,(z-1.35)*1.07+1.35);
      return scaled === ids.embryo || scaled === ids.cardiac_region ? scaled : ids.gestational_sac;
    }
    return t;
  };
  const fetalLabels = new Set(['fetus','nasal_bone','calvarium','falx','spinal_echoes','choroid_plexus','fetal_bladder'].map(name=>ids[name]));
  const firstSample = (x,y,z) => {
    const nt = l.nuchal;
    if (Math.abs(x) < 6 && Math.abs(z - nt[2]) < 7) {
      const taper = Math.sqrt(Math.max(0,1-(x/6)**2-((z-nt[2])/7)**2));
      const outer = nt[1]-l.shape.nt*taper;
      if (taper && y <= nt[1] && y >= outer) return ids['NT space'];
      if (taper && Math.abs(y-outer+.22)<.25) return ids['posterior skin'];
      if (kind === 'limited' && Math.abs(y-(outer-1.5-.4*x))<.32) return ids['amnion fold'];
    }
    if (inside(x,y,z,[-3.3,3.8,-2.9*l.scale],[2.9,2.8,3.6])) return ids['first stomach'];
    if (inside(x,y,z,l.heart,[3.75,3.4,3.65])) return ids['model heart'];
    const unscaled = raw(x,y,z), scaled = raw(x,y,z/l.scale);
    if (fetalLabels.has(scaled)) return scaled;
    return fetalLabels.has(unscaled) ? ids.amniotic_fluid : unscaled;
  };
  const gestSample = (x,y,z) => {
    const f = l.femur;
    const u = (x-f.centre[0])*f.direction[0]+(y-f.centre[1])*f.direction[1]+(z-f.centre[2])*f.direction[2];
    if (Math.abs(u) <= f.length/2
      && (x-f.centre[0]-u*f.direction[0])**2+(y-f.centre[1]-u*f.direction[1])**2
      +(z-f.centre[2]-u*f.direction[2])**2 < (stage==='late'?4.2:2.6)**2) return ids['ossified shaft'];
    const lesion = l.omphalocele?.tissue(x,y,z);
    if (lesion) return ids[lesion];
    const [hx, hy, hz] = l.head;
    const [ax, ay, az] = l.abdomen;
    const [hrx, hry] = l.hcAxes;
    const [arx, ary] = l.acAxes;
    if (Math.abs(z-hz)<8 && Math.abs(x)<hrx+7 && Math.abs(y-hy)<hry+7) {
      const factor = Math.sqrt(1-((z-hz)/29)**2);
      const d = Math.hypot(x/hrx,(y-hy)/hry);
      const [nativeX, nativeY] = native.head;
      const sampled = raw(x*nativeX/hrx,hy+(y-hy)*nativeY/hry,z);
      if (Math.abs(d-factor)<.032) return ids['calvarial contour'];
      if (d < factor) return sampled || ids.fetus;
      if ([ids.fetus,ids.calvarium,ids.falx,ids.thalami,ids.cavum].includes(sampled)) return ids.amniotic_cavity;
    }
    if (Math.abs(z-az)<6 && Math.abs(x)<arx+5 && Math.abs(y-ay)<ary+5) {
      const d = Math.hypot(x/arx,(y-ay)/ary);
      const [nativeX, nativeY] = native.abdomen;
      const sampled = raw(x*nativeX/arx,ay+(y-ay)*nativeY/ary,z);
      if (Math.abs(d-1)<.025) return ids['abdominal skin'];
      if (d < 1) return sampled || ids.fetus;
      if ([ids.fetus,ids.stomach,ids.umbilical_vein].includes(sampled)) return ids.amniotic_cavity;
    }
    const pocket = [x-l.fluid[0],y-l.fluid[1],z-l.fluid[2]];
    const along = pocket[0]*l.vertical[0]+pocket[1]*l.vertical[1]+pocket[2]*l.vertical[2];
    const radial = pocket[0]**2+pocket[1]**2+pocket[2]**2-along**2;
    if (radial<fluidPocketRadius**2 && Math.abs(along)<l.shape.dvp/2+5) {
      if ((along/(l.shape.dvp/2))**2+radial/fluidPocketRadius**2<1) return ids['nearest fluid'];
      if ((along/(l.shape.dvp/2+1.4))**2+radial/12**2<1.05) return ids['maternal interface'];
    }
    if (stage === 'mid' && Math.abs(x)>15 && y>15 && y<39 && z>-43 && z<49) {
      for (let i=0;i<l.limbs.length;i++) {
        const [,joint,wrist] = l.limbs[i];
        if (distanceToTube(x+1.55,y,z,joint,wrist)<1.1 || distanceToTube(x-1.55,y,z,joint,wrist)<1.1) {
          return ids['forearm / lower-leg bones'];
        }
      }
    }
    return raw(x,y,z);
  };
  return { scan: stage==='early' ? earlySample : stage==='first' ? firstSample : gestSample,
    interpolated, ids, names: [null,...names,...softNames] };
}

export function patientEnvelope(stage) {
  return patient[stage];
}

export function probeContact(stage, target, beam, transvaginal) {
  if (transvaginal) {
    const canalY = -40, canalZ = -67;
    return [Math.max(-20,Math.min(20,target[0]*.31)),canalY + beam[0]*7,canalZ + beam[1]*4];
  }
  const { centre, radii } = patient[stage];
  const d = sub(target,centre).map((n,i)=>n/radii[i]);
  const q = beam.map((n,i)=>n/radii[i]);
  const bd = dot(d,q);
  const length = (bd+Math.sqrt(Math.max(0,bd*bd-dot(q,q)*(dot(d,d)-1))))/dot(q,q);
  return sub(target,mul(beam,length));
}
