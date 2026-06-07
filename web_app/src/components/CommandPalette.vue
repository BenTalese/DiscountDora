<template>
    <q-dialog
        v-model="paletteOpen"
        position="top"
        transition-show="fade"
        transition-hide="fade"
        @hide="onHide"
    >
        <q-card class="command-palette">
            <div class="row items-center q-px-md q-pt-md q-pb-sm">
                <q-icon :name="ICONS.search" size="20px" class="q-mr-sm dora-text-secondary" />
                <q-input
                    ref="inputRef"
                    v-model="query"
                    borderless
                    dense
                    autofocus
                    class="col"
                    placeholder="Type a command or search…"
                    @keydown="onInputKeydown"
                />
                <kbd class="cp-kbd">Esc</kbd>
            </div>
            <q-linear-progress v-if="searchLoading" indeterminate size="2px" color="primary" />
            <q-separator />

            <div ref="listRef" class="cp-list" role="listbox" :aria-activedescendant="activeId">
                <div v-if="flatItems.length === 0" class="dora-text-muted text-caption q-pa-lg text-center">
                    <span v-if="query.trim()">No matches.</span>
                    <span v-else>Type to search — or pick a command below.</span>
                </div>

                <template v-for="(group, gi) in groupedItems" :key="group.label + gi">
                    <div class="cp-section-label">{{ group.label }}</div>
                    <div
                        v-for="item in group.items"
                        :key="item.key"
                        :id="`cp-item-${item.index}`"
                        :class="['cp-row', { 'cp-row--selected': selectedIndex === item.index }]"
                        role="option"
                        :aria-selected="selectedIndex === item.index"
                        @mouseenter="selectedIndex = item.index"
                        @click="executeAt(item.index)"
                    >
                        <q-icon :name="item.icon" size="18px" class="cp-row__icon" />
                        <div class="cp-row__text">
                            <div class="cp-row__title">
                                <template v-for="(seg, si) in renderTitle(item.title, item.spans)" :key="si">
                                    <span v-if="seg.hl" class="cp-hl">{{ seg.text }}</span>
                                    <span v-else>{{ seg.text }}</span>
                                </template>
                            </div>
                            <div v-if="item.subtitle" class="cp-row__subtitle">{{ item.subtitle }}</div>
                        </div>
                        <q-chip v-if="item.badge" dense square size="sm" class="cp-row__badge">
                            {{ item.badge }}
                        </q-chip>
                    </div>
                </template>
            </div>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import type { QInput } from 'quasar';
    import { useQuasar } from 'quasar';
    import {
        bumpCommandUsage,
        commandUsageCount,
        useCommandsRegistry,
    } from 'src/composables/useCommands';
    import { useCommandPalette } from 'src/composables/useCommandPalette';
    import { pushRecent, useRecents } from 'src/composables/useRecents';
    import SearchApiService, {
        type SearchResult,
        type SearchResultType,
    } from 'src/services/api/searchApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, nextTick, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const { paletteOpen, closePalette } = useCommandPalette();
    const { commands } = useCommandsRegistry();
    const { recents } = useRecents();
    const shoppingListStore = useShoppingListStore();
    const { quickAddTargetListId } = storeToRefs(shoppingListStore);

    const api = new SearchApiService();
    const inputRef = ref<QInput | null>(null);
    const listRef = ref<HTMLElement | null>(null);

    const query = ref('');
    const selectedIndex = ref(0);
    const searchLoading = ref(false);
    const searchResults = ref<SearchResult[]>([]);
    let searchToken = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const ICON: Record<SearchResultType, string> = {
        stock_item: 'inventory_2',
        shopping_list: 'shopping_cart',
        recipe: 'menu_book',
        location: 'place',
        product: 'local_offer',
        meal_plan: 'calendar_month',
    };
    const TYPE_LABEL: Record<SearchResultType, string> = {
        stock_item: 'Stock items',
        shopping_list: 'Shopping lists',
        recipe: 'Recipes',
        location: 'Locations',
        product: 'Products',
        meal_plan: 'Meal plans',
    };

    function pathForEntity(type: SearchResultType, id: string): string {
        switch (type) {
            case 'stock_item': return `/stock/${id}`;
            case 'shopping_list': return `/shopping-lists/${id}`;
            case 'recipe': return `/recipes/${id}`;
            case 'location': return `/stock?location_id=${id}`;
            case 'product': return '/my-products';
            case 'meal_plan': return '/meal-plans';
        }
    }

    // ── Client-side command filtering (substring + start-of-word bonus) ──
    function commandScore(needle: string, label: string, tags: string[] = []): number {
        if (!needle) return 0;
        const q = needle.toLowerCase();
        const l = label.toLowerCase();
        if (l === q) return 200;
        if (l.startsWith(q)) return 160;
        if (l.includes(q)) return 120;
        for (const t of tags) if (t.toLowerCase().includes(q)) return 90;
        return 0;
    }

    const visibleCommands = computed(() =>
        commands.filter((c) => !c.when || c.when()),
    );

    const filteredCommands = computed(() => {
        const q = query.value.trim();
        if (!q) {
            // Empty query: most-used 6 first, then the rest.
            return [...visibleCommands.value].sort((a, b) => {
                const ua = commandUsageCount(a.id);
                const ub = commandUsageCount(b.id);
                if (ua !== ub) return ub - ua;
                return a.label.localeCompare(b.label);
            });
        }
        const scored = visibleCommands.value
            .map((c) => ({ c, score: commandScore(q, c.label, c.tags) }))
            .filter((x) => x.score > 0);
        scored.sort((a, b) => b.score - a.score);
        return scored.map((x) => x.c);
    });

    // ── Search (entities) ────────────────────────────────────────────────
    watch(query, (q) => {
        if (debounceTimer) clearTimeout(debounceTimer);
        const trimmed = q.trim();
        if (!trimmed) {
            searchResults.value = [];
            searchLoading.value = false;
            selectedIndex.value = 0;
            return;
        }
        debounceTimer = setTimeout(() => void runSearch(trimmed), 120);
    });

    async function runSearch(q: string) {
        const myToken = ++searchToken;
        searchLoading.value = true;
        try {
            const resp = await api.searchAsync(q, { limit: 8 });
            if (myToken !== searchToken) return;
            searchResults.value = resp.results;
            selectedIndex.value = 0;
        } catch {
            if (myToken !== searchToken) return;
            searchResults.value = [];
        } finally {
            if (myToken === searchToken) searchLoading.value = false;
        }
    }

    // ── Flat selectable list (grouped for rendering) ─────────────────────
    type Row = {
        key: string;
        index: number;
        title: string;
        subtitle: string | null;
        icon: string;
        spans: number[][];
        badge?: string;
        execute: () => void;
    };
    type Group = { label: string; items: Row[] };

    const groupedItems = computed<Group[]>(() => {
        const groups: Group[] = [];
        let i = 0;
        const push = (label: string, rows: Omit<Row, 'index'>[]): void => {
            if (rows.length === 0) return;
            const items: Row[] = rows.map((r) => ({ ...r, index: i++ }));
            groups.push({ label, items });
        };

        const q = query.value.trim();
        if (!q) {
            // Empty-query view: recents + commands (most-used first).
            push(
                'Recents',
                recents.value.slice(0, 8).map((r) => ({
                    key: `recent-${r.type}-${r.id}`,
                    title: r.title,
                    subtitle: r.subtitle ?? TYPE_LABEL[r.type],
                    icon: ICON[r.type],
                    spans: [],
                    badge: TYPE_LABEL[r.type],
                    execute: () => {
                        pushRecent({ type: r.type, id: r.id, title: r.title, subtitle: r.subtitle ?? null });
                        void router.push(pathForEntity(r.type, r.id));
                        closePalette();
                    },
                })),
            );
            push(
                'Commands',
                filteredCommands.value.slice(0, 20).map((c) => ({
                    key: `cmd-${c.id}`,
                    title: c.label,
                    subtitle: c.section ?? null,
                    icon: c.icon ?? 'play_arrow',
                    spans: [],
                    execute: () => {
                        bumpCommandUsage(c.id);
                        closePalette();
                        void c.action();
                    },
                })),
            );
        } else {
            // Query view: matching commands first, then per-type entity groups.
            push(
                'Commands',
                filteredCommands.value.slice(0, 6).map((c) => ({
                    key: `cmd-${c.id}`,
                    title: c.label,
                    subtitle: c.section ?? null,
                    icon: c.icon ?? 'play_arrow',
                    spans: [],
                    execute: () => {
                        bumpCommandUsage(c.id);
                        closePalette();
                        void c.action();
                    },
                })),
            );
            const byType = new Map<SearchResultType, SearchResult[]>();
            for (const r of searchResults.value) {
                const list = byType.get(r.type) ?? [];
                list.push(r);
                byType.set(r.type, list);
            }
            const order: SearchResultType[] = [
                'stock_item', 'shopping_list', 'recipe', 'location', 'product', 'meal_plan',
            ];
            for (const t of order) {
                const list = byType.get(t);
                if (!list) continue;
                push(
                    TYPE_LABEL[t],
                    list.map((r) => ({
                        key: `${r.type}-${r.id}`,
                        title: r.title,
                        subtitle: r.subtitle,
                        icon: ICON[r.type],
                        spans: r.match_spans,
                        execute: () => {
                            pushRecent({ type: r.type, id: r.id, title: r.title, subtitle: r.subtitle });
                            void router.push(pathForEntity(r.type, r.id));
                            closePalette();
                        },
                    })),
                );
            }
        }
        return groups;
    });

    const flatItems = computed<Row[]>(() => groupedItems.value.flatMap((g) => g.items));

    const activeId = computed(() =>
        flatItems.value[selectedIndex.value] ? `cp-item-${selectedIndex.value}` : '',
    );

    // ── Title highlighting ───────────────────────────────────────────────
    function renderTitle(title: string, spans: number[][]): { text: string; hl: boolean }[] {
        if (!spans || spans.length === 0) return [{ text: title, hl: false }];
        const sorted = [...spans].sort((a, b) => (a[0] ?? 0) - (b[0] ?? 0));
        const segs: { text: string; hl: boolean }[] = [];
        let cursor = 0;
        for (const [s, e] of sorted) {
            const sn = s ?? 0;
            const en = e ?? 0;
            if (sn > cursor) segs.push({ text: title.slice(cursor, sn), hl: false });
            segs.push({ text: title.slice(sn, en), hl: true });
            cursor = en;
        }
        if (cursor < title.length) segs.push({ text: title.slice(cursor), hl: false });
        return segs;
    }

    // ── Keyboard nav ─────────────────────────────────────────────────────
    function clamp(n: number, lo: number, hi: number): number {
        return Math.max(lo, Math.min(hi, n));
    }
    function move(delta: number) {
        const len = flatItems.value.length;
        if (len === 0) return;
        selectedIndex.value = clamp(selectedIndex.value + delta, 0, len - 1);
        void nextTick(() => {
            const el = document.getElementById(`cp-item-${selectedIndex.value}`);
            el?.scrollIntoView({ block: 'nearest' });
        });
    }
    function executeAt(idx: number) {
        const item = flatItems.value[idx];
        if (item) item.execute();
    }
    function onInputKeydown(event: KeyboardEvent) {
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            move(1);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            move(-1);
        } else if (event.key === 'Enter') {
            event.preventDefault();
            executeAt(selectedIndex.value);
        } else if (event.key === 'Escape') {
            // First Esc clears a non-empty query; second closes (q-dialog default).
            if (query.value.length > 0) {
                event.preventDefault();
                event.stopPropagation();
                query.value = '';
            }
        }
    }

    function onHide() {
        query.value = '';
        searchResults.value = [];
        selectedIndex.value = 0;
    }

    // Reset + refocus each time the palette opens.
    watch(paletteOpen, (open) => {
        if (!open) return;
        query.value = '';
        searchResults.value = [];
        selectedIndex.value = 0;
        void nextTick(() => inputRef.value?.focus());
    });

    // Used by the dark-mode command in MainLayout. Exposed so we can also flip
    // dark mode straight from here if a context command wants to.
    void $q.dark;
    // shoppingListStore.quickAddTargetListId is referenced by the "open primary list"
    // static command — pre-import here so the store is initialised when the
    // palette mounts.
    void quickAddTargetListId;
</script>

<style scoped>
    .command-palette {
        width: 600px;
        max-width: 95vw;
        margin-top: 8vh;
        max-height: 70vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .cp-kbd {
        font-family: monospace;
        font-size: 0.7rem;
        padding: 2px 6px;
        border: 1px solid var(--q-grey-5, var(--border-strong));
        border-bottom-width: 2px;
        border-radius: 4px;
        background: var(--overlay-hover);
    }
    .cp-list {
        overflow-y: auto;
        min-height: 80px;
    }
    .cp-section-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        padding: 10px 16px 4px;
    }
    .cp-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px;
        cursor: pointer;
    }
    .cp-row--selected {
        background: color-mix(in srgb, var(--brand-primary) 12%, transparent);
    }
    .cp-row__icon {
        flex-shrink: 0;
        color: var(--q-grey-8, var(--text-secondary));
    }
    .cp-row__text {
        flex: 1;
        min-width: 0;
    }
    .cp-row__title {
        font-size: 0.95rem;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .cp-row__subtitle {
        font-size: 0.78rem;
        color: var(--text-muted);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .cp-row__badge {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .cp-hl {
        background: var(--highlight-search);
        border-radius: 2px;
    }
</style>
