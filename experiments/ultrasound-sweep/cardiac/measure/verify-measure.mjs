import { longitudinalCurves } from './strain.js';
import assert from 'node:assert/strict';
import { BEAT_SECONDS, protocol, spectra, tools } from './protocol.js';
import {
  aliased,
  beamGain,
  diskTrace,
  diskVolume,
  fractionalChange,
  integral,
  spectralResults,
  velocity,
} from './calculations.js';
import { axialFlow } from './color-section.js';
import { heartFrame, probePlane } from '../heart-geometry.js';
import { CARDIAC_VIEWS } from '../heart-poses.js';

const near = (a, b, t = 1e-7) => assert.ok(Math.abs(a - b) < t, `${a} vs ${b}`);
for (const id of Object.keys(CARDIAC_VIEWS)) assert.ok(protocol[id], id);
for (const ids of Object.values(protocol)) for (const id of ids) assert.ok(spectra[id] || tools[id], id);
for (const s of Object.values(spectra)) {
  for (const [phase, cmps] of s.knots) near(velocity(s, phase), cmps);
  assert.ok(integral(s).vti > 0);
}
near(beamGain('PW', 60, 0), 0.5);
near(beamGain('CW', 60, 9), 0.5);
near(beamGain('PW', 0, 7), 0);
near(beamGain('TDI', 0, 4), 0);
near(beamGain('CW', 90, 0), 0);
near(aliased(61, 50), -39);
near(aliased(-61, 50), 39);
near(aliased(50, 50), 50);
const plug = {
  knots: [
    [0, -100],
    [1, -100],
  ],
};
near(integral(plug).vti, 100 * BEAT_SECONDS);
near(integral(plug).meanGradient, 4);
near(integral(plug, 1, 0.2, 0.5).vti, 100 * BEAT_SECONDS * 0.3);
assert.ok(Number.isNaN(integral(plug, 1, 0.5, 0.1).vti));
assert.match(spectralResults('tr', 1, 2, 3).join(' '), /RVSP estimate 22.4 mmHg/);
assert.match(spectralResults('lvot', 1, 2, 3).join(' '), /mL/);
assert.deepEqual(spectralResults('mitral', 0, 2, 3), ['No sampled signal']);
assert.match(spectralResults('mitral', 1, 2, 3).join(' '), /E\/A 1.46/);
near(fractionalChange(120, 48), 60);

const ellipse = [];
for (let i = 0; i <= 320; i++) {
  const a = (Math.PI * i) / 320;
  ellipse.push([20 * Math.cos(a), 80 * Math.sin(a)]);
}
const t = diskTrace(ellipse, [0, 0]);
near(diskVolume(t, t), (2 * Math.PI * 20 ** 2 * 80) / 3000, 0.04);
const fr = heartFrame(0.51);
const map = axialFlow(fr, probePlane(0, 'a4c'), 0.51);
assert.ok(map.some((v) => v > 60));
assert.notDeepEqual(map, axialFlow(fr, probePlane(18, 'a4c'), 0.51));
assert.ok(axialFlow(heartFrame(0.16), probePlane(0, 'suprasternal-arch'), 0.16).some((v) => v < -40));
for (const id of ['a4c', 'plax', 'subcostal-ivc', 'suprasternal-arch']) {
  const v = axialFlow(heartFrame(0), probePlane(0, id), 0);
  assert.ok(
    v.every((n) => n === 0),
    id + ' at ED',
  );
}
const curves = longitudinalCurves(20);
assert.equal(curves[0].flat().length, 18);
assert.ok(curves[0].flat().every((n) => Math.abs(n) < 1e-6));
assert.ok(curves[7].flat().every((n) => Number.isFinite(n) && n < 0));
assert.ok(
  curves
    .at(-1)
    .flat()
    .every((n) => Math.abs(n) < 1e-6),
);
console.log(
  'Measurement units, disk summation, Doppler sampling, gradients, VTI, aliasing and registered flow passed.',
);
