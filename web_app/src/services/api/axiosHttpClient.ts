import type { Axios, AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import axios from 'axios';
import { Notify } from 'quasar';

class ApiErrorResponse extends Error {
    detail!: string;
    status!: number;
    errors!: Map<string, string>;
    title!: string;
    type!: string;
}

// Normalised error shape every caller sees, regardless of backend response
// shape. Carriers a correlationId so logs/bug-reports can be matched back to
// the request line on the server side.
export class NormalisedApiError extends Error {
    status: number;
    code: string;
    details: Record<string, unknown> | null;
    correlationId: string;
    isNetworkError: boolean;
    method: string;
    url: string;

    constructor(args: {
        status: number;
        code: string;
        message: string;
        details: Record<string, unknown> | null;
        correlationId: string;
        isNetworkError: boolean;
        method: string;
        url: string;
    }) {
        super(args.message);
        this.name = 'NormalisedApiError';
        this.status = args.status;
        this.code = args.code;
        this.details = args.details;
        this.correlationId = args.correlationId;
        this.isNetworkError = args.isNetworkError;
        this.method = args.method;
        this.url = args.url;
    }
}

// Optional callback the auth store registers to react to expired sessions
// (clear user state, redirect to /login). The setter avoids a Pinia circular
// import that would happen if this module imported the store directly.
type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
    unauthorizedHandler = handler;
}

// Endpoints where a 401 is an expected outcome (anonymous boot probe / explicit
// login attempt), so we must NOT trigger the global session-expired handler.
const SUPPRESS_401_PATHS = ['/auth/me', '/auth/login', '/auth/register'];

// Endpoints whose failures are surfaced in-page rather than via toast — the
// boot probe is owned by SplashScreen, so a noisy "server tripped" notify on
// cold-load would race with the splash and look broken.
const SUPPRESS_NOTIFY_PATHS = ['/auth/me'];

function shouldSuppress401(url: string | undefined): boolean {
    if (!url) return false;
    return SUPPRESS_401_PATHS.some((p) => url.endsWith(p));
}

function shouldSuppressNotify(url: string | undefined): boolean {
    if (!url) return false;
    return SUPPRESS_NOTIFY_PATHS.some((p) => url.endsWith(p));
}

// The API may return either a bare { id } envelope or the full created
// resource as the body. Callers can narrow on entity-specific id fields.
export type CreatedResponse = { id?: string } & Record<string, unknown>;

export type HttpClientResponse<TResponse> = TResponse;

export interface HttpClient {
    get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>;
    post<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    patch<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>;
}

export function resolveBaseURL(): string {
    const envValue = import.meta.env.VITE_API_BASE_URL;
    if (envValue && envValue.length > 0) return envValue.replace(/\/+$/, '');
    if (typeof window !== 'undefined' && window.location) {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:5170/api`;
    }
    return 'http://localhost:5170/api';
}

// ─── Correlation id ──────────────────────────────────────────────────
// Lightweight UUIDv4 generator. We can't rely on `crypto.randomUUID` in
// every target browser (Chrome ≥92, but still); fall back if missing.
function newCorrelationId(): string {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        return (crypto as Crypto & { randomUUID: () => string }).randomUUID();
    }
    // RFC4122 v4 fallback. Not cryptographically strong, but fine for an
    // id whose only job is to match log lines.
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

// ─── Retry policy ────────────────────────────────────────────────────
// Spec: GET only, max 3 attempts, exponential backoff on network errors
// and 502/503/504. Never retry POST/PUT/PATCH/DELETE (those are
// the offline queue's job — see useOfflineQueue).
const RETRYABLE_STATUSES = new Set([502, 503, 504]);
const MAX_RETRIES = 3;

function isRetryable(method: string | undefined, error: AxiosError): boolean {
    const m = (method ?? 'get').toLowerCase();
    if (m !== 'get') return false;
    if (!error.response) return true; // network error / no response
    return RETRYABLE_STATUSES.has(error.response.status);
}

function backoffDelay(attempt: number): number {
    // 1: 200ms, 2: 400ms, 3: 800ms + small jitter
    const base = 200 * 2 ** (attempt - 1);
    const jitter = Math.random() * 100;
    return base + jitter;
}

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// Augment axios's request config with our retry / correlation-id state
// so the interceptors can pass it across attempts.
type DoraRequestConfig = InternalAxiosRequestConfig & {
    __retryCount?: number;
    __correlationId?: string;
};

export default class AxiosHttpClient implements HttpClient {
    private axios: Axios;

    constructor() {
        this.axios = axios.create({
            baseURL: resolveBaseURL(),
            headers: { 'Content-Type': 'application/json' },
            // withCredentials lets the browser send/receive the dora_session
            // cookie on cross-origin requests (dev: 5174 → 5170).
            withCredentials: true
        });

        // ── Request interceptor: correlation id ─────────────────────
        this.axios.interceptors.request.use((config) => {
            const cfg = config as DoraRequestConfig;
            if (!cfg.__correlationId) cfg.__correlationId = newCorrelationId();
            cfg.headers.set?.('X-Request-Id', cfg.__correlationId);
            return cfg;
        });

        // ── Response interceptor: 401 + retry + normalisation ──────
        this.axios.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                const cfg = (error.config ?? {}) as DoraRequestConfig;

                // 401 — session expired (or never authed). Route to login.
                if (error.response?.status === 401 && !shouldSuppress401(cfg.url)) {
                    unauthorizedHandler?.();
                    return Promise.reject(error);
                }

                // Retry GETs on network errors and 5xx-class transient codes.
                if (isRetryable(cfg.method, error)) {
                    const attempt = (cfg.__retryCount ?? 0) + 1;
                    if (attempt <= MAX_RETRIES) {
                        cfg.__retryCount = attempt;
                        await sleep(backoffDelay(attempt));
                        return this.axios.request(cfg);
                    }
                }

                return Promise.reject(error);
            }
        );
    }

    async delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.delete<TResponse>(path)).data;
        } catch (error) {
            return this.handleError(error as AxiosError, 'DELETE', path);
        }
    }

    async get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.get<TResponse>(path)).data;
        } catch (error) {
            return this.handleError(error as AxiosError, 'GET', path);
        }
    }

    /** Map any axios error into a NormalisedApiError, surface 5xx via notify. */
    private handleError(error: AxiosError, method: string, path: string): Promise<never> {
        const cfg = (error.config ?? {}) as DoraRequestConfig;
        const correlationId = cfg.__correlationId ?? '';
        const status = error.response?.status ?? 0;
        const isNetworkError = !error.response;
        const errorData = error.response?.data;

        let code = 'unknown_error';
        let message = error.message || 'Request failed';
        let details: Record<string, unknown> | null = null;

        if (this.isCustomApiErrorResponse(errorData)) {
            const apiError = errorData;
            code = apiError.type || `http_${status}`;
            message =
                apiError.detail ||
                apiError.title ||
                Object.values(apiError.errors ?? {}).join(', ') ||
                message;
            details = {
                title: apiError.title,
                errors: apiError.errors,
                type: apiError.type,
            };
        } else if (isNetworkError) {
            code = 'network_error';
            message = 'Network request failed';
        } else {
            code = `http_${status}`;
        }

        // 5xx → noisy toast so the user knows the server tripped.
        // 4xx is the caller's responsibility to phrase — it might be a
        // benign 404 from a search, etc.
        if (status >= 500 && !shouldSuppressNotify(path)) {
            try {
                Notify.create({
                    type: 'negative',
                    position: 'top',
                    message: 'Something on the server tripped. We logged the error.',
                    ...(correlationId
                        ? { caption: `Ref: ${correlationId.slice(0, 8)}` }
                        : {}),
                    timeout: 5000,
                });
                 
                console.warn(
                    `[api] ${method} ${path} → ${status} ${code} (${correlationId})`,
                    details,
                );
            } catch {
                // Notify isn't available during boot — ignore.
            }
        }

        return Promise.reject(
            new NormalisedApiError({
                status,
                code,
                message,
                details,
                correlationId,
                isNetworkError,
                method,
                url: path,
            }),
        );
    }

    isCustomApiErrorResponse = (error: unknown): error is ApiErrorResponse =>
        error !== null &&
        typeof error === 'object' &&
        'detail' in error &&
        'status' in error &&
        'errors' in error &&
        'title' in error &&
        'type' in error;

    async patch<TResponse = unknown, TBody = unknown>(
        path: string,
        body: TBody
    ): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.patch<TResponse>(path, body)).data;
        } catch (error) {
            return this.handleError(error as AxiosError, 'PATCH', path);
        }
    }

    async post<TResponse = unknown, TBody = unknown>(
        path: string,
        body: TBody
    ): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.post<TResponse>(path, body)).data;
        } catch (error) {
            return this.handleError(error as AxiosError, 'POST', path);
        }
    }

    async put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.put<TResponse>(path, body)).data;
        } catch (error) {
            return this.handleError(error as AxiosError, 'PUT', path);
        }
    }

    /** Raw config-bearing call used by the offline queue when draining: we need
     *  to replay a stored request exactly as it was, without rewrapping. */
    async request<TResponse = unknown>(config: AxiosRequestConfig): Promise<TResponse> {
        try {
            return (await this.axios.request<TResponse>(config)).data;
        } catch (error) {
            return this.handleError(
                error as AxiosError,
                (config.method ?? 'GET').toUpperCase(),
                config.url ?? '',
            );
        }
    }
}
