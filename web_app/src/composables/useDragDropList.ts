import { reactive, readonly } from 'vue';

/**
 * Shared HTML5 drag-and-drop scaffolding for reorderable lists.
 *
 * Three editor surfaces (shopping-list lines, recipe steps, recipe
 * ingredients) had hand-rolled drag state + nearly-identical CSS;
 * this composable owns the state machine and exposes per-row binding
 * objects, leaving each consumer to write only the bits that are
 * actually different (drop-target validity and the drop-completion
 * effect). See `R-022 / ADR-018` in `ENGINEERING_STANDARDS.md`.
 *
 * Two surface shapes are supported:
 *  - **handle mode** — spread `handleProps` on a small drag-handle
 *    element (icon button), and `rowProps` + `rowClass` on the row
 *    body. Inputs/selects inside the row body stay normally
 *    interactive. Recipe step/ingredient editors use this.
 *  - **whole-row mode** — spread both `handleProps` and `rowProps`
 *    on the same element (typically a `q-item`). The whole row is
 *    grabbable. Shopping-list lines use this (no inline editors on
 *    the row).
 *
 * `mime` is a unique payload type per logical list so a drag in
 * one list never satisfies a drop check in another (dragover keys
 * off the MIME types present on the DataTransfer).
 */

export interface UseDragDropListOptions<TItem> {
    /** Stable id for an item; used as the drag payload and as the
     *  `draggingId` / `dragOverId` value. Returning null/undefined
     *  marks the row as non-draggable (e.g. a freshly-added row that
     *  hasn't been assigned a client_id yet). */
    getId: (item: TItem) => string | null | undefined;

    /** Called when a valid drop completes. Receives both ids and the
     *  resolved items so the consumer doesn't have to look them up
     *  again. The composable has already cleared its drag state by
     *  the time this fires. */
    onDrop: (
        source: { id: string; item: TItem },
        target: { id: string; item: TItem },
    ) => void;

    /** Unique MIME type for this list's drag payload. Convention:
     *  `application/x-dora-<thing>`. Prevents cross-list drops. */
    mime: string;

    /** Per-row drag-start gate. Return false to disable dragging
     *  that row (and to hide the browser's drag affordance — the
     *  `draggable` attribute reflects this). Use for both per-row
     *  and global gates (return based on a captured ref). */
    canDragStart?: (item: TItem) => boolean;

    /** Per-pair drop-target gate. Defaults to "anything but self".
     *  Use to enforce siblings-only / nesting / type-compat
     *  constraints. The default rejects same-id drops; consumers
     *  layering extra rules don't need to re-check that. */
    canDropOn?: (source: TItem, target: TItem) => boolean;
}

export interface DragDropRowBindings {
    /** Spread on the handle (or on the whole row in whole-row mode).
     *  `draggable` reflects `canDragStart(item)`; `dragstart` sets
     *  the payload and effect; `dragend` clears the drag state. */
    handleProps: {
        draggable: boolean;
        onDragstart: (event: DragEvent) => void;
        onDragend: () => void;
    };
    /** Spread on the row body (drop target). */
    rowProps: {
        onDragover: (event: DragEvent) => void;
        onDragleave: () => void;
        onDrop: (event: DragEvent) => void;
    };
    /** Class binding object — `dora-dnd-row`, plus `--dragging` on
     *  the source while it's being dragged, plus `--drop-over` on
     *  the row the cursor is over. Use with `:class` on the row. */
    rowClass: Record<string, boolean>;
    /** This row is the active source. */
    isDragging: boolean;
    /** This row is the active drop target. */
    isDropOver: boolean;
}

export interface DragDropListState {
    /** Id of the row currently being dragged, or null. */
    draggingId: string | null;
    /** Id of the row currently under the cursor, or null. */
    dragOverId: string | null;
}

export function useDragDropList<TItem>(options: UseDragDropListOptions<TItem>) {
    const state = reactive<DragDropListState>({
        draggingId: null,
        dragOverId: null,
    });

    // The composable owns a private item lookup keyed by id so the
    // drop handler can resolve the source row even after a re-render
    // moved its index. Refreshed on every dragstart (always current).
    let sourceItem: TItem | null = null;

    function clearState() {
        state.draggingId = null;
        state.dragOverId = null;
        sourceItem = null;
    }

    function isValidDropTarget(target: TItem): boolean {
        if (state.draggingId == null || sourceItem == null) return false;
        const targetId = options.getId(target);
        if (!targetId || targetId === state.draggingId) return false;
        if (options.canDropOn && !options.canDropOn(sourceItem, target)) return false;
        return true;
    }

    function bind(item: TItem): DragDropRowBindings {
        const id = options.getId(item) ?? null;
        const draggable = id != null && (options.canDragStart ? options.canDragStart(item) : true);
        const isDragging = id != null && state.draggingId === id;
        const isDropOver = id != null && state.dragOverId === id;

        return {
            handleProps: {
                draggable,
                onDragstart: (event: DragEvent) => {
                    if (!draggable || !id || !event.dataTransfer) return;
                    event.dataTransfer.setData(options.mime, id);
                    event.dataTransfer.effectAllowed = 'move';
                    // Use the closest `.dora-dnd-row` as the drag image so
                    // the preview matches the row, not the small handle.
                    // Consumers can opt out by stopping propagation in
                    // their own listener before this fires (very rare).
                    const handleEl = event.target as HTMLElement | null;
                    const rowEl = handleEl?.closest('.dora-dnd-row') as HTMLElement | null;
                    if (rowEl) event.dataTransfer.setDragImage(rowEl, 0, 0);
                    state.draggingId = id;
                    sourceItem = item;
                },
                onDragend: () => {
                    clearState();
                },
            },
            rowProps: {
                onDragover: (event: DragEvent) => {
                    if (!event.dataTransfer?.types.includes(options.mime)) return;
                    if (!isValidDropTarget(item)) return;
                    // preventDefault enables drop; without it the browser
                    // rejects the operation regardless of the listener.
                    event.preventDefault();
                    event.dataTransfer.dropEffect = 'move';
                    const targetId = options.getId(item);
                    if (targetId) state.dragOverId = targetId;
                },
                onDragleave: () => {
                    const targetId = options.getId(item);
                    if (targetId && state.dragOverId === targetId) {
                        state.dragOverId = null;
                    }
                },
                onDrop: (event: DragEvent) => {
                    if (!isValidDropTarget(item)) return;
                    event.preventDefault();
                    const sourceId = state.draggingId;
                    const targetId = options.getId(item);
                    const capturedSource = sourceItem;
                    clearState();
                    if (!sourceId || !targetId || !capturedSource) return;
                    options.onDrop(
                        { id: sourceId, item: capturedSource },
                        { id: targetId, item },
                    );
                },
            },
            rowClass: {
                'dora-dnd-row': true,
                'dora-dnd-row--dragging': isDragging,
                'dora-dnd-row--drop-over': isDropOver,
            },
            isDragging,
            isDropOver,
        };
    }

    return {
        /** Read-only drag state. Useful for surfaces that want to
         *  branch on "is anything being dragged right now?" outside
         *  of the per-row bindings (rare). */
        state: readonly(state),
        /** Build the per-row bindings. Call inside the template (or
         *  a computed) — values reflect the current drag state and
         *  re-evaluate naturally when state changes. */
        bind,
    };
}
