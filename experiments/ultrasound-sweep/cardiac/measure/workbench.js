import { strainPanel } from './strain.js';
import { colorPanel } from './color-section.js';
import { protocol, sources, spectra, tools } from './protocol.js';
import { signalPanel } from './signal-view.js';
import { caliperPanel, movementPanel, volumePanel } from './sections.js';

export function createMeasureWorkbench({ root, section, getState, onSeek }) {
  root.innerHTML = `<details class="mw"><summary>Doppler &amp; measurements</summary><div class="mw-inside">
    <label class="mw-task">Check <select aria-label="Measurement or Doppler check"></select></label>
    <div class="mw-panel"></div><details class="mw-method"><summary>Methods &amp; sources</summary>
    <p>Distance calipers use the frozen B-mode image and its modeled depth scale. Chamber volumes and TAPSE use the neutral model planes. Spectra assume a separately aligned sample at the named site. Color flow uses the current probe angle. Velocity and respiratory profiles are prescribed examples. Acquired reference images retain their original subject and scale.</p>
    <p class="mw-links"></p></details></div></details>`;
  const details = root.querySelector('details'),
    select = root.querySelector('select'),
    panel = root.querySelector('.mw-panel');
  const context = { section, getState, onSeek, state: getState(), diameter: 2.05, rap: 3, linear: {} };
  const selected = new Map();
  const labels = {
    comprehensive: 'Adult TTE protocol',
    chambers: 'Chamber quantification',
    strain: 'Strain guidance',
    right: 'Right heart',
    diastolic: 'Diastolic function',
  };
  for (const [id, url] of Object.entries(sources)) {
    const a = document.createElement('a');
    a.textContent = labels[id];
    a.href = url;
    root.querySelector('.mw-links').append(a);
  }
  let currentView, updatePanel;
  function mountTask() {
    const id = select.value;
    selected.set(currentView, id);
    updatePanel = null;
    if (spectra[id]) updatePanel = signalPanel(panel, id, context);
    else if (id === 'strain') updatePanel = strainPanel(panel, context);
    else if (id === 'color') updatePanel = colorPanel(panel, context);
    else if (id === 'length') caliperPanel(panel, context);
    else if (id === 'tapse' || id === 'ivc') movementPanel(panel, id, context);
    else volumePanel(panel, id, context);
  }
  function openView() {
    currentView = context.state.viewId;
    const checks = protocol[currentView] || ['length'];
    select.replaceChildren();
    for (const id of checks) {
      const label = spectra[id] ? spectra[id].label + ' · ' + spectra[id].mode : tools[id];
      select.add(new Option(label, id));
    }
    select.value = selected.get(currentView) || checks[0];
    mountTask();
  }
  select.onchange = mountTask;
  details.ontoggle = () => {
    if (details.open) {
      context.state = getState();
      openView();
    }
  };
  return {
    update(state) {
      context.state = state;
      if (!details.open) return;
      if (currentView !== state.viewId) openView();
      else if (updatePanel) updatePanel(state);
    },
  };
}
