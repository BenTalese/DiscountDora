import { ref } from 'vue';
import { useQuasar } from 'quasar';
import type { Alert, AlertAction } from 'src/models/alert';
import AlertApiService from 'src/services/api/alertApiService';
import { useAlertStore } from 'src/stores/alertStore';
import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

const api = new AlertApiService();

/**
 * The one place the "user taps an inline alert action" mutation lives: the
 * applyAction API call + refresh + success/error toast + per-row busy state.
 * Every alert surface (bell peek, /alerts hub, dashboard card) composes this so
 * the toast + error handling can't drift apart again (FU-521 / R-003) — the bug
 * that motivated it was the dashboard silently swallowing both toasts while the
 * bell + hub toasted "Done.".
 *
 * `refresh` defaults to the shared alert store; a surface with extra derived
 * state (the dashboard also reloads its summary/score) passes its own.
 *
 * Call from a component `setup`. Bind `busyAlertId` for per-row spinners.
 */
export function useAlertActions() {
    const $q = useQuasar();
    const alertStore = useAlertStore();

    const busyAlertId = ref<string | null>(null);

    async function applyAction(
        alert: Alert,
        action: AlertAction,
        opts?: { refresh?: () => Promise<void> },
    ): Promise<boolean> {
        busyAlertId.value = alert.alert_id;
        try {
            await api.applyActionAsync(alert.alert_id, action);
            await (opts?.refresh ? opts.refresh() : alertStore.refreshAsync());
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Done.' });
            return true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not apply.',
                caption: toastCaption(err),
            });
            return false;
        } finally {
            busyAlertId.value = null;
        }
    }

    return { busyAlertId, applyAction };
}
