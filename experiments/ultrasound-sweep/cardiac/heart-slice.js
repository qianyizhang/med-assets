// Intersect the same triangulated lofts used by the spatial view. The small
// classification offset breaks ties when a plane passes exactly along a mesh edge.
const TIE_BREAK = 1e-6;
const keyOf = ([x, y]) => `${Math.round(x * 1e5)},${Math.round(y * 1e5)}`;

function crossing(a, b, sa, sb, plane) {
  const f = sa / (sa - sb);
  return plane.section([a[0] + (b[0] - a[0]) * f,
    a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]);
}

function triangle(a, b, c, sa, sb, sc, plane, link) {
  const count = (sa > 0) + (sb > 0) + (sc > 0);
  if (count === 0 || count === 3) return;
  if ((sa > 0) !== (sb > 0) && (sa > 0) !== (sc > 0)) {
    link(crossing(a, b, sa, sb, plane), crossing(a, c, sa, sc, plane));
  } else if ((sb > 0) !== (sa > 0) && (sb > 0) !== (sc > 0)) {
    link(crossing(b, a, sb, sa, plane), crossing(b, c, sb, sc, plane));
  } else {
    link(crossing(c, a, sc, sa, plane), crossing(c, b, sc, sb, plane));
  }
}

function meshCut(rings, plane, closed) {
  const graph = new Map();
  const signed = rings.map(ring => ring.map(point => plane.distance(point) + TIE_BREAK));
  function link(a, b) {
    const ka = keyOf(a);
    const kb = keyOf(b);
    if (ka === kb) return;
    if (!graph.has(ka)) graph.set(ka, {point: a, neighbors: new Set()});
    if (!graph.has(kb)) graph.set(kb, {point: b, neighbors: new Set()});
    graph.get(ka).neighbors.add(kb);
    graph.get(kb).neighbors.add(ka);
  }
  for (let row = 1; row < rings.length; row += 1) {
    const a = signed[row - 1], b = signed[row];
    const length = a.length - (closed ? 0 : 1);
    for (let index = 0; index < length; index += 1) {
      const next = (index + 1) % a.length;
      const count = (a[index] > 0) + (a[next] > 0) + (b[index] > 0) + (b[next] > 0);
      if (count === 0 || count === 4) continue;
      const p = rings[row - 1][index], q = rings[row][index];
      const r = rings[row][next], s = rings[row - 1][next];
      triangle(p, q, r, a[index], b[index], b[next], plane, link);
      triangle(p, r, s, a[index], b[next], a[next], plane, link);
    }
  }
  if (closed) {
    for (const row of [0, rings.length - 1]) {
      const ring = rings[row], values = signed[row];
      for (let index = 2; index < ring.length; index += 1) {
        triangle(ring[0], ring[index - 1], ring[index], values[0], values[index - 1], values[index], plane, link);
      }
    }
  }
  const paths = [];
  const starts = [...graph.keys()].sort((a, b) => graph.get(a).neighbors.size - graph.get(b).neighbors.size);
  for (const first of starts) {
    const start = graph.get(first);
    while (start.neighbors.size > 0) {
      const points = [start.point];
      let key = first;
      while (graph.get(key).neighbors.size > 0) {
        const {neighbors} = graph.get(key);
        const next = neighbors.values().next().value;
        neighbors.delete(next);
        graph.get(next).neighbors.delete(key);
        points.push(graph.get(next).point);
        if (next === first) break;
        key = next;
      }
      if (points.length > (closed ? 3 : 1)) paths.push(points);
    }
  }
  return paths;
}

export function polygonArea(points) {
  let total = 0;
  for (let i = 0; i < points.length; i += 1) {
    const a = points[i], b = points[(i + 1) % points.length];
    total += a[0] * b[1] - a[1] * b[0];
  }
  return Math.abs(total) / 2;
}

export function heartSection(frame, plane) {
  const chambers = Object.fromEntries(Object.entries(frame.chambers).map(([name, {wall, lumen}]) => [name, {
    wall: meshCut(wall, plane, true), lumen: meshCut(lumen, plane, true),
  }]));
  for (const [name, vessel] of Object.entries(frame.vessels)) {
    chambers[name] = {
      wall: vessel.wall.flatMap(rings => meshCut(rings, plane, true)),
      lumen: vessel.lumen.flatMap(rings => meshCut(rings, plane, true)),
    };
  }
  const valveCuts = frame.details.filter(({material}) => material === 'leaflet')
    .flatMap(({name, rings}) => meshCut(rings, plane, false).map(points => ({name, points})));
  const muscleCuts = frame.details.filter(({material}) => material === 'muscle')
    .flatMap(({rings}) => meshCut(rings, plane, true));
  return {chambers, valveCuts, muscleCuts};
}

export function largestContour(paths) {
  return paths.reduce((largest, path) => polygonArea(path) > polygonArea(largest) ? path : largest, []);
}
