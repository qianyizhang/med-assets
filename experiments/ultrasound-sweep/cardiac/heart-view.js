import {createEchoRenderer} from './heart-echo.js';
import {heartFrame, heartSection, probePlane} from './heart-geometry.js';
import {renderScene} from './heart-scene.js';

function canvasViewport(canvas) {
  const ink = canvas.getContext('2d', {alpha: false});
  if (!ink) throw new Error('This browser could not open the cardiac canvas.');
  return (paint) => {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!(width > 0 && height > 0)) return;
    const deviceScale = Math.min(2, window.devicePixelRatio || 1);
    const pixelWidth = Math.round(width * deviceScale);
    const pixelHeight = Math.round(height * deviceScale);
    if (canvas.width !== pixelWidth) canvas.width = pixelWidth;
    if (canvas.height !== pixelHeight) canvas.height = pixelHeight;
    ink.setTransform(pixelWidth / width, 0, 0, pixelHeight / height, 0, 0);
    paint(ink, width, height);
  };
}

export function createHeartView({scene, section}) {
  const sceneViewport = canvasViewport(scene);
  const sectionViewport = canvasViewport(section);
  const renderEcho = createEchoRenderer();
  let frame;
  let plane;
  let cut;
  let previousPhase;
  return {
    render({phase = 0, tilt = 0, overlay = false, yaw = 31, pitch = -14} = {}) {
      const phaseChanged = phase !== previousPhase;
      const planeChanged = tilt !== plane?.tilt;
      if (phaseChanged) frame = heartFrame(phase);
      if (planeChanged) plane = probePlane(tilt);
      if (phaseChanged || planeChanged) cut = heartSection(frame, plane);
      previousPhase = phase;
      sceneViewport((ink, width, height) => renderScene(ink, width, height, frame, plane, cut, overlay, yaw, pitch));
      sectionViewport((ink, width, height) => renderEcho(ink, width, height, plane, cut, frame.motion, overlay));
    },
  };
}
