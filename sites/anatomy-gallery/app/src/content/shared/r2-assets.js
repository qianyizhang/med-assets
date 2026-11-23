// The pinned Site Worker imports this entry point.
import release from '../assets/gallery-release.json' with { type: 'json' };
import { createGalleryDelivery } from './release-delivery.js';

export function createAssetDelivery(manifest, ownerCanEdit) {
  return createGalleryDelivery(manifest, ownerCanEdit, release);
}
