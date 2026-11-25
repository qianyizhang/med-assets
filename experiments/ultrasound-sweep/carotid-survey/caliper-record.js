// Project the measured lumen's near and far wall witnesses into the displayed plane.
export function distalCcaCalipers(station, view) {
  if (station?.segment !== 'cca-dist' || view !== station.views?.longitudinal) return null;
  const endpoints = station.gate?.wallPoints;
  if (endpoints?.length !== 2 || !(view.mmPerPx > 0)) return null;
  const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
  const points = [];
  for (const point of endpoints) {
    const delta = point.map((v, i) => v - view.contact[i]);
    const across = dot(delta, view.width);
    const depth = dot(delta, view.beam);
    const offPlane = delta.map((v, i) => v - across * view.width[i] - depth * view.beam[i]);
    if (Math.hypot(...offPlane) > .02) return null;
    const x = view.centerPx[0] + across / view.mmPerPx;
    const y = view.centerPx[1] + depth / view.mmPerPx;
    if (!(x >= 0 && x < view.widthPx && y >= 0 && y < view.heightPx)) return null;
    points.push([x, y]);
  }
  const [a, b] = points;
  const lengthMm = Math.hypot(a[0] - b[0], a[1] - b[1]) * view.mmPerPx;
  if (!(lengthMm > 0) || Math.abs(lengthMm - station.gate.diameterMm) > .025) return null;
  return { points, lengthMm, record: {
    side: station.side, segment: station.segment, label: station.label,
    type: 'Modeled lumen span', value: lengthMm.toFixed(1) + ' mm',
    acquisition: 'Long axis · inner walls', frame: view.path, endpointsPx: points, lengthMm,
  } };
}
