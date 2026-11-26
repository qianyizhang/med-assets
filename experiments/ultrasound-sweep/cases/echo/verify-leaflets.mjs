// Arguments: current study URL, baseline study URL, optional evidence directory.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const [candidate = 'http://127.0.0.1:8897/', baseline = 'http://127.0.0.1:8902/', output] = process.argv.slice(2);
const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({
  executablePath: process.env.MODEL_SURVEY_BROWSER, chromiumSandbox: true, args: ['--enable-unsafe-swiftshader'],
});
if (output) await mkdir(output, { recursive: true });

async function review(root, isBaseline) {
  const page = await browser.newPage({ viewport: { width: 1360, height: 960 } });
  try {
    const route = new URL('tours/echo/echo-aortic-stenosis-sweep.html?chapter=psax-av-section&frame=24', root).href;
    await page.goto(route);
    await page.locator('canvas#pose[data-scene-ready]').waitFor();
    if (output) {
      const pixels = await page.locator('.monitors').screenshot();
      const webp = await page.evaluate(async (raw) => {
        const image = new Image();
        image.src = 'data:image/png;base64,' + raw;
        await image.decode();
        const canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        canvas.getContext('2d').drawImage(image, 0, 0);
        return canvas.toDataURL('image/webp', .93).split(',')[1];
      }, pixels.toString('base64'));
      await writeFile(join(output, isBaseline ? 'context-before.webp' : 'context-after.webp'), Buffer.from(webp, 'base64'));
    }
    const result = await page.evaluate(async ({ before, save }) => {
      const [{ createCaseModel }, acquisition, { heartFrame }, THREE] = await Promise.all([
        import('../../cases/echo/playable-scene.js'), import('../../cases/echo/playable.js'),
        import('../../cardiac/heart-geometry.js'), import('../../vendor/build/three.module.js'),
      ]);
      const record = JSON.parse(document.querySelector('#record').textContent);
      const chapter = acquisition.chapters(record).find(({ id }) => id === 'psax-av-section');
      const n = chapter.evidenceFrame;
      const source = acquisition.sample(chapter, n, record);
      const normal = heartFrame(source.phase);
      const scan = document.querySelector('#scan');
      const scanData = scan.getContext('2d').getImageData(0, 0, scan.width, scan.height).data;
      const scanHash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', scanData)))
        .map((byte) => byte.toString(16).padStart(2, '0')).join('');
      const model = await createCaseModel(record, chapter);
      model.update(chapter, n);
      const cusp = (root, name) => root.getObjectByName('Aortic valve cusp ' + name);
      const sourceParts = source.frame.details.filter(({ name, material }) => name === 'AV' && material === 'leaflet');
      const candidateParts = [1, 2, 3].map((name) => cusp(model.anatomy, name)).filter(Boolean);
      const evidence = {};
      if (before) return { scanHash, count: candidateParts.length, evidence };
      if (candidateParts.length !== 3) throw Error('Expected three independent source cusps.');

      const sourceError = (mesh, rows) => {
        const coordinates = mesh.geometry.attributes.position.array;
        return Math.max(...rows.flat(2).map((value, i) => Math.abs(value - coordinates[i])));
      };
      const metrics = candidateParts.map((mesh, i) => {
        const positions = mesh.geometry.attributes.position;
        const triangles = mesh.geometry.index.array;
        const edgeCounts = new Map();
        for (let j = 0; j < triangles.length; j += 3) {
          for (const [a, b] of [[triangles[j], triangles[j+1]], [triangles[j+1], triangles[j+2]], [triangles[j+2], triangles[j]]]) {
            const key = [a, b].sort((left, right) => left - right).join('/');
            edgeCounts.set(key, (edgeCounts.get(key) ?? 0) + 1);
            if (a % 19 === 0 && b % 19 === 18 || b % 19 === 0 && a % 19 === 18) {
              throw Error('A triangle crosses the open commissural boundary.');
            }
          }
        }
        return { name: mesh.name, vertices: positions.count, triangles: triangles.length / 3,
          boundaryEdges: [...edgeCounts.values()].filter((count) => count === 1).length,
          nonmanifoldEdges: [...edgeCounts.values()].filter((count) => count > 2).length,
          sourceErrorMm: sourceError(mesh, sourceParts[i].rings) };
      });

      const witness = candidateParts[0];
      const exact = witness.geometry.clone();
      const closed = acquisition.sample(chapter, 0, record);
      model.update(chapter, 0);
      const closedErrorMm = sourceError(witness, closed.frame.details.filter(({ name }) => name === 'AV')[0].rings);
      const closedGeometry = witness.geometry.clone();
      const openPoints = exact.attributes.position.array;
      const closedPoints = closedGeometry.attributes.position.array;
      let motionMm = 0;
      for (let i = 0; i < openPoints.length; i += 3) {
        motionMm = Math.max(motionMm,
          Math.hypot(openPoints[i] - closedPoints[i], openPoints[i+1] - closedPoints[i+1], openPoints[i+2] - closedPoints[i+2]));
      }
      model.update(chapter, n);

      const replacement = exact.clone();
      replacement.attributes.position.array.set(normal.details.filter(({ name }) => name === 'AV')[0].rings.flat(2));
      replacement.computeVertexNormals();
      const sourceRows = sourceParts[0].rings;
      const lightRows = [0, 2, 4, 6];
      const lightCols = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18];
      const vertices = lightRows.flatMap((row) => lightCols.flatMap((col) => sourceRows[row][col]));
      const light = new THREE.BufferGeometry();
      light.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      const indices = [];
      for (let y = 0; y < lightRows.length - 1; y++) {
        for (let x = 0; x < lightCols.length - 1; x++) {
          const a = y * lightCols.length + x;
          const b = a + 1;
          indices.push(a, b, b + lightCols.length, a, b + lightCols.length, a + lightCols.length);
        }
      }
      light.setIndex(indices);
      light.computeVertexNormals();
      const v = (x, y, z) => new THREE.Vector3(x, y, z);
      const closest = v(0,0,0);
      const triangle = new THREE.Triangle();
      let maxDeviationMm = 0;
      let maxFreeEdgeDeviationMm = 0;
      for (const [row, points] of sourceRows.entries()) {
        for (const point of points) {
          const target = new THREE.Vector3(...point);
          let nearest = Infinity;
          for (let i = 0; i < indices.length; i += 3) {
            const corner = (index) => v(...vertices.slice(indices[index] * 3, indices[index] * 3 + 3));
            triangle.set(corner(i), corner(i+1), corner(i+2)).closestPointToPoint(target, closest);
            nearest = Math.min(nearest, closest.distanceTo(target));
          }
          maxDeviationMm = Math.max(maxDeviationMm, nearest);
          if (row === 6) maxFreeEdgeDeviationMm = Math.max(maxFreeEdgeDeviationMm, nearest);
        }
      }
      if (save) {
        exact.computeBoundingBox();
        const center = exact.boundingBox.getCenter(v(0,0,0));
        const radius = 12;
        const renderer = new THREE.WebGLRenderer({ antialias:true, preserveDrawingBuffer:true });
        renderer.setSize(704, 512);
        renderer.setClearColor('#172a30');
        function draw(name, geometry, isReverse, gray) {
          const scene = new THREE.Scene();
          scene.add(new THREE.HemisphereLight('#fff3da', '#6f8089', 1.65));
          const key = new THREE.DirectionalLight('#fff2dc', 2.08);
          key.position.copy(center).add(isReverse ? v(-8,36,40) : v(40,16,-18));
          scene.add(key);
          if (geometry) scene.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
            color: gray ? '#cbd0d1' : '#e5c8a0', roughness:.76, side:THREE.DoubleSide,
          })));
          const camera = new THREE.OrthographicCamera(-radius*704/512, radius*704/512, radius,-radius,.01,500);
          camera.position.copy(center).add(isReverse ? v(-30,38,22) : v(37,32,-31));
          camera.lookAt(center);
          renderer.render(scene,camera);
          evidence[name] = renderer.domElement.toDataURL('image/webp',.94).split(',')[1];
          scene.traverse((node) => node.material?.dispose());
        }
        draw('isolated-before.webp', null, false, false);
        draw('candidate-oblique.webp', exact, false, false);
        draw('candidate-closed.webp', closedGeometry, false, false);
        draw('candidate-reverse.webp', exact, true, false);
        draw('candidate-gray.webp', exact, false, true);
        draw('original-oblique.webp', replacement, false, false);
        draw('lighter-trial.webp', light, false, false);
        renderer.dispose();
      }
      return { scanHash, count: candidateParts.length, metrics, evidence, motionMm, closedErrorMm,
        phase: source.phase, lighterTriangles: indices.length / 3,
        maxDeviationMm, maxFreeEdgeDeviationMm };
    }, { before:isBaseline, save:Boolean(output) });
    if (output) {
      for (const [name, data] of Object.entries(result.evidence)) await writeFile(join(output, name), Buffer.from(data,'base64'));
    }
    delete result.evidence;
    return result;
  } finally {
    await page.close();
  }
}

try {
  const before = await review(baseline, true);
  const after = await review(candidate, false);
  assert.equal(before.count, 0, 'Baseline already exposes an aortic cusp mesh');
  assert.equal(after.count, 3);
  assert.equal(before.scanHash, after.scanHash, 'Modeled scan changed with the 3D geometry update');
  for (const cusp of after.metrics) {
    assert.equal(cusp.vertices, 133);
    assert.equal(cusp.triangles, 216);
    assert.equal(cusp.boundaryEdges, 48);
    assert.equal(cusp.nonmanifoldEdges, 0);
    assert.ok(cusp.sourceErrorMm < .00001);
  }
  assert.ok(after.motionMm > .1 && after.closedErrorMm < .00001, 'Leaflet deformation is not bound to acquisition phase');
  const report = { before, after };
  if (output) await writeFile(join(output, 'measurements.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
