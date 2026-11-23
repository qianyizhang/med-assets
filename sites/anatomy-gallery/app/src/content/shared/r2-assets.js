// The pinned Site Worker imports this entry point.
import { createAssetDelivery as assetHandler } from './asset-delivery.js';
import { studies } from '../gallery/catalog.js';

export function createAssetDelivery(manifest, ownerCanEdit) {
  const serveAsset = assetHandler(manifest, ownerCanEdit);
  return (request, env) => {
    const url = new URL(request.url);
    if (url.pathname !== '/rubric' && url.pathname !== '/api/gallery/v1/studies') {
      return serveAsset(request, env);
    }
    const headers = {
      'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store',
      'access-control-allow-origin': '*', 'x-content-type-options': 'nosniff',
    };
    if (!['GET', 'HEAD'].includes(request.method)) {
      return Response.json({ error: 'Read only.' }, { status: 405, headers });
    }
    if (url.pathname === '/rubric') return Response.redirect(new URL('/#/rubric', url), 302);
    return new Response(request.method === 'HEAD' ? null : JSON.stringify(studies), { headers });
  };
}
