import {chapterFor, measure, tissue} from './playable-geometry.js';

const nodule = [-15, 20, -8];
const thyroidRight = [-15, 20, 0];
const thyroidLeft = [15, 20, 0];

export function thyroidVolume(record, chapter) {
  const obscured = record.id === 'thyroid-limited';
  return [
    tissue('Strap muscle', [0,10,0], [31,2.5,31], 71),
    tissue('Right lobe', thyroidRight, [10.35,7.5,24], 136),
    tissue('Left lobe', thyroidLeft, [9.5,7,22], 132),
    tissue('Isthmus', [0,16,0], [9,1.5,13], 134),
    tissue('Tracheal air interface', [0,25,0], [8,7,35], 199, {shadow: .83}),
    tissue('Right carotid', [-29,23,0], [3.5,3.5,44], 15),
    tissue('Left carotid', [29,23,0], [3.5,3.5,44], 15),
    ...(record.id === 'thyroid-nodule' ? [tissue('Solid hypoechoic nodule', nodule, [4,5.5,7], 86)] : []),
    ...[-1,1].flatMap(side => [
      tissue(`${side < 0 ? 'Right' : 'Left'} jugular vein`, [side*34,21,0], [4,3,44], 21),
      tissue(`${side < 0 ? 'Right' : 'Left'} lateral node`, [side*37,22,9], [2.5,2.5,7], 86),
      tissue('Echogenic fatty hilum', [side*37,22,9], [1.2,1.1,4], 162)
    ]),
    ...(obscured ? [tissue('Clavicle', [chapter.position === 'Angled suprasternal repeat' ? 13.5 : 15,9,-20],
      [11,2.5,9], 222, {shadow:.98})] : [])
  ];
}

export function thyroidChapters(record) {
  const thy = (key, target, settings = {}) => chapterFor(record, key, {
    target, depth:46, sweep:[-23,23], linear:true, ...settings
  });
  const diameters = ['Right lobe','Left lobe'].flatMap(id => [measure(id,'width'),measure(id,'depth')]);
  diameters.push(measure('Isthmus','depth'));
  const hasNodule = record.id === 'thyroid-nodule';
  const limited = record.id === 'thyroid-limited';
  const transverse = thy(hasNodule ? 'thyroid-axial-superior' : 'thyroid-axial', [0,20,0], {marks:diameters});
  const right = thy(hasNodule ? 'thyroid-right-long-nodule' : 'thyroid-right-long', thyroidRight,
    {axis:2, sweep:[-10,10], marks:[measure('Right lobe','width')]});
  const left = thy(limited ? 'thyroid-long-limited' : 'thyroid-left-long', thyroidLeft,
    {axis:2, sweep:[-9,9], marks:limited ? [] : [measure('Left lobe','width')]});
  const nodal = thy('thyroid-node', [-37,22,9], {axis:2, depth:42,sweep:[-6,6], marks:[measure('Right lateral node','depth')]});
  return [
    transverse, right, left,
    ...(limited ? [{...left, id:'thyroid-left-lower-retry', title:'Left inferior pole · angled repeat',
      position:'Angled suprasternal repeat', target:[16,20,-5], sweep:[-7,7],
      observation:'The altered approach shifts the clavicular interface, but the shadow continues across the inferior pole. An index nodule measurement is withheld.'}]
      : []),
    ...(hasNodule ? [
      thy('thyroid-nodule-trans', nodule, {depth:34,sweep:[-9,9],marks:[measure('Solid hypoechoic nodule','width'),measure('Solid hypoechoic nodule','depth')]}),
      thy('thyroid-nodule-long', nodule, {axis:2,depth:34,sweep:[-6,6],marks:[measure('Solid hypoechoic nodule','width')]}),
    ] : []),
    {...nodal,title:'Right lateral cervical chain · level III sample'},
    {...nodal,id:'thyroid-node-left',title:'Left lateral cervical chain',target:[37,22,9],marks:[],measurement:undefined,
      observation:'The visible left lateral node is elongated with a preserved echogenic hilum.'},
    {...nodal,id:'thyroid-node-central',title:'Central cervical compartments',target:[0,22,-15],axis:0,sweep:[-14,21],marks:[],measurement:undefined,
      observation:limited ? 'Inspect the central compartment visible above the clavicular shadow.'
        : 'Sweep the visible pretracheal and bilateral paratracheal tissues. No suspicious node is modeled in the central compartment.'},
  ];
}

const rightX = -53;
const leftX = 53;
const cyst = [55,18,10];
const node = [-112,22,55];
const otherNode = [112,22,55];

function normalBreast(x) {
  return [
    tissue('Chest wall', [x,38,0], [58,7,74], 82),
    tissue('Pectoral fascia', [x,32,0], [58,1.5,72], 188),
    tissue('Subcutaneous fat', [x,11,0], [49,8,59], 73),
    tissue('Fibroglandular tissue', [x,20,0], [45,10,53], 130),
    tissue('Fibroglandular tail', [x*1.58,18,34], [26,6,29], 125),
    tissue('Echogenic septum', [x*.89,13,12], [25,1,42], 179),
    tissue('Skin', [x,2,0], [54,1.25,64], 183),
    tissue('Normal duct', [x,12,6], [2,2,13], 48),
  ];
}

export function breastVolume(record, chapter) {
  const [x,y,z] = node;
  const [lx,ly,lz] = otherNode;
  const focus = record.id;
  const incomplete = focus === 'breast-limited';
  const rightAbnormal = focus === 'breast-axillary-node';
  return [
    ...normalBreast(rightX), ...normalBreast(leftX),
    tissue('Right nipple', [rightX,2,0], [4,1.5,5], 208, {shadow:.39}),
    tissue('Left nipple', [leftX,2,0], [incomplete ? 10 : 4,1.5,incomplete ? 9 : 5], 208,
      {shadow: incomplete ? chapter.position === 'Altered angle and gel reattempt' ? .93 : .98 : .40}),
    ...(focus === 'breast-retroareolar-cyst'
      ? [tissue('Anechoic simple cyst', cyst, [5,4,6], 11, {enhance:.46})]
      : []),
    tissue('Right axillary vessel', [x-10,y+10,z], [4,3,21], 19),
    tissue('Left axillary vessel', [lx+10,ly+10,lz], [4,3,21], 19),
    tissue('Right axillary cortex', node, [5.5,4.6,rightAbnormal ? 14 : 10], 77),
    tissue('Right fatty hilum', [x,rightAbnormal ? y+.9 : y+.1,z], [3.8,rightAbnormal ? 1.7 : 1.9,rightAbnormal ? 6.2 : 8.2], 168,
      {flow:'hilum'}),
    tissue('Left axillary cortex', otherNode, [5.5,4.6,13], 77),
    tissue('Left fatty hilum', [lx,ly+.1,lz], [3.9,1.9,9], 171,{flow:'hilum'}),
    ...(rightAbnormal ? [tissue('Right peripheral flow', [x+2.75,y-1.7,z], [1.2,1.1,8], 92,{flow:'peripheral'})] : []),
  ];
}

export function breastChapters(record) {
  const breast = (key, target, settings = {}) => chapterFor(record, key, {
    target, linear:true, depth:46, sweep:[-11,11], ...settings
  });
  const screen = record.id === 'breast-supplemental-screening';
  if (screen) {
    return [
      breast('breast-screen-map', [rightX,21,0], {axis:0,sweep:[48,-48],frames:37,
        position:'Supine oblique · arm raised', coverage:true,
        title:'Coverage overview · cranial-to-caudal right breast pass',
        observation:'Make the initial cranial-to-caudal pass with the probe marker toward patient right. The locator maps the overlapping band traverses that follow on both sides.'}),
      ...['right','left'].flatMap((side,index) =>
      [35,0,-35].map((band,number) => breast(`breast-screen-${side}-${number}`,
        [index ? leftX : rightX,21,band],
        {axis:2, sweep:index ? [-60,60] : [60,-60], frames:121, aperture:80,
          position:'Supine oblique · arm raised',
          observation:`Translate from the medial to lateral edge of the ${side} breast. ${number === 0
            ? 'Continue across the upper lateral tissue toward the axillary tail.'
            : number === 1
              ? 'Overlap the neighboring footprints and traverse the nipple region.'
              : 'End at the inframammary fold. Inspect down to the pectoral fascia.'}`
        })))
    ];
  }
  if (record.id === 'breast-retroareolar-cyst') {
    return [
      breast('breast-cyst-radial', cyst, {axis:2, marks:[measure('Anechoic simple cyst','width'),measure('Anechoic simple cyst','depth')]}),
      breast('breast-cyst-anti', cyst, {marks:[measure('Anechoic simple cyst','width')]}),
    ];
  }
  if (record.id === 'breast-axillary-node') {
    return [
      breast('axillary-node-long', node, {axis:2, colorIds:['Right fatty hilum','Right peripheral flow'], sweep:[-8,8],
        marks:[measure('Right axillary cortex','wall','Right fatty hilum',5.63),measure('Right axillary cortex','width')]}),
      breast('axillary-node-short', node, {colorIds:['Right fatty hilum','Right peripheral flow'], sweep:[-17,17],
        marks:[measure('Right axillary cortex','wall','Right fatty hilum'),measure('Right axillary cortex','depth')]}),
      breast('axillary-node-opposite', otherNode, {axis:2, colorIds:['Left fatty hilum'], sweep:[-8,8],
        marks:[measure('Left axillary cortex','wall','Left fatty hilum')]}),
      breast('axillary-tail-diagnostic', [-90,25,38], {axis:2, sweep:[-19,19]})
    ];
  }
  const initial = breast('breast-retro-limited', [leftX,15,0], {sweep:[-7,7], position:'Initial retroareolar approach'});
  return [
    breast('breast-limited-adjacent', [68,18,0], {axis:2, sweep:[-7,10]}),
    initial,
    {...initial,id:'breast-retro-limited-repeat',title:'Left retroareolar window · reattempt',
      axis:2, target:[leftX+2,15,2], position:'Altered angle and gel reattempt', sweep:[-6,5]},
  ];
}
