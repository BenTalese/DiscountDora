/**
 * Shared helpers for "fetch a file from the API and save it via the
 * browser". Used by every in-context export composable + the backup
 * download. Centralised so the Content-Disposition regex and the
 * <a download> trick live in one place.
 */

/** Pull a filename out of a Content-Disposition header. Returns null
 *  when the header is missing or doesn't carry a filename. */
export function parseFilename(header: string | null): string | null {
    if (!header) return null;
    const match = /filename="?([^";]+)"?/i.exec(header);
    return match ? match[1]! : null;
}

/** Trigger a browser download of a blob. Cleans up the object URL
 *  after the click so we don't leak memory across many exports. */
export function triggerSave(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
}
