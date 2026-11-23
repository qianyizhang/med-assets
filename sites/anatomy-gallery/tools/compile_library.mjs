// Compile the chosen project's own catalog, reviews and frozen Survey seed.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [project, selection] = process.argv.slice(2);
if (!['candidate', 'published'].includes(selection)) throw Error('Select candidate or published.');
const gallery = resolve(project, 'src/content/gallery');
const read = async (file) => JSON.parse(await readFile(join(gallery, file), 'utf8'));
const { libraryRows } = await import(pathToFileURL(join(gallery, 'library-data.js')));
const { byPath } = await import(pathToFileURL(join(gallery, 'catalog.js')));
const seed = await read('../../data.json');
const review = await read('teaching-inputs/teaching-assessments.json');
const assessments = [...review.assessments, ...(review.campaign ?? [])];
const references = new Map(assessments.map((entry, i) => [entry, i]));
function ref(value) {
  if (value === undefined) return undefined;
  if (!references.has(value)) throw Error('Library assessment has no owning review.');
  return references.get(value);
}
function fileRef(file) {
  return file === byPath.get(file.path) ? file.path : file;
}
function packRecord({ assessment, previousAssessment, fileAssessments, ...record }) {
  if (record.exports) record.exports = record.exports.map(fileRef);
  return { ...record, assessment: ref(assessment), previousAssessment: ref(previousAssessment),
    fileAssessments: fileAssessments && [...fileAssessments.values()].map(ref) };
}
const candidate = selection === 'candidate';
const selected = libraryRows(seed, review, { localPreview: candidate });
const originalRows = new Map([...seed.queries.model_survey.rows, ...seed.queries.products.rows].map(row => [row.id, row]));
const rows = selected.map(({ history, recommended, lessons, ...row }) => {
  const index = (record) => {
    const i = history.indexOf(record);
    if (i < 0) throw Error('Recommended lesson is outside its family history.');
    return i;
  };
  const original = originalRows.get(row.id);
  if (original) {
    for (const key of Object.keys(original)) {
      if (Object.hasOwn(row, key) && row[key] === original[key]) delete row[key];
    }
  }
  if (row.media) row.media = row.media.map(fileRef);
  return { seedId: original?.id, ...packRecord(row), history: history.map(packRecord),
    recommended: recommended && index(recommended), lessons: lessons?.map(index) };
});
// Planning describes the dated Survey and links its original family destinations.
const planning = libraryRows(seed).map(({ id, label, path }) => ({ id, label, path }));
await writeFile(join(gallery, 'selected-library.json'), JSON.stringify({ candidate, rows, planning }));
