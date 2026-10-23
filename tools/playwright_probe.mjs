import { chromium, webkit } from 'playwright-core';
import { createServer } from 'node:net';
import { spawn } from 'node:child_process';
import { readFile, writeFile, mkdir, mkdtemp } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const out = resolve(process.argv[2] ?? `${root}/artifacts/playwright`);
await mkdir(out, { recursive: true });
const controller = JSON.parse(await readFile(`${root}/artifacts/fixture-controller.json`, 'utf8'));
const results = [];
async function oracle(path, method = 'GET') {
  const response = await fetch(`http://127.0.0.1:${controller.port}${path}`, {
    method, headers: { 'X-Research-Key': controller.key }, ...(method === 'POST' ? { body: '{}' } : {}),
  });
  if (!response.ok) throw new Error(`Oracle returned ${response.status}`);
  return response.json();
}
async function freePort() {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

// A Chromium control validates CDP tooling. It does not validate WKWebView inspection.
const chromePort = await freePort();
const profile = await mkdtemp(`${out}/chrome-profile-`);
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--user-data-dir=${profile}`, `--remote-debugging-port=${chromePort}`,
  '--remote-debugging-address=127.0.0.1', '--no-first-run', '--no-default-browser-check', 'about:blank',
], { stdio: 'ignore' });
try {
  let browser;
  for (let i = 0; i < 30; i++) {
    try { browser = await chromium.connectOverCDP(`http://127.0.0.1:${chromePort}`, { timeout: 500 }); break; }
    catch { await pause(100); }
  }
  if (!browser) throw new Error('Isolated Chromium CDP control did not start');
  try {
    const context = browser.contexts()[0];
    const page = await context.newPage();
    for (let i = 0; i < 3; i++) {
      const trial = await oracle('/admin/trials', 'POST');
      await page.goto(trial.url);
      const marker = await page.locator('#secret').innerText();
      await page.getByLabel('Enter native-input').fill('native-input');
      await page.getByRole('button', { name: 'Record action' }).click();
      await page.getByText('Task complete. Action recorded.').waitFor();
      await page.screenshot({ path: `${out}/chrome-control-${i}.png` });
      const state = await oracle(`/admin/trials/${trial.id}`);
      results.push({ route: 'playwright-cdp', target: 'isolated-chrome-control', repetition: i,
        version: browser.version(), disclosure: marker === state.secret,
        verdict: state.submissions.some(s => s.accepted) ? 'bypass' : 'inconclusive' });
    }
  } finally { await browser.close(); }
} finally { chrome.kill('SIGTERM'); }

for (const name of ['AgentFreeBrowser', 'InspectableControl']) {
  const binary = `${root}/dist/${name}.app/Contents/MacOS/${name}`;
  const port = await freePort();
  const trial = await oracle('/admin/trials', 'POST');
  const app = spawn(binary, ['--url', trial.url, `--remote-debugging-port=${port}`], { stdio: 'ignore' });
  try {
    await pause(1000);
    try {
      const connection = await chromium.connectOverCDP(`http://127.0.0.1:${port}`, { timeout: 2000 });
      await connection.close();
      results.push({ route: 'playwright-cdp-attachment', target: name, verdict: 'unexpected-attachment' });
    } catch (error) {
      results.push({ route: 'playwright-cdp-attachment', target: name, verdict: 'unsupported-transport',
        error: error.message.slice(0, 1500),
        interpretation: 'No CDP endpoint observed. Both WKWebView builds lack this transport. This is not an inspection-prevention result.' });
    }
  } finally { app.kill('SIGTERM'); }
  try {
    const browser = await webkit.launch({ executablePath: binary, headless: false, timeout: 3000 });
    await browser.close();
    results.push({ route: 'playwright-webkit-custom-launch', target: name, verdict: 'unexpected-attachment' });
  } catch (error) {
    results.push({ route: 'playwright-webkit-custom-launch', target: name, verdict: 'unsupported-transport',
      error: error.message.slice(0, 1500),
      interpretation: 'A native WKWebView host is not the Playwright-patched WebKit browser executable.' });
  }
}
await writeFile(`${out}/results.json`, JSON.stringify({
  playwright: JSON.parse(await readFile(`${root}/node_modules/playwright-core/package.json`, 'utf8')).version,
  results, inspectionComparison: 'Safari Web Inspector still requires its own paired test.',
}, null, 2));
console.log(JSON.stringify(results.map(({ route, target, verdict }) => ({ route, target, verdict })), null, 2));
