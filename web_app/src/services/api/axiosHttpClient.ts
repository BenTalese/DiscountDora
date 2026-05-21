import type { Axios, AxiosError } from 'axios';
import axios from 'axios';

class ApiErrorResponse extends Error {
    detail!: string;
    status!: number;
    errors!: Map<string, string>;
    title!: string;
    type!: string;
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

function shouldSuppress401(url: string | undefined): boolean {
    if (!url) return false;
    return SUPPRESS_401_PATHS.some((p) => url.endsWith(p));
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

/** Which backend the client targets. Lets callers pick the right env var +
 *  dev port fallback without knowing URLs. */
export type ApiBackend = 'dora' | 'merchant';

function resolveBaseURL(backend: ApiBackend): string {
    const envValue =
        backend === 'merchant'
            ? import.meta.env.VITE_MERCHANT_API_BASE_URL
            : import.meta.env.VITE_API_BASE_URL;
    if (envValue && envValue.length > 0) return envValue.replace(/\/+$/, '');

    const port = backend === 'merchant' ? 5172 : 5170;
    if (typeof window !== 'undefined' && window.location) {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:${port}/api`;
    }
    return `http://localhost:${port}/api`;
}

export default class AxiosHttpClient implements HttpClient {
    private axios: Axios;

    /**
     * @param backend Which API to hit; defaults to the main Dora API.
     *   Pass `'merchant'` for the standalone merchant_api on port 5172.
     */
    constructor(backend: ApiBackend = 'dora') {
        this.axios = axios.create({
            baseURL: resolveBaseURL(backend),
            headers: { 'Content-Type': 'application/json' },
            // withCredentials lets the browser send/receive the dora_session
            // cookie on cross-origin requests (dev: 5174 → 5170). The merchant
            // API doesn't currently use cookies, but enabling this on its
            // client is harmless — the browser only sends a cookie that
            // originated at that origin.
            withCredentials: true
        });

        this.axios.interceptors.response.use(
            (response) => response,
            (error: AxiosError) => {
                if (error.response?.status === 401 && !shouldSuppress401(error.config?.url)) {
                    unauthorizedHandler?.();
                }
                return Promise.reject(error);
            }
        );
    }

    async delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.delete<TResponse>(path)).data;
        } catch (error) {
            return this.handleError(error as AxiosError);
        }
    }

    async get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.get<TResponse>(path)).data;
        } catch (error) {
            return this.handleError(error as AxiosError);
        }
    }

    private handleError(error: AxiosError): Promise<never> {
        const errorData = error.response?.data;
        if (this.isCustomApiErrorResponse(errorData)) {
            const apiError = errorData;
            return Promise.reject(
                new Error(
                    `API ERROR :: STATUS CODE ${apiError.status} :: ${apiError.title} :: ${apiError.detail} :: ${Object.values(apiError.errors).join(', ')}`
                )
            );
        } else {
            return Promise.reject(new Error(`API ERROR :: ${error.name} :: ${error.message} :: ${error.config?.url}`));
        }
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
            return this.handleError(error as AxiosError);
        }
    }

    async post<TResponse = unknown, TBody = unknown>(
        path: string,
        body: TBody
    ): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.post<TResponse>(path, body)).data;
        } catch (error) {
            return this.handleError(error as AxiosError);
        }
    }

    async put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.put<TResponse>(path, body)).data;
        } catch (error) {
            return this.handleError(error as AxiosError);
        }
    }
}
