/**
 * Helpers for wrangling base64-encoded images into something the browser can
 * render or POST to `dora_api` as a data-URL string.
 *
 * FU-014 — `dora_api/products` expects a `data:image/...;base64,...` string
 * on create (matching the stock-item / recipe convention), so
 * `wrapAsDataUrl` is the canonical encoder. Backed by a lightweight
 * magic-byte sniff so we stop defaulting every image to `image/jpeg`.
 *
 * PROPOSAL_RECIPE_IMAGE_STEPS — `processImageFile` is the single client-side
 * resize + re-encode + MIME-validation pipeline used by every upload site
 * (user avatar, recipe hero, stock item, store, step images). Centralised
 * so resize targets / quality / MIME allow-list don't drift per surface.
 *
 * FU-345 — the resize dimensions + JPEG quality are install-wide
 * settings (`AppSetting.image_max_dimension` + `AppSetting.image_quality`)
 * exposed via `/health.image_policy`. `processImageFile` reads them via
 * `currentImagePolicy()` on every call — no per-surface knobs to keep
 * in sync. Callers may still override for narrow cases (e.g. avatars),
 * but the default path just uses the admin's chosen policy.
 */

import { currentImagePolicy } from 'src/composables/useImagePolicy';

/** MIME types we accept for upload across the app. */
export const ALLOWED_UPLOAD_MIME_TYPES = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
] as const;

export type ProcessImageOptions = {
    /** Long-edge cap in px. Larger images are scaled down preserving aspect
     *  ratio; smaller images are passed through (we don't upscale). */
    maxLongEdge?: number;
    /** JPEG quality 0–1 used when re-encoding. Ignored when the source is
     *  already a PNG-with-transparency we want to preserve — for now we
     *  always re-encode to JPEG since recipe / avatar uploads don't need
     *  alpha. */
    quality?: number;
    /** Raw byte cap on the *input file* (pre-resize). Defaults to 12MB —
     *  comfortably above what phones produce; rejects pathological uploads
     *  without forcing a roundtrip through canvas. */
    maxInputBytes?: number;
};

export type ProcessedImage = {
    /** `data:image/jpeg;base64,...` ready to POST to dora_api or set as
     *  an <img> src. */
    dataUrl: string;
    /** Final encoded MIME type (always 'image/jpeg' today; the field exists
     *  so callers don't bake the assumption in). */
    mimeType: string;
    /** Decoded dimensions after the resize. */
    width: number;
    height: number;
};

// Input byte cap is a hard limit on the picker (not policy-driven);
// resize + quality default to whatever the install's current policy
// resolves to. `currentImagePolicy()` returns the loaded values (or
// conservative defaults if the health probe hasn't landed yet).
const INPUT_BYTE_CAP_DEFAULT = 12 * 1024 * 1024;

/**
 * Resize + re-encode + validate a user-picked image file. Single shared
 * helper for every upload site so the resize/quality/MIME story stays
 * consistent. Rejects unsupported MIMEs and oversize inputs with a
 * thrown Error whose message is safe to show the user.
 */
export async function processImageFile(
    file: File,
    options: ProcessImageOptions = {},
): Promise<ProcessedImage> {
    // FU-345 — read the install policy on every call. `options` still
    // wins so a narrow surface (e.g. a tight avatar) can override; the
    // vast majority of callers omit options entirely and get the
    // admin-chosen defaults automatically.
    const policy = currentImagePolicy();
    const opts: Required<ProcessImageOptions> = {
        maxLongEdge: options.maxLongEdge ?? policy.maxLongEdge,
        quality: options.quality ?? policy.quality,
        maxInputBytes: options.maxInputBytes ?? INPUT_BYTE_CAP_DEFAULT,
    };

    if (!(ALLOWED_UPLOAD_MIME_TYPES as readonly string[]).includes(file.type)) {
        throw new Error(
            `Unsupported image type "${file.type || 'unknown'}". ` +
            `Try a JPEG, PNG, or WebP.`,
        );
    }
    if (file.size > opts.maxInputBytes) {
        const megabytes = Math.round(opts.maxInputBytes / (1024 * 1024));
        throw new Error(`Image is too large (max ${megabytes}MB). Pick a smaller one.`);
    }

    const bitmap = await loadAsBitmap(file);
    const { width, height } = scaleToFit(bitmap.width, bitmap.height, opts.maxLongEdge);

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        bitmap.close?.();
        throw new Error('Could not process that image (canvas unavailable).');
    }
    ctx.drawImage(bitmap, 0, 0, width, height);
    bitmap.close?.();

    const dataUrl = canvas.toDataURL('image/jpeg', opts.quality);
    return { dataUrl, mimeType: 'image/jpeg', width, height };
}

async function loadAsBitmap(file: File): Promise<ImageBitmap> {
    // `createImageBitmap` is supported in every browser Dora targets and
    // handles EXIF orientation correctly when given `imageOrientation:
    // 'from-image'` — important so a portrait phone photo doesn't end up
    // sideways after canvas re-encode.
    try {
        return await createImageBitmap(file, { imageOrientation: 'from-image' });
    }
    catch {
        // Some older Safari builds reject the options bag — fall back to
        // the no-options form rather than failing the whole pick.
        return await createImageBitmap(file);
    }
}

function scaleToFit(
    width: number,
    height: number,
    maxLongEdge: number,
): { width: number; height: number } {
    const longest = Math.max(width, height);
    if (longest <= maxLongEdge) return { width, height };
    const ratio = maxLongEdge / longest;
    return {
        width: Math.round(width * ratio),
        height: Math.round(height * ratio),
    };
}

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
