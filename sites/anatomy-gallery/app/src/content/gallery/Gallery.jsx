import React, { useEffect, useRef, useState } from 'react';
import {
  route, libraryId, studyId, reviewId, bodyPartsAdrenal, comparePath, bodyPartsReviewPath,
  adrenalCandidateBookmark, adrenalStudyBookmark, salivary, airway, staticReviews,
} from './catalog.js';
import { adrenalLesson, adrenalLibrary } from './adrenal-study.js';
import { FDI31_ID } from '../shared/fdi31-download.js';
import { useDataApp } from '../../data-app-public.jsx';
import { componentPermalinkId, componentPermalinkShortId, readComponentPermalink } from '../../chart-permalink.js';
import { Library, Revision, CollectionEntry } from './Library.jsx';
import teachingReview from './teaching-inputs/teaching-assessments.json';
import { libraryAliases, libraryRows, selectExactExport } from './library-data.js';
import { firstForkPath, isLoopbackGallery } from './local-models.js';
import { UseCases, Lesson } from './UseCases.jsx';
import { Planning, surveyCoverageId } from './Planning.jsx';
import { Systems } from './Systems.jsx';
import { Compare } from './Compare.jsx';
import { Refinements, TeachingTarget } from './Refinements.jsx';
import { BodyPartsReview } from './BodyPartsReview.jsx';
import { SalivaryLesson, SalivaryReview } from './Salivary.jsx';
import { Archive, DentalFilms } from './Archive.jsx';
import {
  DentalLayers, DentalShotStudies, HeartSlice, OneBreath,
  dentalLayersPath, dentalShotsPath, heartSlicePath, oneBreathPath,
} from './SpecialistStills.jsx';
import { KidneyTrial } from './KidneyTrial.jsx';
import { DentalArch } from './DentalArch.jsx';
import { PathwayLesson } from './Pathways.jsx';
import { pathways } from './pathway-data.js';
import { OralSpacesLesson, RegionalLocators } from './Teaching.jsx';
import { oralSpacesPath, ovaryPickupDetail, regionalPath } from './teaching-data.js';
import { SkeletalLesson, skeletalDetail } from './SkeletalLesson.jsx';
import { skeletalPath } from './skeletal-data.js';
import { AirwayLesson, AirwayReview, FirstForkLesson } from './Airway.jsx';
import { StaticReview } from './StaticReviews.jsx';
import { Stage } from './Stage.jsx';
import { Rubric } from './Rubric.jsx';
import { Link, Missing } from './GalleryUI.jsx';
import './gallery.css';

const compareBookmarks = new Map([
  [adrenalCandidateBookmark.slice(1), '/' + bodyPartsReviewPath],
  [adrenalStudyBookmark.slice(1), '/' + comparePath],
]);

function currentRoute() {
  const fragment = location.hash.slice(1);
  if (fragment) {
    if (compareBookmarks.has(fragment)) return compareBookmarks.get(fragment);
    if (fragment === FDI31_ID) return '/library/' + fragment;
    if (fragment.startsWith('family-')) return '/library/' + fragment.slice('family-'.length);
    return fragment;
  }
  if (location.pathname === '/rubric') return '/rubric';
  const link = readComponentPermalink(location);
  if (link?.kind === 'component' && [
    surveyCoverageId,
    componentPermalinkShortId(location, surveyCoverageId),
    componentPermalinkId(location, surveyCoverageId),
  ].includes(link.id)) return '/archive/planning/coverage';
  return '/library';
}

function useRoute() {
  const [url, setUrl] = useState(currentRoute);
  useEffect(() => {
    const follow = () => setUrl(currentRoute());
    window.addEventListener('hashchange', follow);
    return () => window.removeEventListener('hashchange', follow);
  }, []);
  return url;
}

function Header({ surface, id }) {
  return (
    <header className="ga-bar">
      <Link to="library" className="ga-brand">
        Anatomy Gallery
      </Link>
      <nav aria-label="Gallery">
        <Link to="library" aria-current={surface === 'library' ? 'page' : undefined}>
          Asset Library
        </Link>
        <Link
          to="use-cases"
          aria-current={
            ['use-cases', 'archive'].includes(surface) && id !== 'systems' ? 'page' : undefined
          }
        >
          Use Cases
        </Link>
        <Link
          to="use-cases/systems"
          aria-current={surface === 'use-cases' && id === 'systems' ? 'page' : undefined}
        >
          Body Systems
        </Link>
        <details className="ga-tools" key={surface}>
          <summary>Tools</summary>
          <div>
            <Link to="compare" aria-current={surface === 'compare' ? 'page' : undefined}>
              Compare
            </Link>
            <Link to="stage" aria-current={surface === 'stage' ? 'page' : undefined}>
              3D Stage
            </Link>
          </div>
        </details>
      </nav>
    </header>
  );
}

export function Gallery() {
  const { snapshot } = useDataApp();
  const localPreview = isLoopbackGallery(location.hostname);
  const raw = useRoute();
  const [path, query = ''] = raw.split('?'),
    [surface, id, revision, ...extra] = (path.replace(/^\//, '') || 'library').split('/');
  const pickup = surface === 'use-cases' && id === 'systems' && revision === 'reproductive' &&
    new URLSearchParams(query).get('detail') === ovaryPickupDetail;
  const focusPath = pickup ? path + '?' + ovaryPickupDetail : path;
  const titleRef = useRef(null),
    lastPath = useRef(focusPath);
  useEffect(() => {
    if (lastPath.current !== focusPath) {
      lastPath.current = focusPath;
      const restore = path === '/library' && history.state?.libraryReturn;
      if (restore) {
        const frame = requestAnimationFrame(() => {
          const target = titleRef.current?.querySelector('a[href="' + CSS.escape(restore.href) + '"]');
          target?.focus({ preventScroll: true });
          window.scrollTo(0, restore.y);
        });
        return () => cancelAnimationFrame(frame);
      }
      titleRef.current?.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }
  }, [focusPath, path]);
  let page = <Missing />;
  if (path.startsWith('/') && !extra.length) {
    const airwayReview = airway.find((record) => record.id === id);
    const staticReview = staticReviews.find((record) => record.id === id);
    if (surface === 'library') {
      const rows = libraryRows(snapshot, teachingReview, { localPreview });
      const canonical = Object.hasOwn(libraryAliases, id) ? libraryAliases[id] : id;
      const row = rows.find((entry) => entry.id === canonical || entry.aliases?.includes(canonical));
      const home = row?.lessons?.find((entry) => entry.family === id) ?? row?.recommended;
      const record = revision
        ? row?.history.find((entry) => entry.library === 'library/' + canonical + '/' + revision)
        : home ?? row?.history.find((entry) => entry.library === salivary.library || entry.library === row.exactLibrary);
      const file = new URLSearchParams(query).get('file');
      const exact = selectExactExport(record, file);
      if (file && !exact) page = <Missing />;
      else if (!id) page = <Library rows={rows} query={query} />;
      else if (id === libraryId) {
        const selected = revision || adrenalLibrary.recommended;
        const study = row.history.find((record) => record.revision === selected);
        page = <Revision revision={selected} assessment={study?.assessment} />;
      } else if (row && (exact || !revision)) {
        const detail = exact?.family === 'cartilage-assembly' ? skeletalDetail(query) : '';
        page = <CollectionEntry row={row} snapshot={snapshot} exact={exact} lessonQuery={detail ? '?from=' + detail : ''} />;
      }
    } else if (surface === 'use-cases' && (!id || id === studyId))
      page = id ? <Lesson stop={revision || adrenalLesson.stops[0].id} /> : <UseCases localPreview={localPreview} />;
    else if (surface === 'use-cases' && id === 'systems') page = <Systems id={revision} query={query} localPreview={localPreview} />;
    else if (surface === 'use-cases' && id === 'head-and-neck') page = <SalivaryLesson stop={revision} query={query} localPreview={localPreview} />;
    else if (surface === 'use-cases' && id === 'airway' && !revision) page = <AirwayLesson localPreview={localPreview} />;
    else if (path === '/' + firstForkPath && localPreview) page = <FirstForkLesson />;
    else if (path === '/' + heartSlicePath) page = <HeartSlice />;
    else if (path === '/' + oneBreathPath) page = <OneBreath />;
    else if (path === '/' + dentalLayersPath) page = <DentalLayers />;
    else if (surface + '/' + id === oralSpacesPath) page = <OralSpacesLesson lang={revision} query={query} />;
    else if (surface + '/' + id === regionalPath) page = <RegionalLocators stop={revision} />;
    else if (surface + '/' + id === skeletalPath) page = <SkeletalLesson id={revision} query={query} />;
    else if (surface === 'use-cases' && id === 'dental-arch' && (!revision || ['upper', 'lower'].includes(revision)))
      page = <DentalArch arch={revision} />;
    else if (surface === 'use-cases' && Object.hasOwn(pathways, id))
      page = <PathwayLesson key={id} id={id} lang={revision} query={query} />;
    else if (path === '/compare/teaching-target' && localPreview)
      page = <TeachingTarget assessments={teachingReview.campaign} query={query} />;
    else if (path === '/compare/teaching-refinements' && localPreview)
      page = <Refinements assessments={teachingReview.campaign} query={query} />;
    else if (surface === 'compare' && staticReview) page = <StaticReview key={path} study={staticReview} chapter={revision} />;
    else if (surface === 'compare' && !revision && airwayReview) page = <AirwayReview study={airwayReview} />;
    else if (surface === 'compare' && !revision && id === 'salivary-native-r02') page = <SalivaryReview />;
    else if (surface === 'compare' && !revision && id === bodyPartsAdrenal.id)
      page = <BodyPartsReview />;
    else if (surface === 'compare' && !revision && (!id || id === reviewId))
      page = <Compare detail={!!id} query={query} refinements={localPreview && teachingReview.campaign.some((row) => row.refinement)} />;
    else if (surface === 'stage' && !revision) page = <Stage key={raw} id={id} query={query} localPreview={localPreview} />;
    else if (surface === 'rubric' && !id) page = <Rubric />;
    else if (surface === 'archive' && !id) page = <Archive />;
    else if (path === '/' + dentalShotsPath) page = <DentalShotStudies />;
    else if (surface === 'archive' && id === 'kidney-outline-trial' && !revision)
      page = <KidneyTrial query={query} />;
    else if (surface === 'archive' && ['dental-image26', 'dental-video-treatments'].includes(id))
      page = <DentalFilms collection={id} id={revision} />;
    else if (surface === 'archive' && id === 'planning')
      page = <Planning snapshot={snapshot} section={revision || 'overlaps'} />;
  }
  return (
    <article className="report-content ga-gallery">
      <Header surface={surface} id={id} />
      <div className="ga-content" ref={titleRef} tabIndex="-1">
        {page}
      </div>
    </article>
  );
}
