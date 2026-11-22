import { salivary } from './catalog.js';
import views from './salivary-views.json';
import jaw from './part-images/salivary-jaw.webp';
import floor from './part-images/salivary-floor.webp';
import locationAnswer from './part-images/salivary-location-answer.webp';
import masseter from './part-images/salivary-masseter.webp';
import duct from './part-images/salivary-duct.webp';
import ductAnswer from './part-images/salivary-duct-course-answer.webp';

const stages = {
  jaw: {
    label: 'Jaw and oral floor',
    image: { src: jaw, alt: 'Six soft-tissue structures around a U-shaped jaw and the muscle forming the floor inside it.' },
  },
  floor: {
    label: 'Glands only',
    image: { src: floor, alt: 'The same six structures in the same positions with the jaw and oral-floor muscle hidden.' },
  },
  masseter: {
    label: 'Jaw and masseter',
    image: { src: masseter, alt: 'Left side of the jaw with muscle, a lobulated gland and a thin tube.' },
  },
  duct: {
    label: 'Gland and duct only',
    image: { src: duct, alt: 'The left gland and thin tube in their original positions with the muscle and jaw hidden.' },
  },
};

const prompts = {
  location: {
    question: 'Can you find all three pairs of salivary glands?',
    instruction: 'Use the jaw and floor of the mouth as landmarks. Hide them to check which shapes belong together.',
    answer: '1. The parotids sit beside the back of the jaw. 2. The submandibular glands sit below the body of the jaw. 3. The smaller sublingual glands lie nearer the midline in the floor of the mouth.',
    answerImage: { src: locationAnswer, alt: 'Leaders mark the three gland types in the isolated view. Each gland has a matching gland on the other side.' },
  },
  'duct-course': {
    question: 'Can you trace the parotid duct over the masseter?',
    instruction: 'Start at the left parotid gland. Hide the jaw and muscle to check where the duct runs.',
    answer: 'Start at the parotid gland (1). Follow the duct (2) forward over the superficial masseter (3). The model shows the gross surface course.',
    answerImage: { src: ductAnswer, alt: 'The numbered side view shows the thin duct crossing the visible outer surface of the masseter from the parotid gland.' },
  },
};

export const salivaryLocalEdition = 'z-native-shared-r01';

export function salivaryTask(stop, localPreview) {
  const view = views[stop];
  const edition = localPreview ? salivaryLocalEdition : salivary.revision;
  return {
    ...prompts[stop],
    camera: view.camera,
    layers: view.layers.map(({ id, file, nodes }) => ({
      ...stages[id], nodes, path: `models/${salivary.family}/exports/${edition}/${file}`,
    })),
  };
}
