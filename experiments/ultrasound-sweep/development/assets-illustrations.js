const illustrations = {
  'mobile-calculus': 'A calculus rests inside the gallbladder lumen.',
  'hepatic-vein': 'Hepatic venous branches converge on the inferior vena cava.',
  'right-hydronephrosis': 'The renal pelvis and upper and lower calyces form a dilated collecting system.',
  'pancreatic-limited-window': 'A gas-filled bowel loop lies in front of the pancreas.',
  'thyroid-suspicious-nodule': 'An irregular thyroid nodule contains small punctate foci.',
  'right-tubal-ectopic-complex': 'An extrauterine sac and yolk sac occupy the right tube beside the ovary.',
  'increased-nuchal-translucency': 'Synthetic scan-style illustration of an enlarged fluid space behind the fetal neck, separate from the amnion.',
  'gallbladder-wall': 'The amber rim marks the requested wall. Green shows the bile-filled lumen.',
};

export function illustrationFor(row) {
  if (row?.source !== 'requirement') return;
  const id = row.part === 'gallbladder-wall' ? row.part :
    row.status === 'rebuild' && row.assetId?.startsWith('required:') ? row.assetId.slice(9) : undefined;
  if (id && illustrations[id]) return {
    src: new URL('./illustrations/' + id + '.webp', import.meta.url).href,
    alt: 'Illustration. ' + illustrations[id], caption: illustrations[id],
  };
}
