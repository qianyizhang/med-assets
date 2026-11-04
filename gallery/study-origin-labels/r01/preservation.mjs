// Reverse only the two pinned presentation edits for historical source assertions.
// No data, media or historical evidence is rewritten.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const sha = raw => createHash('sha256').update(raw).digest('hex');
export function withoutAssetEntryLabels(raw) {
  assert.equal(sha(raw), 'fa4a23fed7337b996c1e79445e3343c9987ed9c8621ce88b4a871a1df15fc1d1', 'Exact asset-entry classification renderer required');
  const prior = raw.toString()
    .replace("'素材条目 · '+data.assets.length:'Asset entries · '+data.assets.length", "'原始素材 · '+data.assets.length:'Original assets · '+data.assets.length")
    .replace("(c.hasBaseline===false?(lang==='zh'?'仅研究条目（无原始基线）':'Study-only entry (no baseline)'):(lang==='zh'?'原版':'Original'))", "(lang==='zh'?'原版':'Original')");
  assert.equal(sha(prior), '246bdc98312f9075d9195170aecd5d1917ec8828218c677b7dd24d8f38463467', 'Reversing only two labels must restore exact #210 renderer');
  return Buffer.from(prior);
}
