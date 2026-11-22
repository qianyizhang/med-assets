// Prepare HTML only. File paths and other legacy pages keep their existing handlers.
const gallery = 'https://med-assets-model-survey.landy123007.chatgpt.site';
const location = 'use-cases/head-and-neck/location';
const duct = 'use-cases/head-and-neck/duct-course';
const salivaryReview = 'compare/salivary-native-r02';
const salivaryExports = 'library/salivary_glands/z-native-scoped-r02';
const bronchialReview = 'compare/bronchial-r13';
const nasalReview = 'compare/nasal-airspace-r01';

const salivary = {
  default: location,
  fragments: {
    annotation: location,
    native: duct, views: duct,
    negative: salivaryReview, 'negative-image': salivaryReview, comparison: salivaryReview,
    checks: salivaryReview, records: salivaryReview, 'record-links': salivaryReview,
    downloads: salivaryExports, 'media-links': salivaryExports,
  },
};
const routes = {
  'anatomy-head-neck-review.landy123007.chatgpt.site': {
    '/': salivary,
    '/review/salivary-native-r02/': salivary,
  },
  'anatomy-airway-review.landy123007.chatgpt.site': {
    '/': {
      default: 'use-cases/airway',
      fragments: { title: bronchialReview, intro: bronchialReview, panels: bronchialReview },
    },
    '/review/bronchial-r13/': { default: bronchialReview, restoreBookmark: true },
    '/review/nasal-airspace-2026-10-26/': { default: nasalReview },
    '/review/trachea-r06/': { default: 'compare/trachea-r06' },
  },
};

export function legacyHandoff(host, path, original) {
  const pages = Object.hasOwn(routes, host) && routes[host];
  const page = pages && Object.hasOwn(pages, path) && pages[path];
  if (!page) return null;
  const href = gallery + '/#/' + page.default;
  const link = `<a id="anatomy-gallery-handoff" href="${href}">Open in Anatomy Gallery <span lang="zh">／在解剖图集中打开</span></a>`;
  if (page.restoreBookmark) {
    const notice = `<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bronchial tree · central junction r13</title>
<main>
  <h1>Bronchial tree · central junction r13</h1>
  <p>${link}</p>
</main>
</html>`;
    if (original == null || original === '' || original === notice) return notice;
  }

  // The browser alone sees the fragment. A plain link works with JavaScript disabled.
  const update = page.fragments ? `<script>
(() => {
  const destinations = ${JSON.stringify(page.fragments)};
  const link = document.getElementById('anatomy-gallery-handoff');
  const target = new URL(link.href);
  const defaultHash = target.hash;
  function update() {
    let fragment = window.location.hash.slice(1);
    try { fragment = decodeURIComponent(fragment); } catch {}
    target.hash = Object.hasOwn(destinations, fragment) ? '/' + destinations[fragment] : defaultHash;
    link.href = target.href;
  }
  update();
  window.addEventListener('hashchange', update);
})();
</script>` : '';
  // Several of the original pages omit the optional body start tag.
  const main = /<main\b[^>]*>/iu;
  if (typeof original !== 'string' || !main.test(original)) {
    throw new Error('The original legacy HTML is required for this handoff.');
  }
  const navigation = `<nav aria-label="Anatomy Gallery"><p>${link}</p></nav>${update}`;
  if (original.includes(navigation)) return original;
  return original.replace(main, (opening) => opening + navigation);
}
