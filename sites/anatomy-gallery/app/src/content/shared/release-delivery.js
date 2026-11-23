import { createAssetDelivery, readAsset } from './asset-delivery.js';

const headers = {
  'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store',
  'access-control-allow-origin': '*', 'x-content-type-options': 'nosniff',
};

export function createGalleryDelivery(publicIndex, ownerCanEdit, release) {
  const serveAsset = createAssetDelivery(publicIndex, ownerCanEdit);
  const resources = new Map(release.resources.map(resource => [resource.url, resource]));
  return (request, env) => {
    const url = new URL(request.url);
    if (url.pathname === '/rubric' || url.pathname === '/api/gallery/v1/studies') {
      if (!['GET', 'HEAD'].includes(request.method)) {
        return Response.json({ error: 'Read only.' }, { status: 405, headers });
      }
      if (url.pathname === '/rubric') return Response.redirect(new URL('/#/rubric', url), 302);
      return new Response(request.method === 'HEAD' ? null : JSON.stringify(release.studies), { headers });
    }
    const resource = resources.get(url.pathname);
    if (!resource) return serveAsset(request, env);
    if (url.search) {
      return Response.json({ error: 'Asset query parameters are not supported.' }, { status: 400, headers });
    }
    return readAsset(request, resource.localOnly ? env.LOCAL_GALLERY_FILES : env.BUCKET, resource);
  };
}
