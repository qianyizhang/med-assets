export const tissue = (id, center, radii, shade, options = {}) => ({id, center, radii, shade, ...options});
export const measure = (id, axis, inner = null, lateralOffset = 0) => ({id, axis, inner, lateralOffset});

export function plane(chapter, frame) {
  const {axis, target, sweep, evidenceFrame, frames} = chapter;
  const normal = axis === 0 ? 2 : 0;
  const offset = frame <= evidenceFrame
    ? sweep[0] * (1 - frame / evidenceFrame)
    : sweep[1] * ((frame - evidenceFrame) / (frames - 1 - evidenceFrame));
  return {axis, normal, center: target[axis], level: target[normal] + offset};
}

export function cut(shape, slice) {
  const distance = (slice.level - shape.center[slice.normal]) / shape.radii[slice.normal];
  if (Math.abs(distance) >= 1) return null;
  const factor = Math.sqrt(1 - distance * distance);
  return {
    x: shape.center[slice.axis] - slice.center,
    y: shape.center[1],
    w: shape.radii[slice.axis] * factor,
    h: shape.radii[1] * factor
  };
}

export function endpoints(model, slice, mark) {
  const shape = model.find(item => item.id === mark.id);
  const section = shape && cut(shape, slice);
  if (!section) return null;
  const {x, y, w, h} = section;
  if (mark.axis === 'width') return [[x-w, y], [x+w, y]];
  if (mark.axis === 'depth') return [[x, y-h], [x, y+h]];
  const other = model.find(item => item.id === mark.inner);
  const inner = other && cut(other, slice);
  if (!inner) return null;
  const u = inner.x + mark.lateralOffset;
  const anterior = (center, width, depth, height) => depth-height*Math.sqrt(1-((u-center)/width)**2);
  return [[u, anterior(x,w,y,h)], [u, anterior(inner.x,inner.w,inner.y,inner.h)]];
}

export function chapterFor(record, key, settings) {
  const viewImage = `images/${key}.svg`;
  const view = record.views.find(item => item.image === viewImage);
  if (!view) throw new Error(`Unknown organ view ${record.id}/${viewImage}`);
  const frames = settings.frames ?? 25;
  return {
    id: key, title: view.title, viewImage, frames, evidenceFrame: Math.floor(frames/2),
    observation: view.caption, measurement: view.measurement,
    axis: 0, sweep: [-16,16], ...settings,
  };
}
