import { test, expect } from './fixtures';

// FU-571 pin — the bug class this spec exists for: the chunked-upload
// composable (and other raw-fetch callers) bypassed the axios CSRF
// interceptor, so every upload 403'd and spreadsheet Import + Backup
// restore were hard-broken in the browser for weeks while all 1,800+
// unit/component/API tests stayed green. Only a real browser driving the
// real SPA↔API handshake catches that seam.
//
// Also pins the SettingsFileDrop behaviour verified manually for FU-545
// (filename display, Remove-doesn't-reopen). Runs as the seeded admin.

const IMPORT_PAGE = '/#/settings/admin/data/import';
const CSV = {
    name: 'e2e-import.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('name,level\nE2E import probe,Stocked\n'),
};

test('picking a spreadsheet uploads + inspects with zero CSRF rejections (FU-571 pin)', async ({ page }) => {
    const csrfRejections: string[] = [];
    page.on('response', (r) => {
        if (r.status() === 403) {
            csrfRejections.push(`${r.request().method()} ${r.url()}`);
        }
    });

    await page.goto(IMPORT_PAGE);

    // Picking a file auto-runs the whole pipeline: chunked upload
    // (start/chunk/finish) then the inspect POST whose 200 proves the
    // server accepted every mutating call.
    const inspected = page.waitForResponse(
        (r) => r.url().includes('/api/data/import/spreadsheet/inspect') && r.status() === 200,
    );
    await page.locator('input[type="file"]').setInputFiles(CSV);
    await inspected;

    // FU-545 L76 — the drop zone holds the steady filled state (before the
    // FU-571 fix the 403 wiped it straight back to idle).
    await expect(page.getByText(CSV.name)).toBeVisible();

    expect(csrfRejections, 'no upload call may be CSRF-rejected').toEqual([]);
});

test('Remove clears the picked file without reopening the picker (FU-545 L79 pin)', async ({ page }) => {
    await page.goto(IMPORT_PAGE);
    await page.locator('input[type="file"]').setInputFiles(CSV);
    await expect(page.getByText(CSV.name)).toBeVisible();

    // The historical bug shape (FU-531): the label forwarded the Remove
    // click into the hidden input and popped the OS file dialog again.
    let pickerOpened = 0;
    page.on('filechooser', () => { pickerOpened += 1; });

    await page.getByRole('button', { name: 'Remove file' }).click();

    // Back to the idle prompt; the picked file is gone; no dialog opened.
    await expect(page.getByText(/choose a spreadsheet/i)).toBeVisible();
    await expect(page.getByText(CSV.name)).toHaveCount(0);
    expect(pickerOpened, 'Remove must not reopen the file picker').toBe(0);
});
