import { Notify } from 'quasar';
import { boot } from 'quasar/wrappers';

export default boot(({ app }) => {
    app.config.errorHandler = (err, vm, info) => {
        console.error('Unhandled Vue Error:', err, vm, info);
        Notify.create({ type: 'oopsie' });
    };
});

window.onerror = function (msg, url, line, col, error) {
    console.error('Unhandled Javascript Error:', msg, url, line, col, error);
    Notify.create({ type: 'oopsie' });
}

window.addEventListener('unhandledrejection', function (event) {
    Notify.create({ type: 'oopsie' });
});
