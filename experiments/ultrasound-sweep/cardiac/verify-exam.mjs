// Walk every window, check the acquired images by decoding them in the served page,
// and capture the section and the body view while the phase and plane are held fixed.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
import {viewOrder} from './reading.js';
const {chromium} = await import(process.env.MODEL_SURVEY_PLAYWRIGHT_MODULE || 'playwright');
const url = process.argv[2] || 'http://127.0.0.1:8887/cardiac/?view=plax';
const folder = process.argv[3];
if (folder) await mkdir(folder, {recursive:true});
const b = await chromium.launch({executablePath:process.env.MODEL_SURVEY_BROWSER,chromiumSandbox:true,args:['--enable-unsafe-swiftshader']});
try {
  const p = await b.newPage({viewport:{width:1360,height:980},reducedMotion:'reduce'});
  const errors = [];
  p.on('pageerror', e=>errors.push(e.message));
  await p.goto(url);
  const by = id => p.locator('#'+id);
  await p.waitForFunction(()=>document.querySelector('#torso-status').hidden && !document.querySelector('#play').disabled);
  const hashes = new Set();
  let panels = 0, clips = 0;
  for (const id of viewOrder) {
    await by('window').selectOption(id);
    await by('pose').click();
    assert.equal(new URL(p.url()).searchParams.get('view'),id);
    assert.equal(await by('phase').inputValue(),'0');
    const image = await by('section').screenshot();
    hashes.add(createHash('sha256').update(image).digest('hex'));
    if (folder) {
      await by('section').screenshot({path:join(folder,id+'-section.png')});
      await by('torso').screenshot({path:join(folder,id+'-pose.png')});
    }
    await by('cine').click();
    await by('ref-status').waitFor({state:'hidden'});
    const options = await by('ref-select').locator('option').evaluateAll(nodes=>nodes.map(n=>n.value));
    for (const value of options) {
      if (value === 'cine') {
        clips++;
        if (id === 'suprasternal-arch') {
          await p.waitForFunction(()=>document.querySelector('#ref-video').readyState>=2);
        } else assert.ok(await by('reference').getAttribute('data-frame') !== null);
      } else {
        await by('ref-select').selectOption(value);
        await p.waitForFunction(n=>{
          const img=document.querySelector('#ref-still');
          return !img.hidden && img.complete && img.naturalWidth>0 && img.src.endsWith('inf'+n+'.jpg');
        },value);
        panels++;
      }
    }
    await by('pose').click();
  }
  assert.equal(hashes.size,viewOrder.length);
  assert.equal(panels,88);
  assert.equal(clips,9);
  await by('window').selectOption('a4c');
  if (folder) await p.screenshot({path:join(folder,'default.png')});
  await by('play').click();
  const phases = await p.evaluate(async () => {
    const seen = new Set(), start = performance.now();
    while (performance.now()-start < 1500) {
      await new Promise(requestAnimationFrame);
      seen.add(document.getElementById('phase').value);
    }
    return seen.size;
  });
  await by('play').click();
  assert.ok(phases >= 12, 'Torso and B-mode must keep playing together.');
  await p.getByRole('button',{name:'End diastole', exact:true}).click();
  const torso = await by('torso').screenshot();
  await by('close-pose').click();
  assert.ok(!(await by('torso').screenshot()).equals(torso), 'Close-up must change the body framing.');
  await by('chest').click();
  if (folder) await by('torso').screenshot({path:join(folder,'contact.png')});
  await by('next').click();
  await p.goBack();
  assert.equal(await by('window').inputValue(),'a4c');
  await p.route('**/torso/skin.raw',r=>r.abort());
  await p.reload();
  await p.getByText(/Torso unavailable/).waitFor();
  await by('model').click();
  assert.ok(await by('scene').isVisible());
  assert.equal(await by('play').isEnabled(),true);
  assert.deepEqual(errors,[]);
  console.log(phases + ' sampled phases in 1.5 s with torso and B-mode playing together.');
  console.log(viewOrder.length+' distinct sections, four contact families, '+clips+' cines, '+panels+' published panels; navigation and torso failure recovery passed.');
} finally { await b.close(); }
