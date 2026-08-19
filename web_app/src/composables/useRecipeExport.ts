/**
 * Recipe export actions — CSV (ingredients) + print-view (recipe card).
 * Sibling to useShoppingListExport; same shape so callers can swap.
 */
import { Notify } from 'quasar';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
import { parseFilename, triggerSave } from 'src/services/files/downloadHelpers';
import { openHtmlDocumentAsync, PopupBlockedError } from 'src/services/files/printView';
import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

export function useRecipeExport() {
    const baseUrl = resolveBaseURL();

    async function downloadCsv(recipeId: string): Promise<void> {
        try {
            const response = await fetch(
                `${baseUrl}/recipes/${encodeURIComponent(recipeId)}/export?format=csv`,
                { method: 'GET', credentials: 'include' },
            );
            if (!response.ok) {
                throw new Error(`Export failed (${response.status})`);
            }
            const filename =
                parseFilename(response.headers.get('content-disposition'))
                ?? `recipe-${recipeId}.csv`;
            const blob = await response.blob();
            triggerSave(blob, filename);
        } catch (err) {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't export the recipe.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    /** Reported 2026-08-19 as "Print button 404s".
     *
     *  It was `window.open(`${baseUrl}/recipes/.../print-view`)` — the exact
     *  R-045 violation signal (a `window.open` built from `resolveBaseURL()`).
     *  That navigation is authenticated only if the browser volunteers the
     *  session cookie, which it does on a same-site dev box (the route returns
     *  200 there, which is why this survived) and declines once the SPA and API
     *  are on different sites — and can never do in the Capacitor shell, whose
     *  SPA origin is not the API origin. The server then answers 401/404 and
     *  the user gets a raw problem document in a new tab.
     *
     *  Same defect the QR sheet had (ADR-041/042); this sibling was never
     *  swept. Now fetched through the client and handed to the tab as a blob,
     *  with the tab claimed on the gesture (R-046) — so this **must** stay a
     *  sync entry point, no `await` before the call below.
     */
    function openPrintView(recipeId: string): void {
        void openHtmlDocumentAsync(
            `/recipes/${encodeURIComponent(recipeId)}/print-view`,
            'Recipe',
        ).catch((err) => {
            // A blocked pop-up is the user's to fix ("allow pop-ups"), not a
            // bug report — so it gets its own sentence and no error ref.
            Notify.create(err instanceof PopupBlockedError
                ? {
                    type: 'negative',
                    position: 'bottom-right',
                    message: 'Your browser blocked the print tab — allow pop-ups for Dora and try again.',
                }
                : {
                    type: 'negative',
                    position: 'bottom-right',
                    message: "Couldn't open the print view.",
                    caption: toastCaption(err),
                });
        });
    }

    return { downloadCsv, openPrintView };
}

