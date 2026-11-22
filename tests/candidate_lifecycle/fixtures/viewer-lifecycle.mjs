// Document ownership outlives a failed interactive view: fallback stays usable.
export function createViewerLifecycle(target) {
  let state = 'active', view = null, failed = false;
  const viewerDisposers = [], documentDisposers = [];
  function releaseView() {
    view?.suspend();
    view = null;
    for (const cleanup of viewerDisposers.splice(0).reverse()) cleanup();
  }
  function fail() {
    if (state === 'disposed' || failed) return;
    failed = true;
    releaseView();
  }
  function dispose() {
    if (state === 'disposed') return;
    state = 'disposed';
    target.removeEventListener('pagehide', hide);
    target.removeEventListener('pageshow', show);
    releaseView();
    for (const cleanup of documentDisposers.splice(0).reverse()) cleanup();
  }
  function hide(event) {
    if (!event.persisted) { dispose(); return; }
    if (state !== 'active') return;
    state = 'suspended';
    view?.suspend();
  }
  function show(event) {
    if (!event.persisted || state !== 'suspended') return;
    state = 'active';
    view?.resume();
  }
  target.addEventListener('pagehide', hide);
  target.addEventListener('pageshow', show);
  return {
    get disposed() { return state === 'disposed'; },
    get suspended() { return state === 'suspended'; },
    get failed() { return failed; },
    async wait(promise) {
      const value = await promise;
      if (state === 'disposed') throw new Error('Viewer document disposed');
      return value;
    },
    own(cleanup, scope = 'viewer') {
      if (state === 'disposed' || (scope === 'viewer' && failed)) cleanup();
      else (scope === 'document' ? documentDisposers : viewerDisposers).push(cleanup);
    },
    attach(callbacks) {
      if (view) throw new Error('Viewer lifecycle already attached');
      if (state === 'disposed' || failed) return;
      view = callbacks;
      if (state === 'active') view.resume();
    },
    fail,
    dispose,
  };
}
