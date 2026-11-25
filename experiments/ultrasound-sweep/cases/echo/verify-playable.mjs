import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chapters,sample} from './playable.js';
import {flowCase,apical,lvotPW} from './playable-signals.js';
import {integral,peakVelocity} from '../../cardiac/measure/calculations.js';
import {bodyPoint} from '../../cardiac/torso/registration.js';
const records=JSON.parse(readFileSync(new URL('cases.json',import.meta.url)));
const [normal,stenosis,limited]=records;
const normalSet=chapters(normal), abnormal=chapters(stenosis), poor=chapters(limited);
assert.equal(new Set(normalSet.filter(x=>x.mode==='section').map(x=>x.view)).size,17);
function chord(chapter,frame,record,vessel,fraction){
  const state=sample(chapter,frame,record), tube=state.frame.vessels[vessel].lumen[0];
  const ring=tube[Math.floor(tube.length*fraction)], hits=[];
  ring.forEach((a,i)=>{
    const b=ring[(i+1)%ring.length],da=state.plane.distance(a),db=state.plane.distance(b);
    if((da>0)!==(db>0)) hits.push(state.plane.section(a.map((v,k)=>v+(b[k]-v)*da/(da-db))));
  });
  assert.equal(hits.length,2);
  return Math.hypot(hits[1][0]-hits[0][0],hits[1][1]-hits[0][1]);
}
const caliper=abnormal.find(c=>c.mode==='diameter');
assert(Math.abs(chord(caliper,caliper.evidenceFrame,stenosis,'LVOT',.78)-21)<.25);
const cava=normalSet.find(c=>c.view==='subcostal-ivc');
assert(Math.abs(chord(cava,20,normal,'IVC',.5)-17)<.2);
assert(Math.abs(chord(cava,30,normal,'IVC',.5)-7)<.1);
const cw=abnormal.find(c=>c.view==='right-parasternal');
const contact=bodyPoint(sample(cw,38,stenosis).plane.origin);
assert(Math.hypot(...contact.map((v,i)=>v-[-44,1304,177.471][i]))<.01);
assert.equal(peakVelocity(flowCase),454);
assert.equal(peakVelocity(apical).toFixed(1),'358.7');
assert.equal(integral(flowCase).meanGradient.toFixed(0),'45');
assert.equal((Math.PI*1.05**2*integral(lvotPW).vti/integral(flowCase).vti).toFixed(2),'0.59');
assert(poor.filter(c=>c.mode==='doppler').every(c=>/withheld|incomplete/i.test(c.measurement)));
const phase=24;
const healthy=sample(normalSet.find(c=>c.view==='psax-av'),phase,normal);
const diseased=sample(abnormal[0],phase,stenosis);
assert.notDeepEqual(healthy.frame.details.filter(v=>v.name==='AV'),diseased.frame.details.filter(v=>v.name==='AV'));
console.log('Echo baseline windows, moving IVC and LVOT calipers, restricted valve, CW contact and flow-derived findings passed.');
