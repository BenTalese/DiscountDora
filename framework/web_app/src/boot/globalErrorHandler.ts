import { Notify } from 'quasar';
import { boot } from 'quasar/wrappers';

export default boot(({ app }) => {
    app.config.errorHandler = (err, vm, info) => {
        console.error('Unhandled Vue Error:', err, vm, info);
        Notify.create({});
    };

    window.onerror = function (msg, url, line, col, error) {
        console.error('Unhandled Javascript Error:', msg, url, line, col, error);
        Notify.create({});
    }

    window.addEventListener('unhandledrejection', function (event) {
        console.error('Unhandled Promise Rejection:', event.reason);
        Notify.create({});
    });
});
