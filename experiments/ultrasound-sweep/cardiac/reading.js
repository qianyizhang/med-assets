// What to look for on the neutral section. Probe coordinates and labels live in heart-poses.js.
export const readings = {
  plax: 'Follow the left ventricle through its outflow tract into the aortic root. The mitral valve opens behind the outflow tract during filling.',
  'rv-inflow': 'Follow the right atrium through the tricuspid valve into the right ventricle. Watch the leaflet tips separate during filling.',
  'rv-outflow': 'Follow the right ventricular outflow tract across the pulmonary valve into the main pulmonary artery.',
  'psax-av': 'Look at the aortic valve in cross-section. Its cusps open in systole, with the right ventricular outflow tract anteriorly.',
  'psax-mv': 'Look through the mitral orifice as the leaflets separate in diastole. The right ventricle lies anterior to the left.',
  'psax-papillary': 'Find the papillary muscles inside the LV cavity. Compare inward motion and wall thickening around the circumference.',
  'psax-apical': 'At the apical level the LV cavity narrows during systole. Compare its size with the papillary-muscle level.',
  a4c: 'Find the LV apex on screen right. The tricuspid attachment is closer to the apex than the mitral attachment. Compare the AV plane at end diastole and end systole.',
  'rv-focused': 'Center the right ventricle and follow its free wall to the apex. Compare the lateral tricuspid annulus through systole.',
  a5c: 'Angle anteriorly from four chamber until the LV outflow tract and aortic root enter the plane.',
  a2c: 'Follow the anterior and inferior LV walls from the mitral annulus to the apex. Pair this view with four chamber for biplane volumes.',
  a3c: 'Follow the LV inlet and outlet in one plane. Compare mitral opening in diastole with aortic opening in systole.',
  'subcostal-4c': 'Look toward the heart from beneath the xiphoid. Inspect the four chambers and the atrial septum.',
  'subcostal-ivc': 'Follow the inferior vena cava into the right atrium. Use the respiratory example to compare expiration with inspiration.',
  'subcostal-sax': 'From below the sternum, follow the short-axis right ventricular outflow tract toward the pulmonary valve.',
  'subcostal-aorta': 'Follow the descending aorta into the upper abdomen. Compare its course with the separate caval–atrial junction view.',
  'suprasternal-arch': 'Follow the aorta around the arch toward its descending segment. Compare the branch origins with the recorded view.',
};
export const viewOrder = ['plax', 'rv-inflow', 'rv-outflow', 'psax-av', 'psax-mv', 'psax-papillary', 'psax-apical',
  'a4c', 'rv-focused', 'a5c', 'a2c', 'a3c', 'subcostal-4c', 'subcostal-ivc', 'subcostal-sax', 'subcostal-aorta', 'suprasternal-arch'];
export const contactNotes = {
  Parasternal: 'Left sternal border · partial left-side roll',
  Apical: 'Left apical impulse · partial left-side roll',
  Subcostal: 'Below the xiphoid · supine position',
  Suprasternal: 'Suprasternal notch · supine position',
};
