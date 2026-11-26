import * as THREE from '../../vendor/build/three.module.js';
import { bodyDirection, bodyPoint } from '../../cardiac/torso/registration.js';
import { chamberColors, valveColors, createRegisteredHeart, loadTorsoParts } from '../../cardiac/torso/torso-view.js';
import { sample } from './playable.js';

// The fitted torso assets use +left, +cranial, +anterior. The common case
// viewer uses +right, +anterior, +cranial, in the same millimetres.
const ribs = '#dbcbb0';
const legend = [
  { label: 'Rib cage', color: ribs },
  { label: 'Right atrium', color: chamberColors.RA },
  { label: 'Right ventricle', color: chamberColors.RV },
  { label: 'Left atrium', color: chamberColors.LA },
  { label: 'Left ventricle', color: chamberColors.LV },
  { label: 'Aortic valve cusps', color: valveColors.AV },
  { label: 'Pulmonary valve cusps', color: valveColors.PV },
];
const toRAS = ([left, cranial, anterior]) => [-left, anterior, cranial];
const mesh = (geometry, color, options) => new THREE.Mesh(geometry,
  new THREE.MeshStandardMaterial({ color, roughness: .75, ...options }));

export async function createCaseModel(record, chapter) {
  const [skinGeometry, bones, cartilage] = await loadTorsoParts();
  const anatomy = new THREE.Group();
  const patient = new THREE.Group();
  patient.matrix.makeBasis(
    new THREE.Vector3(-1, 0, 0), new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 1, 0),
  );
  patient.matrixAutoUpdate = false;
  anatomy.add(patient);
  const skin = mesh(skinGeometry, '#c3977c', { transparent: true, depthWrite: false });
  const ribCage = mesh(bones, ribs);
  const costalCartilage = mesh(cartilage, '#b8b19b');
  skin.name = 'Chest exterior';
  ribCage.name = 'Rib cage';
  costalCartilage.name = 'Costal cartilage';
  patient.add(skin, ribCage, costalCartilage);
  const cardiac = createRegisteredHeart(patient, sample(chapter, chapter.evidenceFrame, record).frame);

  return {
    anatomy, skin, legend, radius: 213,
    update(acquisition, number) {
      const { frame, plane } = sample(acquisition, number, record);
      cardiac.update(frame);
      return {
        contact: toRAS(bodyPoint(plane.origin)),
        width: toRAS(bodyDirection(plane.right)),
        beam: toRAS(bodyDirection(plane.down)),
        depth: plane.depth,
        halfAngle: THREE.MathUtils.radToDeg(plane.halfAngle),
        probe: 'phased',
      };
    },
  };
}
