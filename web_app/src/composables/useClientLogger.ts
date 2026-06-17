/**
 * Tiny SPA-side logger. Mirrors the standard log levels and ships
 * `warn` + `error` to the backend so client crashes land in the same
 * log stream as server errors. `debug` and `info` stay in DevTools.
 *
 * Client-side rate limit (max 10 sent / 60 s) shadows the server's
 * limit so a broken page doesn't generate a thundering herd of POSTs
 * while we're already in trouble.
 *
 * `install()` (called from boot) wires global error handlers:
 *   - window.onerror  → uncaught synchronous errors.
 *   - unhandledrejection → uncaught promise rejections.
 *   - app.config.errorHandler → Vue render / setup errors.
 */
import type { App } from 'vue';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';

type Level = 'debug' | 'info' | 'warn' | 'error';

const WINDOW_MS = 60_000;
const MAX_SENDS = 10;
const sendTimes: number[] = [];

function allowSend(): boolean {
    const now = Date.now();
    // Drop stale timestamps so the array stays small.
    while (sendTimes.length && sendTimes[0]! < now - WINDOW_MS) {
        sendTimes.shift();
    }
    if (sendTimes.length >= MAX_SENDS) return false;
    sendTimes.push(now);
    return true;
}

function buildContext(extra?: Record<string, unknown>): Record<string, unknown> {
    return {
        url: typeof window !== 'undefined' ? window.location.href : null,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : null,
        ...(extra ?? {}),
    };
}

async function ship(level: Level, message: string, context?: Record<string, unknown>): Promise<void> {
    if (level !== 'warn' && level !== 'error') return;
    if (!allowSend()) return;
    try {
        const baseUrl = resolveBaseURL();
        // Plain fetch (not the shared http client) to avoid re-entering
        // the axios interceptor if the failure originated there.
        await fetch(`${baseUrl}/client-logs`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level,
                message: message.slice(0, 2048),
                context: buildContext(context),
            }),
            // Best-effort: don't await long if the network's down.
            keepalive: true,
        });
    } catch {
        // Ignored — logging failures must never break the page.
    }
}

export const clientLog = {
    debug(message: string, context?: Record<string, unknown>) {
         
        console.debug('[dora]', message, context ?? '');
    },
    info(message: string, context?: Record<string, unknown>) {
         
        console.info('[dora]', message, context ?? '');
    },
    warn(message: string, context?: Record<string, unknown>) {
         
        console.warn('[dora]', message, context ?? '');
        void ship('warn', message, context);
    },
    error(message: string, context?: Record<string, unknown>) {
         
        console.error('[dora]', message, context ?? '');
        void ship('error', message, context);
    },
};

export function useClientLogger() {
    return clientLog;
}

/**
 * Register global error handlers so SPA crashes / unhandled rejections
 * also land in the backend log stream. Called once from boot.
 */
export function installGlobalErrorReporting(app: App): void {
    if (typeof window !== 'undefined') {
        window.addEventListener('error', (event) => {
            clientLog.error(event.message || 'window.onerror', {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack,
            });
        });
        window.addEventListener('unhandledrejection', (event) => {
            const reason = event.reason;
            const message =
                reason instanceof Error
                    ? reason.message
                    : typeof reason === 'string'
                    ? reason
                    : 'unhandled promise rejection';
            clientLog.error(message, {
                stack: reason instanceof Error ? reason.stack : undefined,
            });
        });
    }
    app.config.errorHandler = (err, _instance, info) => {
        const message = err instanceof Error ? err.message : String(err);
        clientLog.error(message, {
            vueInfo: info,
            stack: err instanceof Error ? err.stack : undefined,
        });
    };
}
