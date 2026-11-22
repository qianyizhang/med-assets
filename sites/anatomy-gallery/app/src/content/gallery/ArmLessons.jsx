import React from 'react';
import { byPath } from './catalog.js';
import { Heading, Link, Missing } from './GalleryUI.jsx';
import { isLoopbackGallery } from './local-models.js';
import { PartLesson } from './PartLesson.jsx';
import selections from './arm-lesson-layers.json';
import elbowCapsule from './part-images/arm-elbow-capsule.webp';
import elbowNerve from './part-images/arm-elbow-nerve.webp';
import elbowAnswer from './part-images/arm-elbow-answer.webp';
import shoulderGlenoid from './part-images/arm-shoulder-glenoid.webp';
import shoulderCuff from './part-images/arm-shoulder-cuff.webp';
import shoulderAnswer from './part-images/arm-shoulder-answer.webp';

const lessonPath = 'use-cases/right-arm';
const copy = {
  elbow: {
    title: 'Right elbow',
    zh: '右肘',
    question: 'Where does the ulnar nerve pass in relation to the medial epicondyle and the olecranon?',
    instruction: 'Start with the capsule. Keep the two bony landmarks in view as you switch to the ulnar nerve.',
    answer: 'The elbow capsule surrounds the joint. The ulnar nerve stays outside the capsule and passes behind the medial epicondyle of the humerus in the groove between that prominence and the olecranon of the ulna. Both views keep the same three bones in place.',
    answerImage: {
      src: elbowAnswer,
      alt: 'Matched posteromedial views with the same landmarks labeled. The nerve runs past the back of the medial epicondyle on the side facing the olecranon.',
    },
    layers: {
      capsule: {
        label: 'Joint capsule',
        publicSource: 'models/joints/exports/z-elbow-r01/elbow_z_native.glb',
        image: { src: elbowCapsule, alt: 'Posteromedial right elbow. A tinted sheet follows the joint surfaces between the upper arm and forearm bones.' },
      },
      nerve: {
        label: 'Ulnar nerve',
        publicSource: 'models/peripheral_nerves/exports/ulnar-elbow-r01/right-ulnar-elbow.glb',
        image: { src: elbowNerve, alt: 'Same elbow view. Trace the thin yellow strand as it passes the two bony prominences.' },
      },
    },
    context: 'Illustrative colors and different bone shading come from the two exports. Both keep the native pose and scale. The nerve view shows the selected surface course; the source does not include the full cubital tunnel or surrounding soft tissues.',
  },
  shoulder: {
    title: 'Right shoulder',
    zh: '右肩',
    question: 'How do the rotator cuff muscle surfaces sit around the scapular spine and the glenoid socket?',
    instruction: 'Find the socket, then switch to the rotator cuff and use the spine to orient the back. Turn the 3D model to see the front, or compare the front and back in the answer.',
    answer: 'The glenoid is the shallow socket at the outer edge of the scapula, rimmed by the labrum. On the back, supraspinatus lies above the scapular spine. Infraspinatus lies below the spine, with teres minor along the lateral border below it. Subscapularis lies on the front face, toward the ribs.',
    answerImage: {
      src: shoulderAnswer,
      alt: 'Three labeled shoulder views show the glenoid and its rim, the scapular spine with three cuff muscles on the back, and subscapularis on the front.',
    },
    layers: {
      glenoid: {
        label: 'Glenoid and labrum',
        publicSource: 'models/joints/exports/z-shoulder-r01/shoulder_z_native.glb',
        image: { src: shoulderGlenoid, alt: 'Rear-oblique right shoulder blade. A colored rim borders the shallow socket at its outer edge.' },
      },
      cuff: {
        label: 'Rotator cuff',
        image: { src: shoulderCuff, alt: 'Same shoulder view, with colored muscle surfaces against the back of the shoulder blade on either side of a ridge.' },
      },
    },
    context: 'Illustrative colors. The layers share the native right-arm pose and scale. The humerus is hidden to expose the socket. The selected muscle surfaces show position; their complete attachments and motion are outside the study.',
  },
};

function armTask(id) {
  const { layers, ...lesson } = copy[id];
  const { camera, layers: choices } = selections[id];
  return { ...lesson, camera, layers: choices.map((choice) => ({ ...choice, ...layers[choice.id] })) };
}

function AssetLinks({ layers }) {
  const local = isLoopbackGallery(globalThis.location?.hostname);
  return <ul>{layers.map(({ label, route, path, publicSource }) => {
    if (local || byPath.has(path)) return <li key={route}><Link to={route}>{label} · exact Library revision</Link></li>;
    const related = byPath.get(publicSource);
    return related?.source ? <li key={route}><a href={related.source}>{label} · earlier source revision</a></li> : null;
  })}</ul>;
}

export function ArmLessons({ id = 'elbow' }) {
  if (!Object.hasOwn(copy, id)) return <Missing />;
  const task = armTask(id);
  return (
    <>
      <Link to="use-cases">← Use Cases</Link>
      <Heading title={task.title}><span lang="zh">{task.zh}</span></Heading>
      <nav className="ga-tabs" aria-label="Right arm lessons">
        {Object.entries(copy).map(([key, lesson]) => (
          <Link key={key} to={lessonPath + '/' + key} aria-current={key === id ? 'page' : undefined}>
            {lesson.title}
          </Link>
        ))}
      </nav>
      <PartLesson key={id} task={task} />
      <p>{task.context}</p>
      <details>
        <summary>Assets and credits</summary>
        <AssetLinks layers={task.layers} />
        <p>
          Z-Anatomy / BodyParts3D geometry and derived lesson images · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>.
          Historical BodyParts3D / DBCLS credit · <a href="https://creativecommons.org/licenses/by-sa/2.1/jp/">CC BY-SA 2.1 Japan</a>.
        </p>
      </details>
    </>
  );
}
