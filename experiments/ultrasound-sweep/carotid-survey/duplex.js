// Synthetic pulsed and color Doppler for a normal teaching model.
const SOUND_SPEED_M_S = 1540;
const DEFAULT_FREQUENCY_MHZ = 5;
const DEFAULT_PRF_HZ = 6500;
const DEFAULT_HEART_RATE_BPM = 69;
const CYCLES = 3;
const SAMPLES_PER_BEAT = 120;
const SPECTRAL_BINS = 161;

const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const dot = (a, b) => a.reduce((value, element, index) => value + element * b[index], 0);
const wrap = (value, interval) => ((value % interval) + interval) % interval;
const radians = (degrees) => degrees * Math.PI / 180;

/** Resolve the shared waveform profiles for the discrete station list. */
export function duplexStations(protocol) {
  return protocol.stations.map((station) => {
    if (!station.waveformProfile) return station;
    const waveform = protocol.waveformProfiles[station.waveformProfile];
    if (!waveform) throw new Error(`Missing waveform for ${station.id}`);
    return { ...station, waveform };
  });
}

function unit(vector) {
  if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(Number.isFinite)) return null;
  const length = Math.hypot(...vector);
  return length > 0 ? vector.map((value) => value / length) : null;
}

function validRange(value, min, max) {
  return Number.isFinite(value) && value >= min && value <= max;
}

function projection(acquisition) {
  const beam = unit(acquisition?.beamDirection);
  const flow = unit(acquisition?.flowDirection);
  return beam && flow ? clamp(-dot(beam, flow), -1, 1) : null;
}

function settings(acquisition) {
  const frequencyMHz = acquisition.frequencyMHz ?? DEFAULT_FREQUENCY_MHZ;
  const prfHz = acquisition.prfHz ?? DEFAULT_PRF_HZ;
  if (!validRange(frequencyMHz, 1, 20) || !validRange(prfHz, 500, 30000)) return null;
  const hertzPerCmS = 2 * frequencyMHz * 1e6 / (SOUND_SPEED_M_S * 100);
  return { prfHz, hertzPerCmS };
}

function radialVelocity(radiusFraction) {
  return Math.max(0, 1 - radiusFraction**2.7);
}

function modelVelocity(station, phase, radiusFraction) {
  const { waveform, velocityScale = 1 } = station;
  if (!waveform || radiusFraction >= 1) return 0;
  const t = wrap(phase, 1);
  const right = waveform.findIndex(([clock]) => clock > t);
  const [leftTime, leftVelocity] = waveform[right - 1];
  const [rightTime, rightVelocity] = waveform[right];
  // Smooth analytic envelope. Pulsatility is illustrative, not patient-derived.
  const blend = (t - leftTime) / (rightTime - leftTime);
  const smooth = blend * blend * (3 - 2 * blend);
  return (leftVelocity + (rightVelocity - leftVelocity) * smooth) * radialVelocity(radiusFraction) * velocityScale;
}

function fold(signedShiftHz, prfHz) {
  return wrap(signedShiftHz + prfHz / 2, prfHz) - prfHz / 2;
}

/** Positive is flow toward the probe. Color uses raw, uncorrected axial velocity. */
export function colorVelocityAt(station, acquisition, { phase, radiusFraction }) {
  const axial = projection(acquisition);
  const config = settings(acquisition ?? {});
  if (axial === null || !config || !Number.isFinite(phase) || !validRange(radiusFraction, 0, 1)) return null;
  const { hertzPerCmS, prfHz } = config;
  const velocity = modelVelocity(station, phase, radiusFraction) * axial;
  return fold(velocity * hertzPerCmS, prfHz) / hertzPerCmS;
}

/** Adapt one calibrated 3D station gate to the spectral sampler. */
export function registeredAcquisition(gate, options = {}) {
  if (!gate || gate.steeringSupported === false) return null;
  return {
    ...options,
    beamDirection: gate.beamDirection,
    flowDirection: gate.flowDirection,
    gate: {
      radiusFraction: options.radiusFraction ?? gate.radiusFraction ?? 0,
      lengthMm: options.lengthMm ?? Math.min(2, gate.diameterMm * .5),
      lumenDiameterMm: gate.diameterMm,
    },
  };
}

/** Receiver power rows are ordered by time; bins are ascending signed cm/s. */
export function duplexSample(station, acquisition) {
  const unavailable = (reason) => ({ status: 'unavailable', reason, measurements: null });
  if (!station.waveform) return unavailable('This station has an anatomical view only.');
  if (!acquisition) return unavailable('No registered Doppler gate.');
  const axial = projection(acquisition);
  const config = settings(acquisition);
  const heartRateBpm = acquisition.heartRateBpm ?? DEFAULT_HEART_RATE_BPM;
  if (axial === null || !config || !validRange(heartRateBpm, 30, 200)) {
    return unavailable('Invalid Doppler geometry or instrument settings.');
  }

  const actualAngleDeg = Math.acos(Math.abs(axial)) * 180 / Math.PI;
  const angleDeg = acquisition.angleDeg ?? actualAngleDeg;
  if (!validRange(angleDeg, 0, 60 + 1e-8) || actualAngleDeg > 60 + 1e-8) {
    return unavailable('A usable spectral beam and correction angle must be 60° or less.');
  }
  const gate = acquisition.gate;
  if (!gate || !validRange(gate.radiusFraction, 0, 1) || !validRange(gate.lengthMm, .2, 10)
      || !validRange(gate.lumenDiameterMm, .5, 35)) return unavailable('No valid registered sample gate.');

  const radialHalfSpan = gate.lengthMm * Math.sin(radians(actualAngleDeg)) / gate.lumenDiameterMm;
  if (gate.radiusFraction + radialHalfSpan >= 1) return unavailable('Keep the Doppler gate inside the lumen.');

  const period = 60 / heartRateBpm;
  const { hertzPerCmS, prfHz } = config;
  const correction = Math.cos(radians(angleDeg));
  const nyquistCmS = prfHz / (2 * hertzPerCmS * correction);
  const binStep = 2 * nyquistCmS / (SPECTRAL_BINS - 1);
  const velocityBinsCmS = Array.from({ length: SPECTRAL_BINS }, (_, index) => index * binStep - nyquistCmS);
  const timeSeconds = [], power = [], envelopeCmS = [];
  const near = Math.max(0, gate.radiusFraction - radialHalfSpan);
  let aliased = false;
  for (let i = 0; i <= CYCLES * SAMPLES_PER_BEAT; i += 1) {
    const phase = (i % SAMPLES_PER_BEAT) / SAMPLES_PER_BEAT;
    const axialEdge = modelVelocity(station, phase, near) * axial;
    const peakHz = axialEdge * hertzPerCmS;
    aliased ||= Math.abs(peakHz) >= prfHz / 2;
    timeSeconds.push(i * period / SAMPLES_PER_BEAT);
    envelopeCmS.push(fold(peakHz, prfHz) / (hertzPerCmS * correction));
    const row = new Float32Array(SPECTRAL_BINS);
    for (let scatter = 0; scatter < 19; scatter += 1) {
      const fraction = scatter / 18;
      const offset = gate.radiusFraction + radialHalfSpan * (2 * fraction - 1);
      const speed = modelVelocity(station, phase, Math.abs(offset)) * axial;
      const samplingWidthHz = 1.1 * binStep * hertzPerCmS * correction;
      const shiftHz = speed * hertzPerCmS - Math.sign(speed) * samplingWidthHz * (scatter % 4) * .75;
      if (Math.abs(shiftHz) < 23) continue;
      const bin = Math.round((fold(shiftHz, prfHz) / (hertzPerCmS * correction) + nyquistCmS) / binStep);
      const weight = .30 + .54 * Math.sin(Math.PI * fraction);
      for (let delta = -2; delta <= 2; delta += 1) {
        const k = Math.max(0, Math.min(SPECTRAL_BINS - 1, bin + delta));
        const signal = weight * Math.exp(-delta * delta / 2);
        row[k] = 1 - (1 - row[k]) * (1 - signal);
      }
    }
    power.push(row);
  }

  let measurements = null;
  if (!aliased) {
    const sign = Math.sign(axial);
    const end = CYCLES * SAMPLES_PER_BEAT;
    const start = end - SAMPLES_PER_BEAT;
    let peak = start;
    for (let i = start + 1; i < end; i += 1) {
      if (sign * envelopeCmS[i] > sign * envelopeCmS[peak]) peak = i;
    }
    measurements = {
      psvCmS: sign * envelopeCmS[peak], edvCmS: sign * envelopeCmS[end],
      psvTimeSeconds: timeSeconds[peak], edvTimeSeconds: timeSeconds[end],
    };
  }
  return {
    status: aliased ? 'aliased' : 'measured', actualAngleDeg, angleDeg,
    beamDirection: axial > 0 ? 'toward' : 'away',
    physiologicalDirection: station.physiologicalDirection,
    side: station.side, segment: station.segment, timeSeconds, power,
    velocityBinsCmS, envelopeCmS, rangeCmS: [-nyquistCmS, nyquistCmS], measurements,
  };
}

/** The denominator is the ipsilateral distal CCA. An incomplete ratio stays unavailable. */
export function icaCcaRatio(samples, side) {
  const ipsilateral = samples.filter((sample) => sample.side === side && sample.measurements);
  const cca = ipsilateral.find((sample) => sample.segment === 'cca-dist');
  const ica = ['ica-prox', 'ica-mid', 'ica-dist'].map((segment) =>
    ipsilateral.find((sample) => sample.segment === segment));
  if (!(cca?.measurements.psvCmS > 0) || ica.some((sample) => !sample)) return null;
  const peakIca = ica.reduce((peak, sample) => sample.measurements.psvCmS > peak.measurements.psvCmS ? sample : peak);
  return {
    ratio: peakIca.measurements.psvCmS / cca.measurements.psvCmS,
    numeratorSegment: peakIca.segment, denominatorSegment: cca.segment,
  };
}
