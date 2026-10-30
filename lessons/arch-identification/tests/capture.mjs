// Exact shared plate SVG, rendered offline with Inkscape. Not an HTML/browser screenshot.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {plateSVG, plateHeight, initialState, COPY, describe, escapeXML} from '../plate.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const out = path.resolve(process.argv[2] || '');
if (!process.argv[2]) throw Error('Provide a new output directory');
await fs.mkdir(out, {recursive: false});
const media = path.relative(out, root + '/reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media') + '/';
const records = [];
for (const [name, arch, lang, fdi, width, original, available] of [
  ['original-upper', 'upper', 'en', '11', 640, true, true],
  ['updated-upper-en', 'upper', 'en', '11', 640, false, true],
  ['updated-lower-zh', 'lower', 'zh', '31', 640, false, true],
  ['narrow-upper-en', 'upper', 'en', '17', 292, false, true],
  ['narrow-lower-zh', 'lower', 'zh', '47', 292, false, true],
  ['missing-lower-zh', 'lower', 'zh', '41', 292, false, false],
]) {
  const state = initialState(); state.arch = arch; state.lang = lang;
  state.selected[arch] = fdi; state.image[arch] = available;
  const c = COPY[lang], info = describe(fdi, lang), height = width * plateHeight(state, width) / 1100;
  // The framing is a review caption. Only the nested plate is the live component.
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height + 120}" viewBox="0 0 ${width} ${height + 120}">
  <rect width="100%" height="100%" fill="#11181b"/>
  <g fill="#d9e9e7" font-family="sans-serif" font-size="12"><text x="12" y="20">${escapeXML(c[arch])}</text>
  <text x="12" y="43">${c[arch === 'upper' ? 'right' : 'left']}</text><text x="${width-12}" y="43" text-anchor="end">${c[arch === 'upper' ? 'left' : 'right']}</text></g>
  <g transform="translate(0 54)">${plateSVG(state, width, {media, original})}</g>
  <g fill="#a8f0df" font-family="sans-serif" font-size="12"><text x="12" y="${height + 76}">${original ? 'Original · unchanged source image' : escapeXML(`FDI ${fdi} · ${info.side} · ${info.class}`)}</text><text x="12" y="${height + 100}">${available ? 'Offline shared SVG · not browser evidence' : escapeXML(c.unavailable)}</text></g></svg>`;
  await fs.writeFile(path.join(out, name + '.svg'), svg);
  records.push({name, arch, lang, fdi, plateWidth: width, original, imageAvailable: available});
}
await fs.writeFile(path.join(out, 'states.json'), JSON.stringify(records, null, 2) + '\n');
console.log(out);
