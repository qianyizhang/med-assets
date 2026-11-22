// A lost interactive view stays unavailable until an explicit document reload.
export function watchContextLoss(canvas, lifecycle, unavailable) {
  let lost = false, detached = false;
  function detach() {
    if (detached) return;
    detached = true;
    canvas.removeEventListener('webglcontextlost', onLoss);
  }
  function onLoss() {
    if (lost || lifecycle.failed || lifecycle.disposed) return;
    lost = true;
    lifecycle.fail();
    unavailable();
  }
  function check() {
    if (lost || lifecycle.failed || lifecycle.disposed) {
      throw new Error('Interactive rendering is no longer available');
    }
  }
  canvas.addEventListener('webglcontextlost', onLoss);
  lifecycle.own(detach);
  return {
    get lost() { return lost; },
    check,
    async wait(promise) {
      const value = await promise;
      check();
      return value;
    },
  };
}

const COPY = {
  en: {
    message: 'The 3D rendering context was lost. Reload this page to try again. The verified download and any linked static evidence remain available.',
    reload: 'Reload page',
  },
  zh: {
    message: '三维渲染上下文已丢失。请重新加载页面重试。已验证的下载及已关联的静态证据仍可使用。',
    reload: '重新加载页面',
  },
};

export function renderContextRecovery(container, language, reload, isDisposed) {
  const copy = COPY[language] || COPY.en;
  const document = container.ownerDocument;
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = copy.reload;
  button.onclick = () => {
    if (button.isConnected && !isDisposed()) reload();
  };
  container.replaceChildren(document.createTextNode(copy.message + ' '), button);
}
