import { assetRoute } from '../shared/asset-index.mjs';

export function compileLibrary(selected, teachingReview) {
  const assessments = {};
  function reference(value) {
    if (!value) return undefined;
    const { export: file, maintained, task, route, rubric } = value;
    const id = JSON.stringify([file.path, file.sha256, value.taskId ?? maintained?.taskId ?? task, route, rubric?.revision, value.date]);
    const { releaseEvidence, ...assessment } = value;
    if (assessments[id] && JSON.stringify(assessments[id]) !== JSON.stringify(assessment)) {
      throw Error('Conflicting assessments for ' + file.path + ' ' + task);
    }
    assessments[id] = assessment;
    return id;
  }
  function pack({ assessment, previousAssessment, fileAssessments, ...record }) {
    return {
      ...record, assessment: reference(assessment), previousAssessment: reference(previousAssessment),
      fileAssessments: fileAssessments && Object.fromEntries([...fileAssessments]
        .map(([path, entry]) => [path, reference(entry)])),
    };
  }
  const families = new Set();
  const revisions = new Set();
  const rows = selected.map(({ history, recommended, lessons, ...row }) => {
    if (!row.id || families.has(row.id)) throw Error('Duplicate Library family: ' + row.id);
    families.add(row.id);
    for (const record of history) {
      if (!record.library || revisions.has(record.library)) throw Error('Duplicate Library revision: ' + record.library);
      revisions.add(record.library);
    }
    const id = (record) => {
      if (!history.includes(record)) throw Error('Recommended lesson is outside its family history.');
      return record.library;
    };
    return { ...pack(row), history: history.map(pack), recommended: recommended && id(recommended), lessons: lessons?.map(id) };
  });
  const teaching = teachingReview && {
    assessments: teachingReview.assessments.map(reference),
    campaign: teachingReview.campaign?.map(reference),
  };
  return { rows, assessments, teaching };
}

export function checkMembership(selected, publicIndex, resources) {
  const urls = new Set([...publicIndex.assets.map(assetRoute), ...resources.map(resource => resource.url)]);
  const visit = value => {
    if (typeof value === 'string') {
      if (value.startsWith('/assets/') || value.startsWith('/review-evidence/') || value.startsWith('/reviews/')) {
        if (!urls.has(value)) throw Error('Library resource is outside the release: ' + value);
      }
    } else if (value && typeof value === 'object') {
      if (value.name && value.sha256 && value.mediaType && !value.unavailable
        && !urls.has(value.url?.startsWith('/') ? value.url : assetRoute(value))) {
        throw Error('Library export is outside the release: ' + value.path);
      }
      Object.values(value).forEach(visit);
    }
  };
  visit(selected);
}
