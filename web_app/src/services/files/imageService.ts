/**
 * Helpers for wrangling base64-encoded images into something the browser can
 * render or POST to `dora_api` as a data-URL string.
 *
 * FU-014 — `dora_api/products` expects a `data:image/...;base64,...` string
 * on create (matching the stock-item / recipe convention), so
 * `wrapAsDataUrl` is the canonical encoder. Backed by a lightweight
 * magic-byte sniff so we stop defaulting every image to `image/jpeg`.
 */

/**
 * Sniff the MIME type from the first few base64 characters. Base64 of the
 * standard image magic-byte signatures has a fixed prefix per format.
 * Returns `image/jpeg` as a safe fallback.
 */
function sniffImageMimeFromBase64(base64: string): string {
    if (base64.startsWith('iVBORw0KGgo')) return 'image/png';
    if (base64.startsWith('/9j/')) return 'image/jpeg';
    if (base64.startsWith('UklGR')) return 'image/webp';
    if (base64.startsWith('R0lGOD')) return 'image/gif';
    return 'image/jpeg';
}

/**
 * Turn a raw base64 string (or an already-formed data URL) into a data URL
 * suitable for `<img src>` or POST to a `dora_api` image field.
 * Empty / null / undefined → empty string (caller decides what to render).
 */
export function wrapAsDataUrl(base64OrDataUrl: string | null | undefined): string {
    if (!base64OrDataUrl) return '';
    if (base64OrDataUrl.startsWith('data:')) return base64OrDataUrl;
    return `data:${sniffImageMimeFromBase64(base64OrDataUrl)};base64,${base64OrDataUrl}`;
}
