import {COVERAGE, COPY} from './plate.mjs';
import {mount} from './ui.mjs';

try {
  const response = await fetch(new URL(COVERAGE, import.meta.url));
  if (!response.ok) throw Error(`Coverage HTTP ${response.status}`);
  mount(document.querySelector('#lesson'), await response.json());
} catch {
  document.querySelector('#boot').textContent = `${COPY.en.dataError} / ${COPY.zh.dataError}`;
}
