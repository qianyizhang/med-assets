// Keep older saved acquisitions accessible when opening the redesigned tour.
const savedView = new URL(location.href);
const previousSweep = savedView.searchParams.get('chapter');
if (['liver', 'portal-vein', 'gallbladder'].includes(previousSweep)) {
  const frame = savedView.searchParams.get('frame') ?? '0';
  const sections = [...document.querySelectorAll('.chapters a')];
  const matching = previousSweep === 'liver' && sections.find(({ dataset }) =>
    Number(frame) >= Number(dataset.start) && Number(frame) <= Number(dataset.end));
  if (matching) {
    savedView.searchParams.set('chapter', matching.dataset.chapter);
    history.replaceState(null, '', savedView);
  } else {
    const previous = document.querySelector('#previousView');
    const link = previous.querySelector('a');
    link.href = '../index.html?' + new URLSearchParams({ sweep: previousSweep, frame });
    link.textContent = 'Open your saved ' + previousSweep.replace('-', ' ') + ' sweep frame';
    previous.hidden = false;
    // Retain the original URL until the learner moves, including on reload.
  }
}

const referencePlane = document.querySelector('.pinImage img');
function missingPlane() {
  referencePlane.parentElement.classList.add('missingPlane');
  document.getElementById('pin-instruction').textContent =
    'Starting image unavailable. Choose a letter to inspect its targeted sweep.';
}
referencePlane.addEventListener('error', missingPlane);
if (referencePlane.complete && !referencePlane.naturalWidth) missingPlane();

const pins = document.querySelectorAll('.pin');
for (const pin of pins) {
  pin.addEventListener('click', () => {
    for (const choice of pins) {
      const selected = choice === pin;
      choice.setAttribute('aria-pressed', String(selected));
      document.getElementById(choice.getAttribute('aria-controls')).hidden = !selected;
    }
  });
}
