import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { colorVelocityAt, duplexSample, duplexStations, icaCcaRatio, registeredAcquisition } from './duplex.js';

const protocol = JSON.parse(readFileSync(new URL('./protocol.json', import.meta.url)));
const sources = JSON.parse(readFileSync(new URL('./sources.json', import.meta.url)));
const ccaSources = JSON.parse(readFileSync(new URL('../research/carotid.json', import.meta.url)));
const stations = duplexStations(protocol);
assert.equal(stations.length, 18);
assert.equal(new Set(stations.map(({ id }) => id)).size, 18);
for (const { referenceIds } of stations) {
  assert(referenceIds.every((id) => sources[id] || ccaSources[id]));
}
for (const side of ['left', 'right']) {
  for (const segment of ['cca-prox', 'cca-dist']) {
    assert(stations.find((station) => station.side === side && station.segment === segment)
      .referenceIds.includes('carotid-cca-spectral'));
  }
  assert(stations.find((station) => station.side === side && station.segment === 'subclavian')
    .referenceIds.includes('carotid-subclavian'));
}
for (const [id, source] of Object.entries(sources)) {
  assert.equal(source.path, `carotid-survey/media/${id}.webp`);
  const raw = readFileSync(new URL(`../${source.path}`, import.meta.url));
  assert.equal(raw.subarray(8, 12).toString(), 'WEBP');
  assert.equal(createHash('sha256').update(raw).digest('hex'), source.sha256);
}
for (const waveform of Object.values(protocol.waveformProfiles)) {
  assert.equal(waveform[0][0], 0);
  assert.equal(waveform.at(-1)[0], 1);
  assert.equal(waveform[0][1], waveform.at(-1)[1]);
  assert(waveform.every(([phase, speed], i) => Number.isFinite(speed) && (!i || phase > waveform[i - 1][0])));
}
const beamDirection = [0, 1, 0];
const flowDirection = [0, -.5, Math.sqrt(.75)];
const gate = { beamDirection, flowDirection, diameterMm: 6 };
const acquisition = registeredAcquisition(gate);
assert.equal(registeredAcquisition({ ...gate, steeringSupported: false }), null);
const get = (segment) => stations.find((station) => station.side === 'right' && station.segment === segment);
const sample = (segment, options) => duplexSample(get(segment), { ...acquisition, ...options });
const measurements = (segment) => sample(segment).measurements;
const peak = sample('ica-prox');
assert.equal(peak.status, 'measured');
assert(peak.power.every((row) => row.length === peak.velocityBinsCmS.length &&
  row.every((value) => value >= 0 && value <= 1)));
assert.equal(peak.timeSeconds.length, peak.power.length);
assert.equal(peak.timeSeconds.length, peak.envelopeCmS.length);
assert(Math.abs(peak.actualAngleDeg - 60) < 1e-7);
assert(Math.abs(peak.measurements.psvCmS - Math.max(...peak.envelopeCmS)) < 1e-7);
assert.equal(peak.measurements.edvCmS, peak.envelopeCmS.at(-1));
assert(measurements('ica-prox').edvCmS > measurements('eca').edvCmS);
assert(measurements('vertebral').edvCmS > measurements('eca').edvCmS);
assert(sample('subclavian').envelopeCmS.some((velocity) => velocity < -10));
const subclavian = sample('subclavian');
assert(subclavian.power.at(-1).some((signal) => signal > 0));
assert(subclavian.power.at(-1).every((signal, index) =>
  subclavian.velocityBinsCmS[index] > 0 || signal === 0));
assert(subclavian.power.some((row) => row.some((signal, index) =>
  subclavian.velocityBinsCmS[index] < 0 && signal > 0)));
assert.equal(sample('bulb').status, 'unavailable');
assert(!sample('bulb').measurements);
assert.equal(sample('ica-prox', { prfHz: 1000 }).status, 'aliased');
assert(!sample('ica-prox', { prfHz: 1000 }).measurements);
assert.equal(sample('ica-prox', { angleDeg: 61 }).status, 'unavailable');
assert.equal(sample('ica-prox', { flowDirection: [0, 0, 1] }).status, 'unavailable');
assert.equal(sample('ica-prox', { gate: { ...acquisition.gate, radiusFraction: .95 } }).status, 'unavailable');
assert(sample('ica-prox', { angleDeg: 50 }).measurements.psvCmS < peak.measurements.psvCmS);
const away = sample('ica-prox', { beamDirection: [0, -1, 0] });
assert.equal(away.beamDirection, 'away');
assert(Math.abs(away.measurements.psvCmS - peak.measurements.psvCmS) < 1e-8);
assert(Math.abs(away.envelopeCmS[20] + peak.envelopeCmS[20]) < 1e-8);
const color = (segment, phase, radiusFraction, settings = acquisition) =>
  colorVelocityAt(get(segment), settings, { phase, radiusFraction });
assert(color('ica-prox', .166, 0) > color('ica-prox', .166, .7));
assert.equal(color('ica-prox', .166, 1), 0);
assert(color('ica-prox', .166, 0, { ...acquisition, beamDirection: [0, -1, 0] }) < 0);
assert.equal(color('ica-prox', .166, 0, { ...acquisition, flowDirection: [0, 0, 1] }), 0);
assert(color('ica-prox', .166, 0, { ...acquisition, prfHz: 4000 }) < 0);
const samples = ['ica-prox', 'ica-mid', 'ica-dist', 'cca-dist'].map((segment) => sample(segment));
const ratio = icaCcaRatio(samples, 'right');
assert.equal(ratio.numeratorSegment, 'ica-prox');
assert.equal(ratio.denominatorSegment, 'cca-dist');
assert.equal(ratio.ratio, samples[0].measurements.psvCmS / samples[3].measurements.psvCmS);
assert.equal(icaCcaRatio(samples.slice(1), 'right'), null);
assert.equal(icaCcaRatio(samples, 'left'), null);
console.log('Carotid duplex waveform, gate, projection, timing, alias, angle and ratio checks passed.');
