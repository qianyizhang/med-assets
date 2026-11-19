import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {mkdtemp, readFile, rm, writeFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {setTimeout as pause} from "node:timers/promises";
import {pathToFileURL} from "node:url";

const profile = await mkdtemp(join(tmpdir(), "med-survey-chrome-"));
const browser = spawn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", [
  "--headless", "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"
], {stdio: "ignore"});
const reportDir = process.env.MED_ASSETS_REPO
  ? pathToFileURL(join(process.env.MED_ASSETS_REPO, ".artifacts/body-systems-survey-2026-11-19") + "/")
  : new URL("../../.artifacts/body-systems-survey-2026-11-19/", import.meta.url);
const med = new URL("media/", reportDir);
const out = file => new URL(file, med);

async function start() {
  let port;
  for (let attempt = 0; attempt < 50 && browser.exitCode === null; attempt++) {
    const active = await readFile(join(profile, "DevToolsActivePort"), "utf8").catch(() => "");
    if (active) {
      port = active.split("\n")[0];
      break;
    }
    await pause(130);
  }
  if (!port) throw new Error("Chrome did not expose a debugging port");
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const socket = new WebSocket(tabs.find(tab => tab.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, {once: true});
    socket.addEventListener("error", reject, {once: true});
  });
  return socket;
}

const socket = await start();
let serial = 0;
const waiting = new Map();
socket.addEventListener("message", ({data}) => {
  const message = JSON.parse(data);
  waiting.get(message.id)?.(message);
});
function send(method, params = {}) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { waiting.delete(id); reject(new Error(`${method} timed out`)); }, 15000);
    waiting.set(id, ({result, error}) => {
      clearTimeout(timer);
      waiting.delete(id);
      if (error) reject(new Error(JSON.stringify(error)));
      else resolve(result);
    });
    socket.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const {result, exceptionDetails} = await send("Runtime.evaluate", {
    expression, awaitPromise: true, returnByValue: true,
  });
  assert.equal(exceptionDetails, undefined, JSON.stringify(exceptionDetails));
  return result.value;
}
async function goto(url, selector) {
  const outcome = await send("Page.navigate", {url});
  if (outcome.errorText) throw new Error(outcome.errorText);
  for (let attempt = 0; attempt < 32; attempt++) {
    const ready = await evaluate(`document.readyState === "complete" && Boolean(document.querySelector(${JSON.stringify(selector)}))`);
    if (ready && await evaluate(`location.href.startsWith(${JSON.stringify(url)})`)) return;
    await pause(125);
  }
  throw new Error(`Expected ${selector} after navigation`);
}
async function capture(path) {
  const result = await send("Page.captureScreenshot", {format: "png"});
  await writeFile(path, Buffer.from(result.data, "base64"));
}
async function viewport(width, height) {
  await send("Emulation.setDeviceMetricsOverride", {width, height, mobile: false, deviceScaleFactor: 1});
}

const verified = {};
try {
  await send("Page.enable");
  await viewport(1360, 960);
  const report = new URL("index.html", reportDir).href;
  await goto(report, "#page-title");
  const documentCheck = await evaluate(`(async () => {
    const plates = [...document.querySelectorAll(".system .plate")];
    const images = [...document.images];
    const decoded = await Promise.all([...new Set(images.map(img => img.src))].map(async src => {
      const image = new Image(); image.src = src; await image.decode(); return image.width > 0;
    }));
    const invalidAnchors = [...document.querySelectorAll('a[href^="#"]')].filter(a => !document.getElementById(a.hash.slice(1)));
    return {systemCount: document.querySelectorAll(".system").length, plateCount: plates.length,
      paired: plates.every(plate => plate.querySelectorAll("img").length === 2),
      decoded: decoded.length, allDecoded: decoded.every(Boolean), invalidAnchors: invalidAnchors.length,
      overflow: document.documentElement.scrollWidth > innerWidth};
  })()`);
  assert.equal(documentCheck.systemCount, 11);
  assert.equal(documentCheck.allDecoded, true);
  assert.equal(documentCheck.paired, true);
  assert.equal(documentCheck.invalidAnchors, 0);
  assert.equal(documentCheck.overflow, false);
  verified.report = documentCheck;
  const deliveries = await evaluate(`[...document.querySelectorAll(".system")].map(s => ({
    id:s.id, models:s.querySelectorAll(".downloads a[href$='.glb']").length,
    visiblePairs:s.querySelectorAll(".combined-grid > .plate").length,
    legends:[...s.querySelectorAll("figure[data-plate]")].every(p => p.querySelector(".legend li")),
    detail:s.querySelector(".asset-detail summary")?.textContent,
    status:s.querySelector(".status")?.textContent,
    evidence:s.querySelector(".downloads")?.textContent.includes("Review and checks")
  }))`);
  assert.ok(deliveries.every(s => s.models > 0 && s.evidence && s.visiblePairs > 0
    && s.legends && s.detail.startsWith("Asset detail")));
  const withWorkshop = process.argv.includes("--with-s1233");
  const assemblyPlates = withWorkshop ? 12 : 13;
  const detailPlates = withWorkshop ? 58 : 56;
  assert.equal(deliveries.reduce((n, s) => n + s.visiblePairs, 0), assemblyPlates);
  if (withWorkshop) {
    assert.equal(await evaluate(`document.querySelector("#digestive figure[data-plate=assembly] h4").textContent`),
      "Same-case esophagus through colon");
    const venousLegend = await evaluate(`document.querySelector("#cardiovascular figure[data-plate=assembly] .legend").textContent`);
    assert.match(venousLegend, /Inferior vena cava/);
    assert.match(venousLegend, /Superior vena cava/);
  }
  assert.equal(deliveries.find(s => s.id === "cardiovascular").status, "Partial assembly");
  assert.equal(deliveries.find(s => s.id === "nervous").status, "Illustrative placement");
  assert.equal(await evaluate('document.querySelectorAll("figure[data-plate=detail]").length'), detailPlates);
  assert.equal(await evaluate(`[...document.querySelectorAll("#urinary figure[data-plate=assembly] .legend li")]
    .some(e => /glomerular|bowman|filtration/i.test(e.textContent))`), false);
  verified.gallery = {assemblyPlates, detailPlates, legends: true, scopedStatuses: true};
  verified.deliveredModels = deliveries.reduce((n,s)=>n+s.models,0);
  assert.equal(verified.deliveredModels, withWorkshop ? 14 : 12);
  await capture(join(tmpdir(), "med-systems-desktop.png"));
  await evaluate(`document.querySelector('a[href="#urinary"]').click(); location.hash`);
  assert.equal(await evaluate("location.hash"), "#urinary");
  await evaluate(`document.querySelector("#urinary details summary").focus()`);
  assert.equal(await evaluate('document.activeElement.matches("#urinary details summary")'), true);
  await send("Input.dispatchKeyEvent", {type: "keyDown", key: " ", code: "Space", text: " ", windowsVirtualKeyCode: 32});
  await send("Input.dispatchKeyEvent", {type: "keyUp", key: " ", code: "Space", windowsVirtualKeyCode: 32});
  assert.equal(await evaluate(`document.querySelector("#urinary details").open`), true);
  await evaluate('document.querySelector("#urinary .view-heading").scrollIntoView()');
  await pause(200);
  await capture(join(tmpdir(), "med-systems-assembly.png"));
  await viewport(1024, 768);
  assert.equal(await evaluate("document.documentElement.scrollWidth > innerWidth"), false);
  await evaluate("scrollTo(0,0)");
  await capture(join(tmpdir(), "med-systems-laptop.png"));
  verified.interactions = "System jump, keyboard part disclosure, 1024 px laptop reflow";
  await viewport(1360, 960);
  await evaluate('document.querySelector("#comparison").scrollIntoView()');
  await pause(250);
  await capture(join(tmpdir(), "med-systems-comparison.png"));
  if (!process.argv.includes("--local-only")) {
    await viewport(1360, 960);
    try {
      await goto(pathToFileURL(join(tmpdir(), "med-assets-existing-model-survey.html")).href, ".sv-report");
      await capture(out("existing-survey.png"));
      verified.modelSurvey = "Archived self-contained capture";
    } catch (error) {
      verified.modelSurvey = error.message;
    }
    try {
      await goto("https://anatomy-verification.landy123007.chatgpt.site/review/", "body");
      await pause(1600);
      const state = await evaluate(`({url: location.href, title: document.title, body: document.body.innerText.slice(0,850)})`);
      if (!state.url.startsWith("https://anatomy-verification.landy123007.chatgpt.site/review/") ||
          !/model review|anatomy|模型审查|解剖/i.test(state.title) || state.body.length < 50) {
        throw new Error(`Review route returned "${state.title || "untitled"}" with ${state.body.length} visible characters`);
      }
      await capture(out("existing-gallery.png"));
      verified.gallery = "Live review route capture";
    } catch (error) {
      verified.gallery = error.message;
    }
  }
  console.log(JSON.stringify(verified, null, 2));
} finally {
  socket.close();
  if (browser.exitCode === null) {
    browser.kill();
    await new Promise(resolve => browser.once("exit", resolve));
  }
  await rm(profile, {recursive: true, force: true});
}
