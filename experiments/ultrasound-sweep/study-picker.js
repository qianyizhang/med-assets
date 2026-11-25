function configureStudyPicker(picker, tours, selected, root) {
  const groups = new Map();
  const examPaths = new Map();
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
    const exam = tour.combinedExam;
    if (exam && !examPaths.has(exam.path)) {
      examPaths.set(exam.path, exam.path);
      option(region, exam.title, exam.path);
    }
    option(region, tour.title, tour.id);
  }
  const cardiacId = 'cardiac-a4c';
  examPaths.set(cardiacId, 'cardiac/?view=plax');
  option('Heart', 'Adult echocardiography', cardiacId);
  picker.value = selected;
  picker.disabled = false;
  picker.onchange = () => {
    const examPath = examPaths.get(picker.value);
    if (examPath) {
      location.assign(new URL(examPath, root));
      return;
    }
    const url = selected === cardiacId ? new URL('index.html', root) : new URL(location.href);
    url.searchParams.set('sweep', picker.value);
    url.hash = '';
    location.assign(url);
  };
  window.addEventListener('pageshow', () => { picker.value = selected; });
}
