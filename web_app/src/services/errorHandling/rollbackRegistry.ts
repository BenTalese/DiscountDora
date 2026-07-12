const rollbackRegistry: (() => void)[] = [];

export function registerRollback(fn: (() => void)) {
    rollbackRegistry.push(fn);
}

export function executeRollbacks() {
    while (rollbackRegistry.length) {
        const fn = rollbackRegistry.pop();
        // Each rollback is isolated: this registry's whole job is undoing
        // optimistic UI state, so one throwing undo must not strand the
        // remaining ones (they'd stay stranded in the stack and never run).
        // Swallow + log the failure and keep popping.
        if (fn) {
            try {
                fn();
            } catch (err) {
                console.error('[rollbackRegistry] a rollback threw; continuing', err);
            }
        }
    }
}

export function clearRollbacks() {
    rollbackRegistry.splice(0, rollbackRegistry.length);
}
