// Surface nets retain the sampled contour but expose lattice ridges under
// moving light. This bounded fairing changes positions only, never topology.
export function refineSurface(geometry, spacing, protectedPoints = []) {
  const positions = geometry.attributes.position.array;
  const indices = geometry.index.array;
  if (!indices.length) return geometry;
  const original = positions.slice();
  const count = positions.length / 3;
  const neighbors = Array.from({ length: count }, () => new Set());
  for (let face = 0; face < indices.length; face += 3) {
    const a = indices[face], b = indices[face + 1], c = indices[face + 2];
    neighbors[a].add(b).add(c);
    neighbors[b].add(a).add(c);
    neighbors[c].add(a).add(b);
  }

  // Hold the immediate contours next to saved calipers and small distal
  // landmarks. Broader faces receive up to 0.58 times the working-grid pitch.
  const limits = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const j = i * 3;
    let allowance = 1;
    for (const { point: [x, y, z], radius } of protectedPoints) {
      const distance = Math.hypot(original[j] - x, original[j + 1] - y, original[j + 2] - z);
      const blend = Math.max(0, Math.min(1, (distance - radius) / (2 * spacing)));
      allowance = Math.min(allowance, blend * blend * (3 - 2 * blend));
    }
    limits[i] = 0.58 * spacing * allowance;
  }

  const buffer = new Float32Array(positions.length);
  // Alternating smoothing and inflation limits loss of profile volume.
  // The final position is bounded against the original surface-net vertex.
  for (const gain of [0.47, -0.49, 0.47, -0.49, 0.47, -0.49, 0.47]) {
    for (let i = 0; i < count; i++) {
      const j = i * 3;
      const adjacent = neighbors[i];
      let x = 0, y = 0, z = 0;
      for (const n of adjacent) {
        x += positions[n * 3];
        y += positions[n * 3 + 1];
        z += positions[n * 3 + 2];
      }
      const weight = adjacent.size ? gain / adjacent.size : 0;
      const dx = positions[j] + weight * (x - positions[j] * adjacent.size) - original[j];
      const dy = positions[j + 1] + weight * (y - positions[j + 1] * adjacent.size) - original[j + 1];
      const dz = positions[j + 2] + weight * (z - positions[j + 2] * adjacent.size) - original[j + 2];
      const limit = Math.min(1, limits[i] / (Math.hypot(dx, dy, dz) || 1));
      buffer[j] = original[j] + dx * limit;
      buffer[j + 1] = original[j + 1] + dy * limit;
      buffer[j + 2] = original[j + 2] + dz * limit;
    }
    positions.set(buffer);
  }
  geometry.attributes.position.needsUpdate = true;
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}
