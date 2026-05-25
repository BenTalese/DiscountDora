import { Notify } from 'quasar';
import { boot } from 'quasar/wrappers';
import { clientLog } from 'src/composables/useClientLogger';
import { executeRollbacks } from 'src/services/errorHandling/rollbackRegistry';

// Boot ordering: this runs before route navigation, so any boot-time
// errors after this module loads will land in the backend stream too.
export default boot(({ app }) => {
    app.config.errorHandler = (err, vm, info) => {
        const message = err instanceof Error ? err.message : String(err);
        console.error('Vue Error:', err, vm, info);
        executeRollbacks();
        Notify.create({ type: 'oopsie' });
        // Ship to /api/client-logs so the server-side log stream sees the
        // crash too. Rate-limited and best-effort — never raises.
        clientLog.error(message, {
            origin: 'vue',
            vueInfo: info,
            stack: err instanceof Error ? err.stack : undefined,
        });
    };
});

window.onerror = function (msg, url, line, col, error) {
    console.error('Javascript Error:', msg, url, line, col, error);
    executeRollbacks();
    Notify.create({ type: 'oopsie' });
    clientLog.error(typeof msg === 'string' ? msg : 'window.onerror', {
        origin: 'window',
        url,
        line,
        col,
        stack: error instanceof Error ? error.stack : undefined,
    });
};

window.addEventListener('unhandledrejection', function (event) {
    executeRollbacks();
    Notify.create({ type: 'oopsie' });
    const reason = event.reason;
    const message =
        reason instanceof Error
            ? reason.message
            : typeof reason === 'string'
              ? reason
              : 'unhandled promise rejection';
    clientLog.error(message, {
        origin: 'promise',
        stack: reason instanceof Error ? reason.stack : undefined,
    });
});
