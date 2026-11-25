// Export the same authored surfaces, acquisition frames and calipers used by the vascular case records.
import { readFileSync } from 'node:fs';
import { chapters } from './cases/vascular/playable.js';
import { aorticLength, aorticSurfaces } from './cases/vascular/playable-aorta.js';
import { getAcquisition, getTube, measure, split, tubesAt } from './cases/vascular/playable-model.js';

const records = JSON.parse(readFileSync(0, 'utf8'));
const sampleIntervalMm = .25;

function chapterData(record, chapter) {
  const frames = Array.from({ length: chapter.frames }, (_, number) => {
    const acq = getAcquisition(record, chapter, number);
    const previous = getTube(record, null, acq.z - 2, chapter.target);
    const next = getTube(record, null, acq.z + 2, chapter.target);
    return {
      z: acq.z,
      target: [acq.target?.x ?? 0, acq.target?.y ?? 47, acq.z],
      long: acq.long,
      slope: previous && next ? (next.x - previous.x) / 4 : 0,
      window: chapter.window ?? 'anterior',
      limited: acq.blind,
      calipers: measure(record, chapter, number, acq).map(({ z, x, y, lo, hi, transverse = false }) => ({
        transverse,
        endpoints: transverse ? [[lo, y, z], [hi, y, z]] : [[x, lo, z], [x, hi, z]],
      })),
    };
  });
  return { id: chapter.id, frames, evidenceFrame: chapter.evidenceFrame, color: Boolean(chapter.color) };
}

function modelData(record) {
  const samples = Array.from({ length: aorticLength / sampleIntervalMm + 1 }, (_, i) =>
    tubesAt(record, null, i * sampleIntervalMm).map(({ x, y, rx, ry, lx, ly, lrx, lry, wall, color, mural }) =>
      [x, y, rx, ry, lx, ly, lrx, lry, wall, color, Number(Boolean(mural))]));
  const surfaces = Object.fromEntries(aorticSurfaces(record).map(({kind, vertices, faces}) =>
    [kind, { vertices: vertices.map(({x,y,z}) => [x,y,z]), faces }]));
  return { samples, surfaces };
}

const modelCase = (record) => record.kind === 'abnormal' ? 'positive' : 'normal';
const models = {};
const cases = records.map((record) => {
  const model = modelCase(record);
  models[model] ??= modelData(record);
  return { id: record.id, model, chapters: chapters(record).map((chapter) => chapterData(record, chapter)) };
});
process.stdout.write(JSON.stringify({ models, cases, sampleIntervalMm, bifurcationMm: split }));
