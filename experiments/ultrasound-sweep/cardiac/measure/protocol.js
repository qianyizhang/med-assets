// Velocities in cm/s, positive toward the transducer. Independent illustrative
// envelopes share the 980 ms cardiac clock; amplitude and curvature are authored.
export const BEAT_SECONDS = 0.98;
const ejection = (peak, start = 0.055, end = 0.35) => [
  [start, 0],
  [start + 0.04, peak * 0.57],
  [start + 0.105, peak],
  [end - 0.075, peak * 0.79],
  [end - 0.025, peak * 0.34],
  [end, 0],
];
const filling = (e, a) => [
  [0.43, 0],
  [0.51, e],
  [0.56, e * 0.76],
  [0.68, 0],
  [0.82, 0],
  [0.91, a],
  [0.988, 0],
];
const tissue = (s, e, a) => [...ejection(s, 0.03, 0.35), ...filling(-e, -a)];
export const spectra = {
  mitral: {
    label: 'Mitral inflow',
    mode: 'PW',
    site: 'Place the sample volume between the mitral leaflet tips during diastole.',
    knots: filling(79, 54),
    type: 'inflow',
    range: 100,
  },
  tricuspid: {
    label: 'Tricuspid inflow',
    mode: 'PW',
    site: 'Sample just ventricular to the tricuspid leaflet tips with the beam along the opening.',
    knots: filling(57, 38),
    type: 'inflow',
    range: 75,
  },
  septal: {
    label: 'Septal mitral annulus',
    mode: 'TDI',
    site: 'Place the tissue gate on the septal mitral annulus. The annulus approaches the apex during systole.',
    knots: tissue(8.5, 9, 7),
    type: 'tissue',
    range: 18,
  },
  lateral: {
    label: 'Lateral mitral annulus',
    mode: 'TDI',
    site: 'Sample the lateral mitral annulus. Compare its early relaxation velocity with the septal site.',
    knots: tissue(10, 13, 8),
    type: 'tissue',
    range: 18,
  },
  rvS: {
    label: 'Lateral tricuspid annulus',
    mode: 'TDI',
    site: 'Align the tissue beam with longitudinal movement of the lateral tricuspid annulus.',
    knots: tissue(12.5, 12, 8),
    type: 'tissue',
    range: 18,
  },
  tr: {
    label: 'Tricuspid regurgitant signal',
    mode: 'CW',
    site: 'Conditional example with a measurable small systolic jet toward the atrium. Seek a complete envelope from multiple windows.',
    knots: ejection(-220, 0.025, 0.36),
    type: 'tr',
    range: 275,
  },
  pulmonaryVein: {
    label: 'Pulmonary venous return',
    mode: 'PW',
    site: 'Sample in the right upper pulmonary vein near its entry into the left atrium. Identify systolic, diastolic and atrial-reversal waves.',
    knots: [
      [0.04, 0],
      [0.18, 43],
      [0.37, 8],
      [0.43, 6],
      [0.55, 40],
      [0.74, 4],
      [0.82, 0],
      [0.9, -19],
      [0.98, 0],
    ],
    type: 'venous',
    range: 65,
  },
  hepatic: {
    label: 'Hepatic venous return',
    mode: 'PW',
    site: 'Place the sample volume inside a hepatic vein near the IVC. On this subcostal convention, forward flow runs away from the probe.',
    knots: [
      [0.04, 0],
      [0.16, -40],
      [0.37, -4],
      [0.43, 0],
      [0.55, -27],
      [0.72, 0],
      [0.82, 0],
      [0.9, 14],
      [0.98, 0],
    ],
    type: 'venous',
    range: 55,
  },
  lvot: {
    label: 'LV outflow tract',
    mode: 'PW',
    site: 'Align with systolic outflow and sample proximal to the aortic valve, at the level used for the LVOT diameter.',
    knots: ejection(-102),
    type: 'lvot',
    range: 130,
  },
  aortic: {
    label: 'Aortic valve',
    mode: 'CW',
    site: 'Align the continuous-wave beam along outflow across the valve. Compare the best-aligned window.',
    knots: ejection(-131),
    type: 'aortic',
    range: 170,
  },
  rvot: {
    label: 'RV outflow tract',
    mode: 'PW',
    site: 'Sample in the RVOT just proximal to the pulmonary valve, along forward flow.',
    knots: ejection(-83),
    type: 'outflow',
    range: 110,
  },
  pulmonary: {
    label: 'Pulmonary valve',
    mode: 'CW',
    site: 'Pass the continuous-wave beam through the pulmonary valve along the main pulmonary artery.',
    knots: ejection(-96),
    type: 'semilunar',
    range: 130,
  },
  mr: {
    label: 'Mitral regurgitant signal',
    mode: 'CW',
    site: 'Conditional jet example. Align the beam along a mitral regurgitant jet identified with color and seek its complete systolic envelope.',
    knots: ejection(-465, 0.025, 0.36),
    type: 'regurgitation',
    range: 550,
  },
  ar: {
    label: 'Aortic regurgitant signal',
    mode: 'CW',
    site: 'Conditional jet example. Align the beam through a diastolic aortic regurgitant jet into the LVOT.',
    knots: [
      [0.35, 0],
      [0.38, 355],
      [0.52, 315],
      [0.71, 275],
      [0.91, 244],
      [0.99, 228],
    ],
    type: 'diastolic-jet',
    range: 420,
  },
  pr: {
    label: 'Pulmonary regurgitant signal',
    mode: 'CW',
    site: 'Conditional jet example. Inspect the diastolic envelope along a regurgitant pulmonary jet toward the RVOT.',
    knots: [
      [0.35, 0],
      [0.41, 155],
      [0.55, 105],
      [0.74, 72],
      [0.96, 57],
      [0.99, 54],
    ],
    type: 'diastolic-jet',
    range: 200,
  },
  arch: {
    label: 'Descending thoracic aorta',
    mode: 'PW',
    site: 'Align with flow in the descending aorta. This suprasternal orientation places forward flow away from the transducer.',
    knots: [...ejection(-90), [0.41, -8], [0.58, -9], [0.81, -5], [0.98, -5]],
    type: 'arch',
    range: 120,
  },
};
export const tools = {
  color: 'Color flow mapping',
  length: '2D distance calipers',
  lv: 'LV biplane volumes & ejection fraction',
  strain: 'LV longitudinal strain · model',
  la: 'LA biplane volume & index',
  rv: 'RV fractional area change',
  ra: 'RA area & volume',
  tapse: 'Tricuspid annular excursion · M-mode',
  ivc: 'IVC respiratory collapse · M-mode',
};
export const protocol = {
  plax: ['length', 'color'],
  'psax-av': ['rvot', 'pulmonary', 'pr', 'tr', 'length', 'color'],
  'psax-mv': ['length', 'color'],
  'psax-papillary': ['length', 'color'],
  'psax-apical': ['length', 'color'],
  a4c: [
    'mitral',
    'color',
    'septal',
    'lateral',
    'pulmonaryVein',
    'lv',
    'la',
    'ra',
    'tricuspid',
    'tr',
    'mr',
    'length',
    'strain',
  ],
  a2c: ['lv', 'la', 'mr', 'length', 'color', 'strain'],
  a3c: ['lvot', 'aortic', 'ar', 'mr', 'length', 'color', 'strain'],
  a5c: ['lvot', 'aortic', 'ar', 'length', 'color'],
  'rv-focused': ['tapse', 'rv', 'rvS', 'ra', 'tricuspid', 'tr', 'length', 'color'],
  'rv-inflow': ['tricuspid', 'tr', 'length', 'color'],
  'rv-outflow': ['rvot', 'pulmonary', 'pr', 'length', 'color'],
  'subcostal-4c': ['color', 'length'],
  'subcostal-sax': ['length', 'color'],
  'subcostal-aorta': ['length', 'color'],
  'subcostal-ivc': ['ivc', 'hepatic', 'length', 'color'],
  'suprasternal-arch': ['arch', 'length', 'color'],
};
export const caliperTargets = {
  plax: {
    'LV internal diameter · ED':
      'At end diastole, measure across the LV perpendicular to its long axis just below the mitral tips.',
    'LV internal diameter · ES':
      'Repeat the LV internal diameter at end systole in the same plane and level.',
    'Septal thickness':
      'At end diastole, measure across the septum at the same level as LV internal diameter.',
    'Posterior wall thickness':
      'At end diastole, measure the posterior wall perpendicular to the LV long axis. Exclude adjacent structures.',
    'LVOT diameter':
      'At mid systole, measure inner edge to inner edge, perpendicular to the LVOT at the PW sampling level.',
    'Aortic annulus': 'In systole, measure inner edge to inner edge between the hinge points.',
    'Aortic root / ascending aorta':
      'At end diastole, measure perpendicular to the aortic axis at the selected level. Use a consistent leading-edge convention.',
    'LA anteroposterior diameter':
      'At end systole, measure the LA along the root-to-posterior-wall axis. Biplane LA volume describes size more fully.',
  },
  'rv-focused': {
    'RV basal diameter': 'Measure the widest basal third of the RV at end diastole.',
    'RV mid diameter': 'Measure the midcavity at end diastole, across the long axis at papillary level.',
    'RV length': 'At end diastole, measure from the midpoint of the tricuspid annulus to the RV apex.',
  },
  'subcostal-4c': {
    'RV free wall':
      'At end diastole, measure perpendicular to the RV free wall. Exclude epicardial fat and trabeculations.',
  },
  'subcostal-ivc': {
    'IVC diameter':
      'Measure perpendicular to the IVC course slightly upstream of the RA. The separate respiratory example shows expiration and sniff.',
  },
  'suprasternal-arch': {
    'Arch diameter': 'At end diastole, place calipers perpendicular to the visualized arch segment.',
  },
  'rv-outflow': {
    'RVOT diameter':
      'At end diastole, measure perpendicular to the outflow axis at the chosen proximal or distal level.',
  },
};
export const sources = {
  comprehensive: 'https://www.asecho.org/guideline/comprehensive-tte-in-adults/',
  strain: 'https://www.asecho.org/guideline/clinical-applications-of-strain-echocardiography/',
  chambers: 'https://www.asecho.org/guideline/cardiac-chamber-quantification-by-echo-in-adults/',
  right: 'https://www.asecho.org/guideline/right-heart-in-adults-pulmonary-hypertension/',
  diastolic: 'https://www.asecho.org/guideline/left-ventricular-diastolic-function-by-echo/',
};
