function milliseconds(timestamp) {
  const [hours, minutes, seconds, fraction] = timestamp.split(/[:,]/).map(Number);
  return ((hours * 60 + minutes) * 60 + seconds) * 1000 + fraction;
}

export function readCaptions(srt) {
  return srt.trim().split(/\r?\n\r?\n/).map((block) => {
    const [, time, ...lines] = block.split(/\r?\n/);
    const [start, end] = time.split(' --> ').map(milliseconds);
    return { start, end, text: lines.join('\n') };
  });
}

export function localizeCaptions(cues, firstCue, length) {
  const excerpt = cues.slice(firstCue, firstCue + length);
  // The owning edit opens every scene 300 ms before its narration begins.
  const offset = excerpt[0].start - 300;
  return excerpt.map(({ start, end, text }) => ({ start: start - offset, end: end - offset, text }));
}

const timecode = (ms) => new Date(ms).toISOString().slice(11, 23);

export function vtt(cues) {
  return 'WEBVTT\n\n' + cues.map(({ start, end, text }) =>
    timecode(start) + ' --> ' + timecode(end) + '\n' + text).join('\n\n') + '\n';
}
