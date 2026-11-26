// Inspect the actual fitted meshes in a compact delivery. Browser playback and
// cardiac chest contact have separate checks. Run with the assembled study path.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

assert.ok(process.argv[2], 'Pass the directory containing the assembled ultrasound study.');
const root = pathToFileURL(resolve(process.argv[2]) + sep);
const catalogue = await readFile(new URL('abdomen-tours.js', root), 'utf8');
const prefix = 'const abdomenTours = ';
assert.ok(catalogue.startsWith(prefix));
globalThis.abdomenTours = JSON.parse(catalogue.slice(prefix.length).trim().replace(/;$/, ''));
globalThis.fetch = async (url) => new Response(await readFile(new URL(url)));
const THREE = await import(new URL('vendor/build/three.module.js', root));
const vector = (p) => new THREE.Vector3(...p);

for (const owner of ['organs', 'vascular', 'pregnancy', 'echo']) {
  const family = 'cases/' + owner + '/';
  const records = JSON.parse(await readFile(new URL('../' + family + 'cases.json', import.meta.url), 'utf8'));
  const { chapters } = await import(new URL(family + 'playable.js', root));
  const { createCaseModel } = await import(new URL(family + 'playable-scene.js', root));
  let samples = 0, externalContacts = 0, maxError = 0;
  for (const record of records.filter(({ family }) => family !== 'aaa')) {
    const sections = chapters(record);
    const model = await createCaseModel(record, sections[0]);
    model.anatomy.updateMatrixWorld(true);
    for (const chapter of sections) {
      for (const frame of new Set([0, chapter.evidenceFrame, chapter.frames - 1])) {
        const pose = model.update(chapter, frame);
        const where = record.id + '/' + chapter.id + ' frame ' + frame;
        const beam = vector(pose.beam), width = vector(pose.width), contact = vector(pose.contact);
        assert.ok(pose.contact.every(Number.isFinite) && Number.isFinite(pose.depth) && pose.depth > 0, where);
        assert.ok(Math.abs(1 - beam.length()) < .001 && Math.abs(1 - width.length()) < .001, where);
        assert.ok(Math.abs(beam.dot(width)) < .001, 'Non-orthogonal imaging axes at ' + where);
        const normal = beam.clone().cross(width);
        for (const corner of pose.corners ?? []) {
          assert.ok(Math.abs(vector(corner).sub(contact).dot(normal)) < .01, 'Crop outside scan plane at ' + where);
        }
        samples++;
        if (pose.probe === 'endocavitary' || owner === 'echo') continue;
        // Check the first surface along the beam over a local 40 mm interval.
        // Allow 1.5 mm of discretization in the triangulated teaching surface.
        const ray = new THREE.Raycaster(contact.clone().addScaledVector(beam, -20), beam, 0, 40);
        const [hit] = ray.intersectObject(model.skin);
        assert.ok(hit, 'Missing skin contact at ' + where);
        const residual = Math.abs(hit.distance - 20);
        assert.ok(residual <= 1.5, 'Probe misses modeled skin at ' + where + ' by ' + residual + ' mm');
        maxError = Math.max(maxError, residual);
        externalContacts++;
      }
    }
    model.dispose?.();
  }
  const contactReport = externalContacts ? externalContacts + ' external contacts, ' + maxError.toFixed(2) + ' mm maximum sampled residual' : 'chest contacts checked by cardiac/torso/verify-contact.mjs';
  console.log(owner, samples + ' registered poses,', contactReport);
}
