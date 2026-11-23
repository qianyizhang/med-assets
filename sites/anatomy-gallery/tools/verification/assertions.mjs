import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

export function assertIdentity(bytes, expected, label = expected.path || expected.name) {
  assert.equal(bytes.length, expected.bytes, label);
  assert.equal(sha256(bytes), expected.sha256, label);
  return bytes;
}

export async function exactResponse(response, expected, { contentType } = {}) {
  const label = expected.path || expected.name;
  assert.equal(response.status(), 200, label);
  if (contentType) {
    assert.equal(response.headers()['content-type'].split(';')[0], contentType, label);
  }
  return assertIdentity(await response.body(), expected, label);
}

export const galleryRoute = (base, fragment) => base + '/#/' + fragment;
