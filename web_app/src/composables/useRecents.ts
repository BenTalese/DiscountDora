import { ref } from 'vue';

import type { SearchResultType } from 'src/services/api/searchApiService';

// Local-storage backed "recent entities" — per-device, no backend table.
// The palette reads this when the query is empty; CommandPalette pushes a
// recent when the user selects an entity result.

const KEY = 'dora.recents.v1';
const MAX = 20;

export type RecentEntry = {
    type: SearchResultType;
    id: string;
    title: string;
    subtitle?: string | null;
    visitedAt: number;
};

const recents = ref<RecentEntry[]>([]);

function load() {
    try {
        const raw = localStorage.getItem(KEY);
        recents.value = raw ? (JSON.parse(raw) as RecentEntry[]) : [];
    } catch {
        recents.value = [];
    }
}

function persist() {
    try {
        localStorage.setItem(KEY, JSON.stringify(recents.value));
    } catch {
        // Quota / disabled — recents just don't survive a reload, fine.
    }
}

load();

export function pushRecent(entry: Omit<RecentEntry, 'visitedAt'>): void {
    const next: RecentEntry = { ...entry, visitedAt: Date.now() };
    const deduped = recents.value.filter((r) => !(r.type === next.type && r.id === next.id));
    recents.value = [next, ...deduped].slice(0, MAX);
    persist();
}

export function useRecents() {
    return { recents };
}
