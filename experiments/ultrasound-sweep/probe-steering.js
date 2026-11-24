/** Each cell is an actual sampled pose. Scrubbing and steering select the same frames. */
export function probeSteering({ axes, cells }, fieldset, selectFrame, pause) {
  const ordered = [...cells].sort((a, b) => a.frame - b.frame);
  let active = ordered[0];
  let origin;
  const controls = axes.map((axis, index) => {
    const label = document.createElement('label');
    const slider = document.createElement('input');
    const output = document.createElement('output');
    slider.type = 'range';
    slider.id = 'probe-axis-' + index;
    slider.min = 0;
    slider.max = axis.values.length - 1;
    slider.step = 1;
    label.htmlFor = slider.id;
    output.htmlFor = slider.id;
    label.append(document.createTextNode(axis.label), slider, output);
    slider.setAttribute('aria-label', axis.label);
    slider.oninput = () => {
      const next = [...active.indices];
      next[index] = slider.valueAsNumber;
      select(next);
    };
    fieldset.insertBefore(label, fieldset.lastElementChild);
    return { slider, output };
  });
  fieldset.hidden = false;

  function select(indices) {
    const cell = cells.find((item) => item.indices.every((v, i) => v === indices[i]));
    if (cell) {
      active = cell;
      selectFrame(cell.frame);
    }
  }

  // The four approach frames between indexed cells can have fractional values.
  function atFrame(frame) {
    const lower = ordered.findLast((cell) => cell.frame <= frame) ?? ordered[0];
    const upper = ordered.find((cell) => cell.frame >= frame) ?? ordered.at(-1);
    const t = lower === upper ? 0 : (frame - lower.frame) / (upper.frame - lower.frame);
    const values = axes.map((axis, i) => axis.values[lower.indices[i]] * (1 - t) + axis.values[upper.indices[i]] * t);
    return { cell: t <= .5 ? lower : upper, values };
  }

  function sync(frame) {
    const { cell, values } = atFrame(frame);
    active = cell;
    controls.forEach(({ slider, output }, i) => {
      const text = Number(values[i].toFixed(1)) + (axes[i].unit === '°' ? '°' : ' ' + axes[i].unit);
      slider.value = cell.indices[i];
      slider.setAttribute('aria-valuetext', text);
      output.value = text;
    });
  }

  function drag({ phase, dx, dy }) {
    if (phase === 'start') {
      pause();
      origin = [...active.indices];
    } else if (phase === 'move' && origin) {
      const next = [...origin];
      next[0] = Math.min(axes[0].values.length - 1, Math.max(0, origin[0] + Math.round(dx / 30)));
      next[2] = Math.min(axes[2].values.length - 1, Math.max(0, origin[2] - Math.round(dy / 25)));
      if (next.some((value, i) => value !== active.indices[i])) select(next);
    } else if (phase === 'end') {
      origin = null;
    }
  }

  function referenceFor(frame, keyframes) {
    // Compare cross-duct or along-duct sections according to the actual rotation.
    const angle = atFrame(frame).values[1];
    return keyframes.reduce((best, key) => {
      const diff = Math.abs(atFrame(key.frame).values[1] - angle);
      const bestDiff = Math.abs(atFrame(best.frame).values[1] - angle);
      return diff < bestDiff || (diff === bestDiff && Math.abs(key.frame - frame) < Math.abs(best.frame - frame))
        ? key : best;
    });
  }

  return { sync, drag, referenceFor, rotationAt: (frame) => atFrame(frame).values[1] };
}
