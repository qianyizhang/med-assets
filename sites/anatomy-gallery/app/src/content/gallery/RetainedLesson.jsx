import React, { useEffect, useRef } from 'react';

const source = 'https://github.com/qianyizhang/med-assets/blob/9d70d26/lessons/';

export function RetainedLesson({ name, html, css, connect }) {
  const host = useRef(null);
  useEffect(() => {
    const shadow = host.current.shadowRoot ?? host.current.attachShadow({ mode: 'open' });
    const main = new DOMParser().parseFromString(html, 'text/html').querySelector('main');
    const root = document.createElement('div');
    root.className = 'lesson-body';
    root.id = main.id;
    root.replaceChildren(...main.childNodes);
    const style = document.createElement('style');
    style.textContent = css;
    for (const link of root.querySelectorAll('a[href^="../../"]')) {
      link.href = new URL(link.getAttribute('href'), source + name + '/index.html').href;
    }
    shadow.replaceChildren(style, root);
    const disconnect = connect(root);
    return () => {
      disconnect?.();
      shadow.replaceChildren();
    };
  }, [name, html, css, connect]);
  return <div ref={host} className="ga-retained-lesson" />;
}
