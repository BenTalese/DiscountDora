/**
 * Stage a file to /api/data/uploads/* in 8 MB chunks with per-chunk retry.
 * Returns the upload_id and exposes a reactive progress (0..1) so callers
 * can render a progress bar without wiring their own state.
 *
 * Used by both BackupRestore and DataImport — both flows upload once and
 * then reference the staged file via upload_id in subsequent inspect /
 * commit calls.
 */
import { ref } from 'vue';
// FU-571: these calls bypass axios (hand-rolled fetch for chunk streaming),
// so the interceptor that normally attaches the double-submit CSRF header
// never runs — without csrfHeader() every upload 403s.
import { csrfHeader, resolveBaseURL } from 'src/services/api/axiosHttpClient';

// Defaults match the server-side constants in
// dora_api/features/data/uploads.py — overrideable per-call.
const DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024;
const DEFAULT_MAX_ATTEMPTS = 3;

export interface ChunkedUploadOptions {
    chunkSize?: number;
    maxAttempts?: number;
}

export function useChunkedUpload() {
    // 0..1 inclusive. Stays at 0 until the first chunk lands.
    const progress = ref(0);
    const inFlight = ref(false);
    const lastUploadId = ref<string | null>(null);

    async function upload(file: File, options: ChunkedUploadOptions = {}): Promise<string> {
        const baseUrl = resolveBaseURL();
        const chunkSize = options.chunkSize ?? DEFAULT_CHUNK_BYTES;
        const maxAttempts = options.maxAttempts ?? DEFAULT_MAX_ATTEMPTS;

        progress.value = 0;
        inFlight.value = true;
        try {
            const startResponse = await fetch(`${baseUrl}/data/uploads/start`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json', ...csrfHeader() },
                body: JSON.stringify({ expected_size: file.size }),
            });
            if (!startResponse.ok) {
                throw new Error(await describeError(startResponse));
            }
            const startBody = await startResponse.json() as {
                upload_id: string;
                chunk_size: number;
            };
            lastUploadId.value = startBody.upload_id;
            // The server can dictate a larger chunk size than the caller
            // suggested; honour whichever is larger to avoid extra round-trips.
            const effectiveChunkSize = Math.max(startBody.chunk_size, chunkSize);

            for (let offset = 0; offset < file.size; offset += effectiveChunkSize) {
                const end = Math.min(offset + effectiveChunkSize, file.size);
                const slice = file.slice(offset, end);
                await uploadChunkWithRetry(
                    baseUrl, startBody.upload_id, offset, slice, maxAttempts,
                );
                progress.value = end / file.size;
            }

            const finishResponse = await fetch(`${baseUrl}/data/uploads/finish`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json', ...csrfHeader() },
                body: JSON.stringify({ upload_id: startBody.upload_id }),
            });
            if (!finishResponse.ok) {
                throw new Error(await describeError(finishResponse));
            }
            return startBody.upload_id;
        } finally {
            inFlight.value = false;
        }
    }

    /** Best-effort abort. Safe to call with a stale id (the server returns
     *  204 either way). */
    async function abort(uploadId: string | null): Promise<void> {
        if (!uploadId) return;
        try {
            const baseUrl = resolveBaseURL();
            await fetch(
                `${baseUrl}/data/uploads/${encodeURIComponent(uploadId)}`,
                { method: 'DELETE', credentials: 'include', headers: csrfHeader() },
            );
        } catch {
            // Ignored — TTL sweep will catch it eventually.
        }
    }

    function reset() {
        progress.value = 0;
        lastUploadId.value = null;
    }

    return { progress, inFlight, lastUploadId, upload, abort, reset };
}

async function uploadChunkWithRetry(
    baseUrl: string,
    id: string,
    offset: number,
    chunk: Blob,
    maxAttempts: number,
): Promise<void> {
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        try {
            const form = new FormData();
            form.append('upload_id', id);
            form.append('offset', String(offset));
            form.append('chunk', chunk);
            const response = await fetch(`${baseUrl}/data/uploads/chunk`, {
                method: 'POST',
                credentials: 'include',
                headers: csrfHeader(),
                body: form,
            });
            if (response.ok) return;
            const body = await response.json().catch(() => null);
            const received = body?.errors?.received?.[0];
            if (response.status === 400 && received !== undefined) {
                throw new Error(
                    `Chunk offset mismatch (server has ${received} bytes). Retry the upload.`,
                );
            }
            throw new Error(body?.detail ?? body?.title ?? `HTTP ${response.status}`);
        } catch (err) {
            if (attempt >= maxAttempts) throw err;
            await new Promise((resolve) => setTimeout(resolve, 250 * attempt));
        }
    }
}

async function describeError(response: Response): Promise<string> {
    const body = await response.json().catch(() => null);
    return body?.detail ?? body?.title ?? `HTTP ${response.status}`;
}
