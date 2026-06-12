/**
 * Helpers for wrangling base64-encoded images shipped by `merchant_api`
 * (raw base64 string, no data-URL prefix) into something the browser can
 * render or POST to `dora_api` as a data-URL string.
 *
 * FU-014 — `dora_api/products` now expects a `data:image/...;base64,...`
 * string on create (matching the stock-item / recipe convention), so
 * `wrapAsDataUrl` is the canonical encoder used by both display (offer
 * cards) and save paths. Backed by a lightweight magic-byte sniff so we
 * stop defaulting every image to `image/jpeg` blindly.
 */

/**
 * Sniff the MIME type from the first few base64 characters. Base64 of the
 * standard image magic-byte signatures has a fixed prefix per format.
 * Returns `image/jpeg` as a safe fallback — most merchant offers are JPEG.
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

export default class ImageService {
    /**
     * @deprecated Use `wrapAsDataUrl` directly. Kept for the one consumer
     * still calling it (ProductSearchCard) until its imports flip.
     */
    decodeBase64Image = (encodedImage: string): string => wrapAsDataUrl(encodedImage);
}
