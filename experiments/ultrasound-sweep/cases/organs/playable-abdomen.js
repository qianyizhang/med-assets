import {chapterFor, measure, tissue} from './playable-geometry.js';

const liver = [-48, 58, 25];
const leftLiver = [22, 39, 46];
const gallbladder = [-42, 69, 16];
const duct = [-27, 55, 21];
const pancreas = [12, 69, 28];
const spleen = [86, 50, 26];
const rightKidney = [-72, 76, -18];
const leftKidney = [76, 73, -12];
const bladder = [0, 57, -116];
const aorta = [-10, 93, 0];
const portal = [-25, 61, 28];
const hepatic = [-46, 54, 57];

function renalVolume(center, length, collectingDilatation, side) {
  const [x,y,z] = center;
  const kidney = tissue(`${side} kidney`, center, [24, 21, length / 2], 98, {label: `${side} kidney cortex`});
  const sinus = tissue(`${side} renal sinus`, [x,y+3,z], [12,12,length*.33], 174);
  if (!collectingDilatation) return [kidney, sinus];
  return [kidney, sinus, tissue('Dilated renal pelvis', [x+4,y+2,z], [9,8,16], 16),
    tissue('Upper calyx', [x,y+1,z+17], [7,7,12], 17),
    tissue('Lower calyx', [x,y+3,z-17], [7,7,12], 17)];
}

export function abdominalVolume(record, chapter) {
  const hydronephrosis = record.id === 'abdomen-renal-obstruction';
  const stone = record.id === 'abdomen-biliary-stone';
  const rolled = chapter.position === 'Left lateral decubitus';
  const postvoid = chapter.position === 'Supine after voiding';
  const stonePoint = [-42, rolled ? 69 : 78, rolled ? 29 : 7];
  return [
    tissue('Right hepatic lobe', liver, [57,45,72.15], 128),
    tissue('Left hepatic lobe', leftLiver, [57,28,36], 124),
    tissue('Diaphragm', [-43,98,70], [58,4,24], 188),
    tissue('Hepatic vein wall', hepatic, [4,5,31], 161),
    tissue('Hepatic vein', hepatic, [3,4,29], 23, {flow: 'hepatic'}),
    tissue('Main portal vein wall', portal, [6,7,30], 187),
    tissue('Main portal vein', portal, [5,6,27], 24, {flow: 'portal'}),
    tissue('Gallbladder wall', gallbladder, [15,14,40], 159),
    tissue('Gallbladder lumen', gallbladder, [13,12,38], 13),
    tissue('Extrahepatic duct walls', duct, [3,3,28], 174),
    tissue('Extrahepatic duct', duct, [2,2,27], 14),
    ...(stone ? [tissue('Mobile calculus', stonePoint, [4.5,3.2,5], 240, {shadow: .90})] : []),
    tissue('Pancreatic head', [-21,68,24], [24,12,18], 144),
    tissue('Uncinate process', [-18,78,19], [15,8,11], 144),
    tissue('Pancreatic body', pancreas, [41,9,13], 141),
    tissue('Pancreatic tail', [60,64,31], [27,8,11], 143),
    tissue('Splenic vein', [17,78,28], [52,3,4], 25),
    tissue('Spleen', spleen, [27,31,56.95], 133),
    tissue('Splenic hilum', [70,66,26], [8,8,12], 94),
    ...renalVolume(rightKidney, hydronephrosis ? 112 : 107, hydronephrosis, 'Right'),
    ...renalVolume(leftKidney, 113, false, 'Left'),
    tissue('Vertebral interface', [-2,110,-3], [16,7,94], 181, {shadow: .75}),
    tissue('Aorta', aorta, [10,9,95], 197),
    tissue('Aortic lumen', aorta, [8.5,7.5,94], 18),
    tissue('IVC', [14,88,4], [12,7,94], 23, {flow:'caval'}),
    tissue('Bladder wall', bladder, postvoid ? [22,12,17] : [43,29,38], 158),
    tissue('Bladder lumen', bladder, postvoid ? [20,10,15] : [41,27,36], 13),
    ...(postvoid ? [] : [tissue('Right UVJ', [-28,79,-117], [3,4,4], 110),
      tissue('Left UVJ', [28,79,-117], [3,4,4], 108)]),
    ...(record.id === 'abdomen-limited-pancreas'
      ? [tissue('Bowel gas', chapter.position === 'Left lateral reattempt' ? [27,30,33] : [28,24,26],
          [62,6,23], 218, {shadow: .97})]
      : [])
  ];
}

export function abdominalChapters(record) {
  const abd = (key, target, settings = {}) => chapterFor(record, key, {target, depth: 145, ...settings});
  const right = (key, transverse = false, settings = {}) => abd(key, rightKidney, {
    axis: transverse ? 0 : 2, sweep: transverse ? [-48,48] : [-24,24],
    marks: transverse ? [] : [measure('Right kidney','width')], ...settings
  });
  const left = (key, transverse = false, settings = {}) => abd(key, leftKidney, {
    axis: transverse ? 0 : 2, sweep: transverse ? [-48,48] : [-24,24],
    marks: transverse ? [] : [measure('Left kidney','width')], ...settings
  });
  const ductChapter = () => abd('abd-cbd', duct, {axis:2, depth:110, sweep:[-9,9], colorIds:['Main portal vein'],
    marks:[measure('Extrahepatic duct','depth')]});
  const gall = (key, settings = {}) => abd(key, gallbladder, {axis:2, sweep:[-14,14], depth:120,
    marks:[measure('Gallbladder wall','wall','Gallbladder lumen')], ...settings});
  const hepaticChapter = () => abd('abd-liver', liver, {axis:2, marks:[measure('Right hepatic lobe','width')],
    sweep:[-46,46]});
  const pancreatic = () => abd('abd-pancreas-limited', pancreas, {target:[22,69,28], sweep:[-25,25]});
  const spleenChapter = () => abd('abd-spleen', spleen, {axis:2, sweep:[-26,26],
    marks:[measure('Spleen','width')], position:'Right lateral decubitus'});
  const aortic = () => abd('abd-vessels', aorta, {sweep:[-82,88], marks:[measure('Aorta','depth')]});
  const additional = (chapter, id, title, observation, settings) => ({
    ...chapter, id, title, observation, measurement:undefined, marks:[], ...settings,
  });
  const leftLobe = () => abd('abd-left-liver', leftLiver, {sweep:[-30,34]});
  const ivcLong = () => additional(aortic(), 'ivc-long', 'IVC · long axis and hepatic confluence',
    'Align the sagittal section along the cava. Follow the patent lumen to the hepatic window.',
    {target:[14,88,25], axis:2, depth:145, sweep:[-15,15], colorIds:['IVC']});
  const aortaLong = () => additional(aortic(), 'aorta-long', 'Aorta · long axis',
    'Reorient from the transverse survey to the longitudinal axis and follow the parallel aortic walls.',
    {axis:2, sweep:[-14,14]});
  const liverTrans = () => additional(hepaticChapter(), 'liver-trans', 'Right hepatic lobe · transverse',
    'Sweep cranially and caudally through the right hepatic tissue and portal branches.',
    {axis:0, sweep:[-60,60]});
  const spleenTrans = () => additional(spleenChapter(), 'spleen-trans', 'Spleen · short axis and hilum',
    'Rotate through the splenic parenchyma and hilum.', {axis:0, sweep:[-52,52]});
  if (record.id === 'abdomen-biliary-stone') {
    return [gall('biliary-stone-supine', {position:'Supine'}),
      additional(gall('biliary-stone-supine'), 'biliary-stone-transverse', 'Gallbladder · short axis and neck',
        'Rotate and translate from neck to fundus. The calculus produces a posterior shadow.',
        {axis:0, sweep:[-39,39]}),
      gall('biliary-stone-roll', {position:'Left lateral decubitus'}), ductChapter()];
  }
  if (record.id === 'abdomen-renal-obstruction') {
    return [right('renal-right-hydro'), right('renal-right-hydro-trans', true), left('abd-left-kidney'),
      left('abd-left-kidney-trans', true), abd('renal-bladder', bladder, {sweep:[-35,35]}),
      abd('renal-bladder-sagittal', bladder, {axis:2, sweep:[-40,40]}),
      additional(abd('renal-bladder', bladder), 'bladder-uvj', 'Bladder base and bilateral ureterovesical junctions',
        'Fan across the posterolateral bladder base and inspect both ureterovesical junction regions. The modeled images show no visible distal calculus or UVJ mass.',
        {target:[0,66,-117], depth:115, sweep:[-8,9]}),
      additional(abd('renal-bladder-sagittal', bladder), 'bladder-postvoid', 'Bladder · postvoid',
        'Confirm bladder emptying before comparing the collecting system.', {axis:2, position:'Supine after voiding'}),
      right('renal-right-postvoid', false, {position:'Supine after voiding'})];
  }
  if (record.id === 'abdomen-limited-pancreas') {
    return [pancreatic(), {...pancreatic(), id:'pancreas-retry', title:'Pancreas · left lateral repeat',
      position:'Left lateral reattempt', sweep:[-10,28],
      observation:'The gas interface shifts, but the pancreatic body and tail still lie below shadow. The head remains accessible.'},
      hepaticChapter(), liverTrans(), gall('abd-gb'), additional(gall('abd-gb'), 'gb-short-limited-visit',
        'Gallbladder · short axis', 'Sweep the lumen to the fundus.', {axis:0, sweep:[-39,39]}),
      ductChapter(), spleenChapter(), spleenTrans(),
      right('abd-right-kidney'), additional(right('abd-right-kidney',true), 'right-renal-trans','Right kidney · short axis',
        'Record the visible right renal sinus and cortex.', {}), left('abd-left-kidney'),
      additional(left('abd-left-kidney', true), 'left-renal-trans','Left kidney · short axis',
        'Record the visible left renal sinus and cortex.', {}), aortic(), aortaLong(), ivcLong()];
  }
  return [
    hepaticChapter(), liverTrans(), leftLobe(),
    abd('abd-portal-doppler', portal, {axis:2, depth:110, sweep:[-6,6], spectral:'portal', colorIds:['Main portal vein']}),
    abd('abd-hepatic-vein-doppler', hepatic, {axis:2, depth:110, sweep:[-6,6], spectral:'hepatic', colorIds:['Hepatic vein']}),
    gall('abd-gb'), gall('abd-gb-short', {axis:0, marks:[], sweep:[-39,39]}), ductChapter(),
    abd('abd-pancreas', pancreas, {sweep:[-18,18]}),
    additional(abd('abd-pancreas', pancreas), 'pancreatic-head', 'Pancreatic head and uncinate region',
      'Follow the head from a right-sided parasagittal window and fan into the uncinate region.',
      {target:[-21,68,24], axis:2, sweep:[-18,18]}),
    abd('abd-tail', [65,64,31], {sweep:[-14,13], position:'Right lateral decubitus · splenic window'}),
    spleenChapter(), spleenTrans(), right('abd-right-kidney'), right('abd-right-kidney-trans', true),
    left('abd-left-kidney'), left('abd-left-kidney-trans', true), aortic(), aortaLong(), ivcLong(),
  ];
}
