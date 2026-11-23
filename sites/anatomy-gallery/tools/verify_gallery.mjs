import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { checkBronchialScenes } from './verification/bronchial-scenes.mjs';
import { checkCardiacScenes } from './verification/cardiac-scenes.mjs';
import { checkGalleryAuthoring, checkGalleryCollections, checkGalleryOvary } from './verification/collections.mjs';
import { checkLayerLessons } from './verification/layer-lessons.mjs';
import { checkLessonPlates } from './verification/lesson-plates.mjs';
import { checkLibrary } from './verification/library.mjs';
import { checkRefinementPlates } from './verification/refinement-plates.mjs';
import { checkRefinementScenes } from './verification/refinement-scenes.mjs';
import { checkStaticReviews } from './verification/static-reviews.mjs';
import { checkTeachingTargets } from './verification/teaching-targets.mjs';

const cases = {
  authoring: checkGalleryAuthoring,
  collections: checkGalleryCollections,
  library: checkLibrary,
  'cardiac-scenes': checkCardiacScenes,
  'bronchial-scenes': checkBronchialScenes,
  'refinement-scenes': checkRefinementScenes,
  'layer-lessons': checkLayerLessons,
  ovary: checkGalleryOvary,
  'lesson-plates': checkLessonPlates,
  'static-reviews': checkStaticReviews,
  'refinement-plates': checkRefinementPlates,
  'teaching-targets': checkTeachingTargets,
};
const suites = {
  catalog: ['authoring', 'collections', 'library'],
  scenes: ['cardiac-scenes', 'bronchial-scenes', 'refinement-scenes'],
  lessons: ['layer-lessons', 'ovary', 'lesson-plates'],
  evidence: ['static-reviews', 'refinement-plates', 'teaching-targets'],
};
const { values } = parseArgs({ options: {
  all: { type: 'boolean' },
  authoring: { type: 'boolean' },
  ovary: { type: 'boolean' },
  suite: { type: 'string', multiple: true },
  case: { type: 'string', multiple: true },
  list: { type: 'boolean' },
} });

if (values.list) {
  for (const [suite, members] of Object.entries(suites)) {
    console.log(suite + '  ' + members.join(', '));
  }
} else {
  const groups = (values.suite || []).flatMap((name) => {
    assert.ok(Object.hasOwn(suites, name), 'Unknown verification suite ' + name);
    return suites[name];
  });
  const selected = new Set([
    ...groups,
    ...(values.case || []),
    ...(values.authoring ? ['authoring'] : []),
    ...(values.ovary ? ['ovary'] : []),
    ...(values.all ? Object.keys(cases) : []),
  ]);
  if (!selected.size) {
    selected.add('authoring');
    selected.add('collections');
  }
  for (const name of selected) {
    assert.ok(Object.hasOwn(cases, name), 'Unknown verification case ' + name);
  }
  const repo = fileURLToPath(new URL('../../../', import.meta.url));
  const loopback = (value) => {
    const url = new URL(value);
    assert.ok(url.protocol === 'http:' && ['127.0.0.1', '[::1]', 'localhost'].includes(url.hostname),
      'Gallery verification requires a loopback preview URL.');
    return url.origin;
  };
  const base = loopback(process.env.MODEL_SURVEY_PREVIEW_URL || 'http://127.0.0.1:8858');
  const publishedPreview = process.env.MODEL_SURVEY_PUBLISHED_PREVIEW_URL;
  if (selected.has('lesson-plates')) {
    assert.ok(publishedPreview, 'Set MODEL_SURVEY_PUBLISHED_PREVIEW_URL to the separate published rehearsal preview.');
  }
  const published = publishedPreview ? loopback(publishedPreview) : undefined;
  const builtApp = path.resolve(process.env.MODEL_SURVEY_APP_DIR
    || path.join(repo, 'sites/anatomy-gallery/.local/app'));
  const output = path.resolve(process.env.MODEL_SURVEY_CAPTURE_DIR
    || path.join(repo, '.artifacts/gallery-verification'));
  const { chromium } = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
  const browser = await chromium.launch({
    executablePath: process.env.MODEL_SURVEY_BROWSER,
    headless: true,
    chromiumSandbox: true,
    args: ['--enable-unsafe-swiftshader'],
  });
  try {
    for (const name of selected) {
      const capture = path.join(output, name);
      await mkdir(capture, { recursive: true });
      const contexts = [];
      const errors = [];
      // Give each behavior a clean browser context and block ambient requests.
      // A case can explicitly fulfill a second origin locally through a page route.
      const newContext = async (options) => {
        const context = await browser.newContext({
          viewport: { width: 1280, height: 900 },
          acceptDownloads: true,
          serviceWorkers: 'block',
          ...options,
        });
        contexts.push(context);
        context.on('page', (page) => page.on('pageerror', (error) => errors.push(String(error))));
        await context.route('**/*', (route) => new URL(route.request().url()).origin === base
          ? route.continue() : route.abort());
        return context;
      };
      const session = {
        newContext,
        newPage: async (options) => (await newContext(options)).newPage(),
        version: () => browser.version(),
      };
      try {
        console.log('Checking ' + name);
        await cases[name]({
          browser: session, base, published, repo, builtApp, capture, directory: capture + path.sep,
        });
        assert.deepEqual(errors, [], name + ' page errors');
      } catch (error) {
        process.exitCode = 1;
        console.error('FAIL ' + name, error);
      } finally {
        await Promise.all(contexts.map((context) => context.close()));
      }
    }
  } finally {
    await browser.close();
  }
}
