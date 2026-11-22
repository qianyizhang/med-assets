import selections from './pelvic-lesson-layers.json';
import bladderOutline from './part-images/pelvic-bladder-outline.webp';
import bladderDomeHidden from './part-images/pelvic-bladder-dome-hidden.webp';
import bladderAnswer from './part-images/pelvic-bladder-dome-hidden-answer.webp';
import cervixPelvicNeighbors from './part-images/pelvic-cervix-pelvic-neighbors.webp';
import cervixCenter from './part-images/pelvic-cervix-center.webp';
import cervixAnswer from './part-images/pelvic-cervix-pelvic-neighbors-answer.webp';

const copy = {
  'urinary-left-vesical': {
    transition: 'The system plate uses the Workshop junction illustration. This close-up switches to a separate HRA United Female atlas model in its native frame and at a larger display scale.',
    question: 'Where are the bladder base and neck, and where do the two ureters enter?',
    instruction: 'Start with the bladder outline. Then hide the dome and follow the visible ends of the ureters to the two entry landmarks.',
    answer: 'The bladder neck is the narrow outlet at the bottom. The two ureteral entry landmarks sit at the upper corners of the trigone, one on each side of the base and above the neck. In this view from behind and above, image left and right match the atlas’s left and right.',
    limit: 'The close-up crops the long ureters. The surfaces show entry landmarks and the outlet region. Lumen continuity, wall layers and fill state are outside this lesson.',
    exactLibrary: 'library/bladder/pelvic-base-r01',
    historicalLibrary: 'library/bladder/hra-female-context-r03',
    attribution: 'models/bladder/ATTRIBUTION.md',
    answerImage: {
      src: bladderAnswer,
      alt: 'Bladder with the dome hidden. Leaders mark both ureteral entry landmarks, the base below them and the narrow neck at the bottom.',
    },
    layers: {
      'bladder-outline': {
        label: 'Bladder outline',
        image: { src: bladderOutline, alt: 'View from behind and above. A rounded upper surface meets a darker region with a narrow tip below it.' },
      },
      'bladder-dome-hidden': {
        label: 'Dome hidden',
        image: { src: bladderDomeHidden, alt: 'Same frame with the dome hidden. Two pale tubes approach opposite corners of the lower surface.' },
      },
    },
  },
  'reproductive-female-context': {
    transition: 'The system plate shows the composed reproductive tract. This side view switches to a native HRA United Female selection with same-atlas bladder and rectum. The framing and display colors change.',
    question: 'Where are the cervix and vaginal exterior in relation to the bladder and rectum?',
    instruction: 'In this side view the front of the body is at image left. Find the two central surfaces, then hide the neighbors to inspect their relationship.',
    answer: 'The cervix is the short upper structure. The vaginal exterior extends below it, between the anterior bladder on the left of the image and the posterior rectum on the right.',
    limit: 'This is a surface atlas of one example. The view supports relative exterior placement. It leaves lumen continuity, mucosal detail and variation outside scope.',
    exactLibrary: 'library/vagina_hra/teaching-context-r03',
    historicalLibrary: 'library/vagina_hra/context-r02',
    attribution: 'models/vagina_hra/provenance/context-r02/migration-2026-10-24/ATTRIBUTION.md',
    answerImage: {
      src: cervixAnswer,
      alt: 'Side view labels the cervix above the vaginal exterior, the bladder in front and the rectum behind.',
    },
    layers: {
      'cervix-pelvic-neighbors': {
        label: 'Pelvic neighbors',
        image: { src: cervixPelvicNeighbors, alt: 'Side view with a gold surface in front, two rose surfaces in the middle and a curved teal surface behind.' },
      },
      'cervix-center': {
        label: 'Central structures',
        image: { src: cervixCenter, alt: 'Same side view with only the short upper and elongated lower rose surfaces visible.' },
      },
    },
  },
};

export const pelvicTasks = Object.fromEntries(Object.entries(copy).map(([id, { layers, ...lesson }]) => {
  const { path, camera, layers: choices } = selections[id];
  return [id, {
    ...lesson, camera,
    layers: choices.map(({ id, nodes }) => ({ path, nodes, ...layers[id] })),
  }];
}));
