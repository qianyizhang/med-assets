import { spectra } from '../../cardiac/measure/protocol.js';
const scaled = (s, f) => ({ knots: s.knots.map(([t, v]) => [t, v * f]) });
export const flowCase = {
  knots: [
    [0.035, 0],
    [0.085, -215],
    [0.155, -391],
    [0.205, -454],
    [0.255, -443],
    [0.315, -360],
    [0.36, -220],
    [0.4, 0],
  ],
};
export const apical = scaled(flowCase, 0.79);

export const lvotPW = scaled(spectra.lvot, 0.95);
