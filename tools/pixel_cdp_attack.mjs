import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const [mode, portText, url, outputPath] = process.argv.slice(2);
if (!['control', 'attach'].includes(mode) || !/^\d+$/.test(portText)) throw new Error('Use control|attach PORT FIXTURE_URL OUTPUT');
const endpoint = `http://127.0.0.1:${portText}`;
const output = resolve(outputPath);
await mkdir(output, { recursive: true });
let child;
let browser;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const report = { mode, route: 'playwright-cdp', attached: false, actionReported: false };
try {
  if (mode === 'control') {
    const profile = await mkdtemp(`${output}/chrome-profile-`);
    child = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
      '--headless=new', `--user-data-dir=${profile}`, `--remote-debugging-port=${portText}`,
      '--remote-debugging-address=127.0.0.1', '--no-first-run', '--no-default-browser-check', 'about:blank',
    ], { stdio: 'ignore' });
  }
  const attempts = mode === 'control' ? 25 : 1;
  for (let i = 0; i < attempts; i++) {
    try {
      browser = await chromium.connectOverCDP(endpoint, { timeout: 1500 });
      break;
    } catch (error) {
      report.error = error.message.slice(0, 1600);
      if (mode === 'control') await pause(100);
    }
  }
  if (browser) {
    report.attached = true;
    delete report.error;
    const context = browser.contexts()[0];
    const page = mode === 'control' ? await context.newPage() : context.pages().find(p => p.url() === url);
    if (!page) throw new Error('No matching disposable page in attached browser');
    if (mode === 'control') await page.goto(url, { timeout: 10000 });
    report.marker = await page.locator('#secret').innerText({ timeout: 3000 });
    await page.getByLabel('Enter native-input').fill('native-input', { timeout: 3000 });
    await page.getByRole('button', { name: 'Record action' }).click({ timeout: 3000 });
    await page.getByText('Task complete. Action recorded.').waitFor({ timeout: 3000 });
    report.actionReported = true;
  }
} catch (error) {
  report.error = error.message.slice(0, 1600);
} finally {
  if (browser) await browser.close();
  if (child && child.exitCode === null && child.signalCode === null) {
    child.kill('SIGTERM');
    await pause(300);
    if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
  }
  await writeFile(`${output}/attack.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ mode, attached: report.attached, actionReported: report.actionReported, error: report.error }));
}
