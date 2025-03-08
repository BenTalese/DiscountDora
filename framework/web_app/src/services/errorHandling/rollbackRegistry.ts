const rollbackRegistry: Function[] = [];

export function registerRollback(fn: Function) {
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
