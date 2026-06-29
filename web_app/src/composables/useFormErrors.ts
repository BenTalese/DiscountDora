import { ref } from 'vue';
import type { Ref } from 'vue';

import {
    correlationSuffix,
    extractFieldErrors,
} from 'src/services/errorHandling/apiErrorHandler';

/**
 * FU-099 — the standard catch-block plumbing for a save-button form.
 *
 * Centralises the five lines every editor dialog hand-rolled (binding
 * field-keyed server errors to per-input `error-message` slots, plus a
 * general slot for non-field errors). Forms wire it once:
 *
 *     const { fieldErrors, generalError, handleSaveError, reset } = useFormErrors();
 *
 *     async function onSave() {
 *         reset();
 *         try { await api.saveAsync(...); }
 *         catch (err) {
 *             handleSaveError(err, 'Could not save the recipe.');
 *         }
 *     }
 *
 *     // template:
 *     <q-input :error="!!fieldErrors.name" :error-message="fieldErrors.name" />
 *
 * `handleSaveError` returns the structured extracted-errors map in case
 * the caller wants to also do something with it (e.g. focus the first
 * offending input). R-020 — anywhere with a dedicated Save button, this
 * is the convention.
 */
export interface UseFormErrors {
    fieldErrors: Ref<Record<string, string>>;
    generalError: Ref<string | null>;
    /**
     * Populate the refs from a caught error. `fallback` is used when
     * the error carries no useful message (e.g. unknown shape) — keep
     * it short and form-specific ("Couldn't save the recipe.").
     * Returns the extracted shape for callers that want to inspect it.
     */
    handleSaveError: (
        err: unknown,
        fallback: string,
    ) => { fieldErrors: Record<string, string>; generalError: string | null };
    /** Clear both refs — call at the top of every save attempt. */
    reset: () => void;
    /**
     * Build a `ref: <id>` suffix for the optional brief confirmation
     * toast. Same helper as `correlationSuffix`, re-exposed here so
     * forms don't need a second import.
     */
    correlationSuffix: (err: unknown) => string;
}

export function useFormErrors(): UseFormErrors {
    const fieldErrors = ref<Record<string, string>>({});
    const generalError = ref<string | null>(null);

    function reset() {
        fieldErrors.value = {};
        generalError.value = null;
    }

    function handleSaveError(err: unknown, fallback: string) {
        const extracted = extractFieldErrors(err);
        fieldErrors.value = extracted.fieldErrors;
        generalError.value = extracted.generalError ?? fallback;
        return extracted;
    }

    return {
        fieldErrors,
        generalError,
        handleSaveError,
        reset,
        correlationSuffix,
    };
}
