// Run on the shipped surfaces and the same registered sector used in the UI.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {CARDIAC_VIEWS,probePlane} from '../heart-poses.js';
import {bodyPoint,bodyDirection} from './registration.js';

const inventory = JSON.parse(await readFile(new URL('geometry.json',import.meta.url)));
async function readTriangles(part) {
  const data = await readFile(new URL(part+'.raw',import.meta.url));
  assert.equal(createHash('sha256').update(data).digest('hex'),inventory[part].sha256);
  const vertices=data.readUInt32LE(0), faces=data.readUInt32LE(4);
  assert.equal(data.length,8+12*(vertices+faces));
  const xyz = new Float32Array(data.buffer,data.byteOffset+8,vertices*3);
  const indices = new Uint32Array(data.buffer,data.byteOffset+8+vertices*12,faces*3);
  return Array.from({length:faces},(_,i)=>Array.from(indices.subarray(i*3,i*3+3),j=>xyz.subarray(j*3,j*3+3)));
}
const [skin,bones,cartilage] = await Promise.all(['skin','bones','cartilage'].map(readTriangles));
const minus = (a,b) => [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const dot = (a,b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];

function firstHit(origin, direction, triangles) {
  let closest=Infinity;
  for (const [a,b,c] of triangles) {
    const ab=minus(b,a), ac=minus(c,a);
    const h=cross(direction,ac),det=dot(ab,h);
    if (Math.abs(det)<1e-8) continue;
    const offset=minus(origin,a), u=dot(offset,h)/det;
    if (u<0 || u>1) continue;
    const q=cross(offset,ab),v=dot(direction,q)/det;
    if (v<0 || u+v>1) continue;
    const t=dot(ac,q)/det;
    if (t>0 && t<closest) closest=t;
  }
  return closest;
}

const cage=bones.concat(cartilage);
let maxContact=0;
for (const [id,view] of Object.entries(CARDIAC_VIEWS)) {
  const plane=probePlane(0,id),contact=bodyPoint(plane.origin),beam=bodyDirection(plane.down);
  const front=[contact[0],contact[1],450];
  const surfaceZ=front[2]-firstHit(front,[0,0,-1],skin);
  const residual=Math.abs(surfaceZ-contact[2]);
  maxContact=Math.max(maxContact,residual);
  assert.ok(residual<1,`${id}: lens misses compact anterior skin by ${residual} mm`);
  const distance=Math.hypot(...minus(view.target,plane.origin));
  const boneDistance=firstHit(contact,beam,cage);
  assert.ok(boneDistance>distance,`${id}: rib cage at ${boneDistance.toFixed(1)} mm before the ${distance.toFixed(1)} mm aim point`);
  for(const tilt of [-28,0,28]) {
    const rotated=probePlane(tilt,id);
    assert.deepEqual(rotated.origin,plane.origin);
    assert.deepEqual(rotated.down,plane.down);
    const u=17,v=64,p=bodyPoint(rotated.world(u,v));
    const diff=minus(p,contact),right=bodyDirection(rotated.right);
    assert.ok(Math.abs(dot(diff,right)-u)<1e-5 && Math.abs(dot(diff,beam)-v)<1e-5);
  }
}
console.log(`${Object.keys(CARDIAC_VIEWS).length} skin contacts and central rays passed; maximum anterior skin discrepancy ${maxContact.toFixed(3)} mm.`);

// The modeled case itineraries include a right-parasternal Doppler window
// beyond the regional viewer's stock windows. Validate the actual case
// acquisition's contact, particularly the alternate view.
const visits = JSON.parse(await readFile(new URL('../../cases/echo/cases.json', import.meta.url)));
const {chapters, sample} = await import('../../cases/echo/playable.js');
const caseContacts = new Map();
for (const visit of visits) {
  for (const acquisition of chapters(visit)) {
    const {plane} = sample(acquisition, acquisition.evidenceFrame, visit);
    caseContacts.set(plane.id, bodyPoint(plane.origin));
  }
}
assert.ok(caseContacts.has('right-parasternal'));
let caseResidual = 0;
for (const [id, contact] of caseContacts) {
  const front = [contact[0], contact[1], 450];
  const surfaceZ = front[2] - firstHit(front, [0, 0, -1], skin);
  const residual = Math.abs(surfaceZ - contact[2]);
  caseResidual = Math.max(caseResidual, residual);
  assert.ok(residual < 1, `${id}: case lens misses torso skin by ${residual} mm`);
}
console.log(`${caseContacts.size} modeled case contacts passed; maximum skin discrepancy ${caseResidual.toFixed(3)} mm.`);
