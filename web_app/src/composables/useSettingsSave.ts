import { useQuasar } from 'quasar';
import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
import { ref } from 'vue';

/**
 * R-003 — single source for the save-a-setting toast pattern shared by every
 * settings page (Assistant / Preferences / Nutrition / Money / Notifications /
 * Voice). Each page used to inline an identical `saving` ref + `notifySuccess`
 * + `notifyError` + `update()` helper.
 *
 * FU-601: the old `update()` reused the *success* sentence as the error noun —
 * `notifyError(\`Could not save ${label.toLowerCase()}.\`)` — so a save failure
 * rendered a broken string ("Could not save ai mode turned on.."). The error
 * path now shows one fixed, grammatical message; the specific failure detail
 * already rides in the toast caption via `toastCaption(err)`.
 */
export function useSettingsSave() {
    const $q = useQuasar();
    const saving = ref(false);

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }

    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: toastCaption(err),
        });
    }

    /**
     * Run a save, toasting the success sentence on success and a fixed,
     * grammatical error otherwise. Returns the run's result, or `null` if it
     * threw (the caller has already been told via the toast).
     *
     * `successMessage` is a user-facing sentence ("AI mode turned on."); it is
     * NOT reused in the error path (that was the FU-601 bug).
     */
    async function update<T>(
        successMessage: string,
        run: () => Promise<T>,
    ): Promise<T | null> {
        saving.value = true;
        try {
            const result = await run();
            notifySuccess(successMessage);
            return result;
        } catch (err) {
            notifyError('Could not save your change.', err);
            return null;
        } finally {
            saving.value = false;
        }
    }

    return { saving, notifySuccess, notifyError, update };
}
