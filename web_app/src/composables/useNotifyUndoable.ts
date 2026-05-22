// Toast helper that pairs success notifications with an inline Undo
// action (F5). After 10 seconds the toast itself dismisses — the entry
// stays in the global undo stack for another 19 actions, so the header
// Undo button (or Ctrl-Z) still works.

import { Notify } from 'quasar';
import {
    discardEntry,
    register as registerUndo,
    undo as runUndo,
    type RegisterArgs,
} from './useUndo';

const INLINE_UNDO_TIMEOUT_MS = 10_000;

export type UndoableNotifyArgs = {
    /** Success message shown in the toast. */
    message: string;
    /** Optional secondary line (e.g. "3 items restocked"). */
    caption?: string;
    /** Undo registration. The composable both registers it AND wires
     *  the toast's inline button to fire it. */
    undo: RegisterArgs;
};

export function notifyUndoable(args: UndoableNotifyArgs): string {
    const entryId = registerUndo(args.undo);
    Notify.create({
        type: 'positive',
        position: 'bottom-right',
        message: args.message,
        ...(args.caption ? { caption: args.caption } : {}),
        timeout: INLINE_UNDO_TIMEOUT_MS,
        actions: [
            {
                label: 'Undo',
                color: 'white',
                noDismiss: true,
                handler: async () => {
                    // Route through the stack so the entry moves to redo
                    // and stays consistent with Ctrl-Z / the header button.
                    // If for some reason it's not at the top of the stack
                    // anymore (the user fired another action since), fall
                    // back to direct inverse + discard so the toast button
                    // still does what it says it does.
                    try {
                        const undid = await runUndo();
                        if (!undid) {
                            await args.undo.inverse();
                            discardEntry(entryId);
                        }
                    } catch {
                        // Surfaced by the global handler.
                    }
                },
            },
        ],
    });
    return entryId;
}
