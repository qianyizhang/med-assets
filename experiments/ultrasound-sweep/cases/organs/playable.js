import {abdominalChapters, abdominalVolume} from './playable-abdomen.js';
import {thyroidChapters, thyroidVolume, breastChapters, breastVolume} from './playable-neck-breast.js';
import {drawPose, drawSection} from './playable-render.js';

const acquisition = {
  abdomen: [abdominalChapters, abdominalVolume],
  thyroid: [thyroidChapters, thyroidVolume],
  breast: [breastChapters, breastVolume]
};

export function chapters(record) {
  return acquisition[record.family][0](record);
}

export function render(ctx, chapter, frame, record, {overlay=false}={}) {
  return drawSection(ctx, chapter, frame, acquisition[record.family][1](record, chapter), overlay);
}

export function pose(ctx, chapter, frame, record, {yaw=0}={}) {
  drawPose(ctx, chapter, frame, record, acquisition[record.family][1](record, chapter), yaw);
}
