// Section the delivered triangle surfaces in their original millimetre coordinates.
async function readMesh(path) {
  const response = await fetch('data/' + path);
  if (!response.ok) throw new Error('Lumen mesh unavailable');
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength < 8) throw new Error('Incomplete lumen mesh');
  const header = new DataView(buffer);
  const n = header.getUint32(0, true), t = header.getUint32(4, true);
  if (!n || !t || buffer.byteLength !== 8 + 12 * (n + t)) throw new Error('Invalid lumen mesh');
  return {vertices: new Float32Array(buffer, 8, 3 * n), faces: new Uint32Array(buffer, 8 + 12 * n)};
}

export async function loadSurfaces(recon) {
  const [stitch, ...model] = await Promise.all([
    recon.reconstructionPath, ...['cca','ica','eca'].map(id => recon.sourcePaths[id]),
  ].map(readMesh));
  return {stitch, model};
}

// One scanline fill per solid. Combining the three masks before drawing removes
// the internal edges where the teaching-model branches meet the common trunk.
export function sectionMask(meshes, info, [u,v,d], slice, factor = 2) {
  const w = info.size[u] * factor, h = info.size[v] * factor;
  const mask = new Uint8Array(w * h);
  const z = info.originMm[d] + slice * info.spacingMm[d];
  const project = (mm, axis) => factor * (info.size[axis] - .5 - (mm-info.originMm[axis])/info.spacingMm[axis]);
  for (const {vertices, faces} of meshes) {
    const rows = Array.from({length:h}, () => []);
    for (let f=0; f<faces.length; f+=3) {
      const a = 3*faces[f], b = 3*faces[f+1], c = 3*faces[f+2];
      const below = vertices[a+d] < z;
      if ((vertices[b+d]<z) === below && (vertices[c+d]<z) === below) continue;
      const cut = [];
      for (const [p,q] of [[a,b],[b,c],[c,a]]) {
        if ((vertices[p+d] < z) === (vertices[q+d] < z)) continue;
        const t = (z-vertices[p+d]) / (vertices[q+d]-vertices[p+d]);
        cut.push([project(vertices[p+u]+t*(vertices[q+u]-vertices[p+u]), u),
                  project(vertices[p+v]+t*(vertices[q+v]-vertices[p+v]), v)]);
      }
      if (cut[0][1] > cut[1][1]) cut.reverse();
      const [[x0,y0],[x1,y1]] = cut;
      for (let y=Math.max(0,Math.ceil(y0-.5)); y<Math.min(h,Math.ceil(y1-.5)); y++) {
        rows[y].push(x0 + (y+.5-y0)*(x1-x0)/(y1-y0));
      }
    }
    for (let y=0; y<h; y++) {
      const hits = rows[y].sort((a,b) => a-b);
      for (let i=1; i<hits.length; i+=2) {
        const start = Math.max(0, Math.ceil(hits[i-1]-.5));
        const end = Math.min(w, Math.ceil(hits[i]-.5));
        if (end > start) mask.fill(1, y*w+start, y*w+end);
      }
    }
  }
  return mask;
}

export function sectionLayer(surfaces, info, axes, slice) {
  const factor = 3;
  const model = sectionMask(surfaces.model, info, axes, slice, factor);
  const stitch = sectionMask([surfaces.stitch], info, axes, slice, factor);
  const layer = document.createElement('canvas');
  layer.width = info.size[axes[0]] * factor;
  layer.height = info.size[axes[1]] * factor;
  const w = layer.width;
  const ctx = layer.getContext('2d');
  const pixels = ctx.createImageData(w, layer.height);
  for (let i=0; i<model.length; i++) {
    if (model[i] && (!model[i-1] || !model[i+1] || !model[i-w] || !model[i+w])) {
      pixels.data.set([255,187,104,255], i*4);
    } else if (stitch[i]) pixels.data.set([120,177,228,150], i*4);
  }
  ctx.putImageData(pixels, 0, 0);
  return layer;
}
