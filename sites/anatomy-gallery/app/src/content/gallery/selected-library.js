import catalog from './selected-library.json' with { type: 'json' };
import review from './teaching-inputs/teaching-assessments.json' with { type: 'json' };
import seed from '../../data.json' with { type: 'json' };
import { byPath } from './catalog.js';

const assessments = [...review.assessments, ...(review.campaign ?? [])];
const originals = new Map([...seed.queries.model_survey.rows, ...seed.queries.products.rows].map(row => [row.id, row]));
const file = (entry) => typeof entry === 'string' ? byPath.get(entry) : entry;
function record(entry) {
  return { ...entry, exports: entry.exports?.map(file), assessment: assessments[entry.assessment],
    previousAssessment: assessments[entry.previousAssessment],
    fileAssessments: entry.fileAssessments && new Map(entry.fileAssessments.map((index) => {
      const assessment = assessments[index];
      return [assessment.export.path, assessment];
    })) };
}
export const { candidate, planning } = catalog;
export const rows = catalog.rows.map(({ seedId, ...entry }) => {
  const history = entry.history.map(record);
  const original = originals.get(seedId);
  return { ...original, ...record(entry), media: (entry.media ?? original?.media)?.map(file),
    history, recommended: history[entry.recommended],
    lessons: entry.lessons?.map((i) => history[i]) };
});
