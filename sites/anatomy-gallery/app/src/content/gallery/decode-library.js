export function decodeLibrary(catalog) {
  const assessments = new Map(Object.entries(catalog.assessments));
  function assessment(id) {
    if (id === undefined) return undefined;
    const found = assessments.get(id);
    if (!found) throw Error('Missing Library assessment: ' + id);
    return found;
  }
  function record({ assessment: current, previousAssessment, fileAssessments, ...value }) {
    return {
      ...value,
      assessment: assessment(current),
      previousAssessment: assessment(previousAssessment),
      fileAssessments: fileAssessments && new Map(Object.entries(fileAssessments).map(([path, id]) => [path, assessment(id)])),
    };
  }
  const rows = catalog.rows.map(row => {
    const history = row.history.map(record);
    const historyById = new Map(history.map(entry => [entry.library, entry]));
    function revision(id) {
      if (id === undefined) return undefined;
      const found = historyById.get(id);
      if (!found) throw Error('Missing Library revision: ' + id);
      return found;
    }
    return { ...record(row), history, recommended: revision(row.recommended), lessons: row.lessons?.map(revision) };
  });
  const teachingReview = catalog.teaching && {
    assessments: catalog.teaching.assessments.map(assessment),
    campaign: catalog.teaching.campaign?.map(assessment),
  };
  return { rows, teachingReview };
}
