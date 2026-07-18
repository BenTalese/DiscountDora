// Ad-hoc app driver for agent sessions (UX walks, screenshot audits).
//
// The in-app browser pane runs hidden (no paint/rAF → screenshots time out,
// transition-gated UI wedges), so agent sessions drive a REAL headless Chrome
// via Playwright instead and read the PNGs it writes. This is the interactive
// sibling of the e2e specs — same channel fallback (bundled Chromium isn't
// installable on this box, FU-576 → system Chrome).
//
// Usage:  node e2e/drive.mjs <plan.json>
//
// Plan shape:
// {
//   "baseUrl": "http://localhost:5174",   // default
//   "outDir": "shots",                    // where screenshots land
//   "viewport": "desktop" | "mobile" | {"width":1280,"height":800},
//   "colorScheme": "dark" | "light",
//   "steps": [
//     {"do":"goto","url":"#/stock"},
//     {"do":"click","text":"Filters"},                       // by visible text
//     {"do":"click","role":"button","name":"Sign In"},       // by ARIA role+name
//     {"do":"click","selector":".stock-row >> nth=1"},       // raw selector
//     {"do":"fill","selector":"input[type=search]","value":"milk"},
//     {"do":"press","key":"Escape"},
//     {"do":"wait","ms":800},
//     {"do":"waitFor","selector":".q-dialog"},
//     {"do":"viewport","preset":"mobile"},                   // or width/height
//     {"do":"scheme","value":"light"},
//     {"do":"shot","name":"stock-mobile","fullPage":true},
//     {"do":"text","selector":"body","max":800},             // innerText into results
//     {"do":"eval","js":"location.hash"}                     // serialisable result
//   ]
// }
//
// Every step logs a line; failures record the error and continue (an audit
// wants the rest of the walk, not a crash). Exit code 1 if any step failed.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '@playwright/test';

const PRESETS = {
    desktop: { width: 1280, height: 800 },
    mobile: { width: 375, height: 812 },
    tablet: { width: 768, height: 1024 },
};

const planPath = process.argv[2];
if (!planPath) {
    console.error('usage: node e2e/drive.mjs <plan.json>');
    process.exit(2);
}
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
const baseUrl = plan.baseUrl ?? 'http://localhost:5174';
const outDir = plan.outDir ?? 'shots';
fs.mkdirSync(outDir, { recursive: true });

const viewport =
    typeof plan.viewport === 'string' ? PRESETS[plan.viewport] : (plan.viewport ?? PRESETS.desktop);

const browser = await chromium.launch({
    channel: process.env.DORA_E2E_CHANNEL || 'chrome',
    headless: true,
});
const ctx = await browser.newContext({
    baseURL: baseUrl,
    viewport,
    colorScheme: plan.colorScheme ?? 'dark',
});
// `quasar dev` runs vue-tsc in watch mode via vite-plugin-checker; its
// full-screen error overlay (pre-existing type errors in e2e/src-pwa files)
// intercepts every pointer event in a fresh browser. Kill it on sight — this
// driver audits the app, not the typecheck.
await ctx.addInitScript(() => {
    const inject = () => {
        const style = document.createElement('style');
        style.textContent = 'vite-plugin-checker-error-overlay{display:none !important;pointer-events:none !important;}';
        (document.head || document.documentElement).appendChild(style);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', inject);
    else inject();
});
const page = await ctx.newPage();

async function ensureLoggedIn() {
    await page.goto(baseUrl);
    const user = page.locator('input[autocomplete="username"]');
    try {
        await user.waitFor({ state: 'visible', timeout: 4000 });
    } catch {
        return; // no login form → already authenticated or app landed elsewhere
    }
    await user.fill(plan.username ?? 'dora');
    await page.locator('input[autocomplete="current-password"]').fill(plan.password ?? 'dora');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL(/#\/(?!login)/, { timeout: 10_000 });
}

function target(step) {
    if (step.selector) return page.locator(step.selector);
    if (step.role) return page.getByRole(step.role, step.name ? { name: step.name } : {});
    if (step.text) return page.getByText(step.text, { exact: step.exact ?? false }).first();
    throw new Error('step needs selector, role, or text');
}

const results = [];
let failed = 0;
await ensureLoggedIn();

for (const [i, step] of (plan.steps ?? []).entries()) {
    const label = `${i}:${step.do}`;
    try {
        switch (step.do) {
            case 'goto': {
                const url = step.url.startsWith('http') ? step.url : baseUrl + '/' + step.url.replace(/^\//, '');
                await page.goto(url);
                await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
                break;
            }
            case 'click':
                await target(step).click({ timeout: step.timeout ?? 5000 });
                break;
            case 'fill':
                await target(step).fill(step.value ?? '', { timeout: step.timeout ?? 5000 });
                break;
            case 'press':
                await page.keyboard.press(step.key);
                break;
            case 'wait':
                await page.waitForTimeout(step.ms ?? 500);
                break;
            case 'waitFor':
                await target(step).waitFor({ state: step.state ?? 'visible', timeout: step.timeout ?? 8000 });
                break;
            case 'viewport':
                await page.setViewportSize(
                    step.preset ? PRESETS[step.preset] : { width: step.width, height: step.height },
                );
                break;
            case 'scheme':
                await page.emulateMedia({ colorScheme: step.value });
                break;
            case 'shot': {
                const file = path.join(outDir, `${step.name}.png`);
                await page.screenshot({ path: file, fullPage: step.fullPage ?? false });
                results.push({ step: label, shot: file });
                break;
            }
            case 'text': {
                const t = await (step.selector ? page.locator(step.selector) : page.locator('body')).innerText();
                results.push({ step: label, text: t.slice(0, step.max ?? 1500) });
                break;
            }
            case 'eval': {
                const value = await page.evaluate(step.js);
                results.push({ step: label, value });
                break;
            }
            default:
                throw new Error(`unknown step kind '${step.do}'`);
        }
        console.log(`ok   ${label}`);
    } catch (err) {
        failed += 1;
        const message = String(err).split('\n')[0];
        console.log(`FAIL ${label} — ${message}`);
        results.push({ step: label, error: message });
    }
}

console.log(JSON.stringify({ failed, results }, null, 2));
await browser.close();
process.exit(failed ? 1 : 0);
