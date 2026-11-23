import catalog from './selected-library.json' with { type: 'json' };
import { decodeLibrary } from './decode-library.js';

export const { candidate, planning } = catalog;
export const { rows, teachingReview } = decodeLibrary(catalog);
