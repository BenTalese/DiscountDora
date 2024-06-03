import { Notify } from 'quasar';
import { boot } from 'quasar/wrappers';
import { executeRollbacks } from 'src/services/errorHandling/rollbackRegistry';

export default boot(({ app }) => {
    app.config.errorHandler = (err, vm, info) => {
        console.error('Vue Error:', err, vm, info);
        executeRollbacks();
        Notify.create({ type: 'oopsie' });
    };
});

window.onerror = function (msg, url, line, col, error) {
    console.error('Javascript Error:', msg, url, line, col, error);
    executeRollbacks();
    Notify.create({ type: 'oopsie' });
}

window.addEventListener('unhandledrejection', function (event) {
    executeRollbacks();
    Notify.create({ type: 'oopsie' });
});
