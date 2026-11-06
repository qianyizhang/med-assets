/* Bounded adapter for the pinned BP3D r02 source, not a general glTF loader. */
'use strict';
const crypto = require('node:crypto');
const C = require('./controller.js');
const source = require('./bp3d-source.json');
function readSource(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length !== source.bytes ||
      crypto.createHash('sha256').update(bytes).digest('hex') !== source.sha256)
    throw new Error('Expected exact BP3D r02 source bytes.');
  if (bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2 ||
      bytes.readUInt32LE(8) !== bytes.length || bytes.readUInt32LE(16) !== 0x4e4f534a)
    throw new Error('Invalid GLB container.');
  const doc = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString('utf8'));
  // This source has flat identity nodes; never silently discard a transform.
  if (doc.nodes.length !== source.nodes.length || doc.nodes.some((n, i) =>
      n.name !== source.nodes[i].name || n.extras.source_file_id !== source.nodes[i].id ||
      n.mesh !== i || n.children || n.matrix || n.translation || n.rotation || n.scale))
    throw new Error('Unsupported source node contract.');
  const labels = doc.nodes.map(n => n.name);
  const parts = labels.map(label => ({label, matrix:[...C.IDENTITY]}));
  // This smoke path supports named isolation only. No invented tooth displacement.
  const contract = {labels, offsets:Object.fromEntries(labels.map(label => [label,[0,0,0]]))};
  return {parts, contract, doc};
}
module.exports = {readSource, source};
