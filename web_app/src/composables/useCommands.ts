import { onMounted, onUnmounted, reactive, readonly } from 'vue';

// In-app command registry for the Cmd-K palette (S1).
//
// Commands auto-register on mount and deregister on unmount, so page-specific
// commands are live only while their page is on screen. Static "always
// available" commands are registered by MainLayout, which is mounted for the
// whole authenticated session.

export interface CommandDef {
    /** Stable id used for most-used tracking in localStorage. */
    id: string;
    label: string;
    icon?: string;
    /** Group/section label in the palette (e.g. 'Create', 'Navigate'). */
    section?: string;
    /** Extra strings fed into the fuzzy match (synonyms, abbreviations). */
    tags?: string[];
    /** Hide the command when this returns false at render time. */
    when?: () => boolean;
    action: () => void | Promise<void>;
}

interface RegisteredCommand extends CommandDef {
    refId: number;
}

const registry = reactive<RegisteredCommand[]>([]);
let nextRefId = 1;

const USAGE_KEY = 'dora.commandUsage.v1';

function loadUsage(): Record<string, number> {
    try {
        const raw = localStorage.getItem(USAGE_KEY);
        return raw ? (JSON.parse(raw) as Record<string, number>) : {};
    } catch {
        return {};
    }
}

function saveUsage(usage: Record<string, number>) {
    try {
        localStorage.setItem(USAGE_KEY, JSON.stringify(usage));
    } catch {
        // localStorage can be disabled — usage tracking is best-effort.
    }
}

export function bumpCommandUsage(id: string): void {
    const usage = loadUsage();
    usage[id] = (usage[id] ?? 0) + 1;
    saveUsage(usage);
}

export function commandUsageCount(id: string): number {
    return loadUsage()[id] ?? 0;
}

/** Register one or more commands for the lifetime of the calling component. */
export function useCommands(defs: CommandDef | CommandDef[]): void {
    const list = Array.isArray(defs) ? defs : [defs];
    const refIds: number[] = [];

    onMounted(() => {
        for (const def of list) {
            const refId = nextRefId++;
            registry.push({ ...def, refId });
            refIds.push(refId);
        }
    });

    onUnmounted(() => {
        for (const refId of refIds) {
            const idx = registry.findIndex((c) => c.refId === refId);
            if (idx >= 0) registry.splice(idx, 1);
        }
    });
}

export function useCommandsRegistry() {
    return { commands: readonly(registry) };
}
