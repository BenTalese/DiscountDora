const rollbackRegistry: (() => void)[] = [];

export function registerRollback(fn: (() => void)) {
    rollbackRegistry.push(fn);
}

export function executeRollbacks() {
    while (rollbackRegistry.length) {
        const fn = rollbackRegistry.pop();
        if (fn) fn();
    }
}

export function clearRollbacks() {
    rollbackRegistry.splice(0, rollbackRegistry.length);
}
