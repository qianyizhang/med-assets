// Refit the delivered atlas exterior to the casebook's authored contact datum.
import * as THREE from '../../vendor/build/three.module.js';
import {loadSweepPart, sweepConfig} from '../../case-scene.js';

function painter(geometry, {left, bottom, right, top}, spacing) {
  const width = Math.ceil((right-left)/spacing)+1;
  const height = Math.ceil((top-bottom)/spacing)+1;
  const front = new Float32Array(width*height).fill(-Infinity);
  const vertices = geometry.getAttribute('position');
  const indices = geometry.index.array;
  for (let i=0; i<indices.length; i+=3) {
    const [a,b,c] = [indices[i],indices[i+1],indices[i+2]];
    const x = vertices.getX(a), z = vertices.getZ(a);
    const u = vertices.getX(b)-x, v = vertices.getZ(b)-z;
    const p = vertices.getX(c)-x, q = vertices.getZ(c)-z;
    const det = u*q-v*p;
    if (Math.abs(det)<1e-7) continue;
    const minX = Math.max(0,Math.ceil((x+Math.min(0,u,p)-left)/spacing));
    const maxX = Math.min(width-1,Math.floor((x+Math.max(0,u,p)-left)/spacing));
    const minZ = Math.max(0,Math.ceil((z+Math.min(0,v,q)-bottom)/spacing));
    const maxZ = Math.min(height-1,Math.floor((z+Math.max(0,v,q)-bottom)/spacing));
    const y = vertices.getY(a), by = vertices.getY(b)-y, cy = vertices.getY(c)-y;
    for (let row=minZ; row<=maxZ; row++) {
      for (let col=minX; col<=maxX; col++) {
        const dx=left+col*spacing-x, dz=bottom+row*spacing-z;
        const alpha=(dx*q-dz*p)/det, beta=(dz*u-dx*v)/det;
        if (alpha>=-1e-6 && beta>=-1e-6 && alpha+beta<=1.000001) {
          const k=row*width+col;
          front[k]=Math.max(front[k],y+alpha*by+beta*cy);
        }
      }
    }
  }
  return (x,z) => {
    const u=(x-left)/spacing, v=(z-bottom)/spacing;
    const j=Math.floor(u), i=Math.floor(v);
    if (i<0 || j<0 || i+1>=height || j+1>=width) return undefined;
    const a=u-j, b=v-i;
    const k=i*width+j;
    const result=(front[k]*(1-a)+front[k+1]*a)*(1-b)+(front[k+width]*(1-a)+front[k+width+1]*a)*b;
    return Number.isFinite(result) ? result : undefined;
  };
}

function pointDistance(px,pz,[x,z],[u,v]) {
  const dx=u-x, dz=v-z, len=dx*dx+dz*dz;
  const t=len ? Math.max(0,Math.min(1,((px-x)*dx+(pz-z)*dz)/len)) : 0;
  return Math.hypot(px-x-t*dx,pz-z-t*dz);
}

export async function fitCaseSkin(sources, anchors, paths, {reach=23, blend=36}={}) {
  const id=sources.find(source=>sweepConfig(source));
  if (!id) throw new Error('The delivered study has no exterior for this case region.');
  const geometry=await loadSweepPart(id);
  const scale=sweepConfig(id).voxelMm ?? 1.5;
  const anchor=anchors[id] ?? anchors[sources[0]];
  geometry.translate(-anchor[0],0,-anchor[1]);
  geometry.scale(scale,scale,scale);
  const x=paths.flat().map(p=>p[0]), z=paths.flat().map(p=>p[1]);
  const bounds={
    left:Math.min(...x,0)-reach-blend-10, right:Math.max(...x,0)+reach+blend+10,
    bottom:Math.min(...z,0)-reach-blend-10, top:Math.max(...z,0)+reach+blend+10,
  };
  const surface=painter(geometry,bounds,2);
  const datum=surface(0,0);
  if (!Number.isFinite(datum)) throw new Error('The exterior does not cover the modeled contact datum.');
  const vertices=geometry.getAttribute('position');
  for (let i=0; i<vertices.count; i++) {
    const x=vertices.getX(i), z=vertices.getZ(i);
    const y=vertices.getY(i), front=surface(x,z);
    let yy=y-datum;
    // Keep the whole exterior and preserve its rear contour. Flatten only the
    // anterior shell around the trajectories, as the casebook uses y=0 for contact.
    if (front!==undefined) {
      const displacement=front-datum;
      // An outward lobe such as the chin may protrude further than the
      // default blend depth. Preserve the order of the superficial layers.
      const thickness=Math.max(34,Math.abs(displacement)*1.8+8);
      if (front-y<thickness) {
        const distance=Math.min(...paths.map(([a,b])=>pointDistance(x,z,a,b)));
        const taper=1-Math.max(0,Math.min(1,(distance-reach)/blend));
        const superficial=Math.max(0,Math.min(1,1-(front-y)/thickness));
        yy-=displacement*taper*superficial;
      }
    }
    vertices.setY(i,yy);
  }
  vertices.needsUpdate=true;
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({
    color:'#c6a293',roughness:.96,side:THREE.DoubleSide,transparent:true,opacity:.3,depthWrite:false,
  }));
}
