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
