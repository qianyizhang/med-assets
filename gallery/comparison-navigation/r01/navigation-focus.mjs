// Explicit study navigation only; no initial-load or selection focus policy.
function visible(node) {
  return !!node?.isConnected && !node.closest('[hidden]') && !node.closest('[inert]');
}
export function focusStudyContext(document) {
  const target=document.getElementById('study-focus');
  if (visible(target)) target.focus({preventScroll:true});
}
export function restoreOverviewFocus(document, studyId) {
  const overview=document.getElementById('review-overview');
  if (!visible(overview)) return;
  const matches=[...overview.querySelectorAll('[data-study]')].filter(node=>node.dataset.study===studyId && visible(node));
  const target=matches.length===1?matches[0]:document.getElementById('overview-search');
  if (visible(target)) target.focus({preventScroll:true});
}
