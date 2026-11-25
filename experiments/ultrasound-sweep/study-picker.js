// Both the pose sweeps and the independent cardiac cycle share this study menu.
function configureStudyPicker(picker, tours, selected, root) {
  const groups = new Map();
  function option(region, title, id) {
    if (!groups.has(region)) {
      const group = document.createElement('optgroup');
      group.label = region;
      picker.append(group);
      groups.set(region, group);
    }
    groups.get(region).append(new Option(title, id));
  }
  for (const tour of tours) {
    const region = tour.pregnancyStage ? 'Pregnancy · ' + tour.pregnancyStage.age : tour.bodyRegion ?? 'Abdomen';
    option(region, tour.title, tour.id);
  }
  option('Heart', 'Adult echocardiography', 'cardiac-a4c');
  picker.value = selected;
  picker.disabled = false;
  picker.onchange = () => {
    const cardiac = picker.value === 'cardiac-a4c';
    const url = new URL(cardiac ? 'cardiac/?view=plax' : 'index.html', root);
    if (!cardiac) url.searchParams.set('sweep', picker.value);
    location.assign(url);
  };
  window.addEventListener('pageshow', () => { picker.value = selected; });
}
