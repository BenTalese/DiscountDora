import { NormalisedApiError } from 'src/services/api/axiosHttpClient';

export type ExtractedErrors = {
    fieldErrors: Record<string, string>;
    generalError: string | null;
};

const EMPTY: ExtractedErrors = { fieldErrors: {}, generalError: null };

// Backend RFC7807-ish payloads carry `{ errors: { fieldName: [msg, ...] } }`.
// Anything with an empty/sentinel key is treated as a form-level message.
const GENERAL_KEYS = new Set(['', '_', 'noKey', 'general']);

export function extractFieldErrors(err: unknown): ExtractedErrors {
    if (!(err instanceof NormalisedApiError)) {
        return {
            fieldErrors: {},
            generalError: 'Something went wrong. Please try again.',
        };
    }

    // 5xx already triggers a global Notify in the http client — leave the
    // form's general slot blank so users aren't told twice.
    if (err.status >= 500) return EMPTY;

    if (err.isNetworkError) {
        return {
            fieldErrors: {},
            generalError: "Can't reach the server. Check your connection and try again.",
        };
    }

    const serverErrors = (err.details?.errors ?? {}) as Record<string, string[] | string>;
    const fieldErrors: Record<string, string> = {};
    const generalParts: string[] = [];

    for (const [key, value] of Object.entries(serverErrors)) {
        const text = Array.isArray(value) ? value.join(' ') : String(value);
        if (!text) continue;
        if (GENERAL_KEYS.has(key)) {
            generalParts.push(text);
        } else {
            fieldErrors[key] = text;
        }
    }

    let generalError: string | null = generalParts.join(' ') || null;
    // 4xx with no errors map at all → fall back to the http-level message so
    // the user gets *something* rather than silent failure.
    if (!generalError && Object.keys(fieldErrors).length === 0) {
        generalError = err.message || 'Request failed.';
    }

    return { fieldErrors, generalError };
}

// One-shot helper for places that just want a user-readable string — eg.
// `caption` on a notify. Returns empty string if nothing useful is available
// so callers can fall back to their own copy.
export function describeApiError(err: unknown): string {
    const extracted = extractFieldErrors(err);
    const fields = Object.values(extracted.fieldErrors).filter(Boolean).join(' ');
    return fields || extracted.generalError || '';
}
