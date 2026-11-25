// Derive static report and reading links from the same sampled chapters as playback.
import { readFileSync } from 'node:fs';
const visits = JSON.parse(readFileSync(0, 'utf8')),
  output = {};
for (const { owner, record } of visits) {
  const { chapters } = await import('../cases/' + owner + '/playable.js');
  output[record.id] = chapters(record).map(
    ({ id, title, viewImage, frames, evidenceFrame, observation, measurement }) => {
      if (!Number.isInteger(evidenceFrame) || evidenceFrame < 0 || evidenceFrame >= frames || !observation)
        throw new Error('Unbound observation in ' + record.id + '/' + id);
      return { id, title, viewImage, evidenceFrame, observation, measurement };
    },
  );
}
process.stdout.write(JSON.stringify(output));
