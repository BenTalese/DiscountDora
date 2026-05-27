<template>
    <div class="subs-page">
        <header class="subs-header">
            <div class="subs-title-block">
                <h1 class="subs-title">Substitutes</h1>
                <p class="subs-sub">
                    Map of stock items that can stand in for each other.
                    Click a node or edge to inspect and edit.
                </p>
            </div>
        </header>

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <!-- Toolbar -->
        <section class="subs-toolbar">
            <q-input
                v-model="search"
                dense
                outlined
                clearable
                debounce="150"
                label="Search nodes"
                class="subs-search"
            >
                <template #prepend><q-icon :name="ICONS.search" /></template>
            </q-input>

            <div class="subs-group-chips">
                <q-chip
                    v-for="group in stockGroups"
                    :key="group.stock_group_id"
                    :selected="selectedGroupIds.has(group.stock_group_id)"
                    clickable
                    dense
                    color="primary"
                    text-color="white"
                    @click="toggleGroup(group.stock_group_id)"
                >
                    {{ group.name }}
                </q-chip>
            </div>

            <q-toggle v-model="showIsolated" label="Show isolated" left-label dense />

            <q-btn-toggle
                v-model="layoutName"
                :options="LAYOUT_OPTIONS"
                no-caps
                dense
                rounded
                color="grey-3"
                text-color="grey-9"
                toggle-color="primary"
                toggle-text-color="white"
                @update:model-value="rerunLayout"
            />
        </section>

        <div class="subs-body">
            <div ref="graphContainer" class="subs-graph" />

            <!-- Side panel -->
            <aside v-if="selectedKind !== 'none'" class="subs-side">
                <div v-if="selectedKind === 'node' && selectedNode" class="subs-side-block">
                    <header class="subs-side-head">
                        <q-icon name="inventory_2" size="20px" class="q-mr-xs" />
                        <strong class="subs-side-name">{{ selectedNode.name }}</strong>
                        <q-space />
                        <q-btn flat round dense :icon="ICONS.close" @click="clearSelection" />
                    </header>
                    <div class="subs-side-meta">
                        <q-chip v-if="selectedNode.level" dense color="grey-3">{{ selectedNode.level }}</q-chip>
                        <q-chip v-if="groupNameFor(selectedNode.group_id)" dense color="amber-2">
                            {{ groupNameFor(selectedNode.group_id) }}
                        </q-chip>
                    </div>

                    <h4 class="subs-side-sub">Current substitutes</h4>
                    <ul v-if="substitutesOf(selectedNode.id).length > 0" class="subs-side-list">
                        <li v-for="pair in substitutesOf(selectedNode.id)" :key="otherId(pair, selectedNode.id)">
                            <span class="subs-side-other">
                                {{ nameById[otherId(pair, selectedNode.id)] ?? '—' }}
                            </span>
                            <span v-if="pair.notes" class="subs-side-note">{{ pair.notes }}</span>
                            <q-btn
                                flat
                                dense
                                size="sm"
                                :icon="ICONS.close"
                                @click="removePair(selectedNode.id, otherId(pair, selectedNode.id))"
                            >
                                <q-tooltip>Remove substitute</q-tooltip>
                            </q-btn>
                        </li>
                    </ul>
                    <div v-else class="subs-empty-inline">
                        No substitutes linked yet.
                    </div>

                    <h4 class="subs-side-sub">Add substitute</h4>
                    <q-select
                        v-model="newSubstituteId"
                        :options="addableOptions(selectedNode.id)"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        use-input
                        outlined
                        dense
                        clearable
                        label="Search items"
                        @filter="filterAddable"
                    />
                    <q-input
                        v-model="newSubstituteNotes"
                        outlined
                        dense
                        type="textarea"
                        autogrow
                        label="Notes (optional)"
                        class="q-mt-sm"
                    />
                    <q-btn
                        color="primary"
                        no-caps
                        :icon="ICONS.add"
                        label="Add"
                        :disable="!newSubstituteId"
                        class="q-mt-sm"
                        @click="addPair"
                    />

                    <q-btn
                        flat
                        no-caps
                        :icon="ICONS.open_in_new"
                        label="Open in stock detail"
                        class="q-mt-md"
                        @click="goToStock(selectedNode.id)"
                    />
                </div>

                <div v-else-if="selectedKind === 'edge' && selectedEdge" class="subs-side-block">
                    <header class="subs-side-head">
                        <q-icon :name="ICONS.link" size="20px" class="q-mr-xs" />
                        <strong class="subs-side-name">Pair</strong>
                        <q-space />
                        <q-btn flat round dense :icon="ICONS.close" @click="clearSelection" />
                    </header>
                    <div class="subs-side-pair">
                        <a class="subs-side-pair-name" @click="goToStock(selectedEdge.a)">
                            {{ nameById[selectedEdge.a] ?? '—' }}
                        </a>
                        <q-icon :name="ICONS.swap_horiz" size="18px" class="q-mx-sm" />
                        <a class="subs-side-pair-name" @click="goToStock(selectedEdge.b)">
                            {{ nameById[selectedEdge.b] ?? '—' }}
                        </a>
                    </div>
                    <h4 class="subs-side-sub">Notes</h4>
                    <q-input
                        v-model="edgeNotesDraft"
                        outlined
                        dense
                        type="textarea"
                        autogrow
                        label="Optional notes"
                    />
                    <div class="row q-gutter-sm q-mt-sm">
                        <q-btn color="primary" no-caps :icon="ICONS.save" label="Save" @click="saveEdgeNotes" />
                        <q-btn
                            flat
                            color="negative"
                            no-caps
                            :icon="ICONS.delete"
                            label="Remove pair"
                            @click="removePair(selectedEdge.a, selectedEdge.b)"
                        />
                    </div>
                </div>
            </aside>
        </div>

        <div v-if="graph && graph.edges.length === 0" class="subs-empty">
            <p class="subs-empty-title">No substitutes yet.</p>
            <p>Link two items that can stand in for each other so you have a backup
                option when one's out.</p>
            <q-btn
                color="primary"
                no-caps
                :icon="ICONS.add"
                label="Add your first substitute"
                @click="openFirstSubstituteFlow"
            />
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import cytoscape, { type Core, type ElementDefinition, type LayoutOptions } from 'cytoscape';
    import { storeToRefs } from 'pinia';
    import { Notify } from 'quasar';
    import type { StockGroup } from 'src/models/stockGroup';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import SubstitutesApiService, {
        type GraphEdge,
        type GraphNode,
        type SubstitutesGraph,
    } from 'src/services/api/substitutesApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const subsApi = new SubstitutesApiService();
    const groupApi = new StockGroupApiService();
    const stockItemStore = useStockItemStore();
    const { stockItems } = storeToRefs(stockItemStore);

    const LAYOUT_OPTIONS = [
        { label: 'Force', value: 'cose' },
        { label: 'Concentric', value: 'concentric' },
        { label: 'Breadth-first', value: 'breadthfirst' },
    ];

    const graph = ref<SubstitutesGraph | null>(null);
    const stockGroups = ref<StockGroup[]>([]);
    const loadError = ref<string | null>(null);

    const search = ref('');
    const selectedGroupIds = ref(new Set<string>());
    const showIsolated = ref(true);
    const layoutName = ref<'cose' | 'concentric' | 'breadthfirst'>('cose');

    const selectedKind = ref<'none' | 'node' | 'edge'>('none');
    const selectedNode = ref<GraphNode | null>(null);
    const selectedEdge = ref<GraphEdge | null>(null);

    const newSubstituteId = ref<string | null>(null);
    const newSubstituteNotes = ref('');
    const edgeNotesDraft = ref('');

    const addableOptionsCache = ref<Map<string, { label: string; value: string }[]>>(new Map());

    const graphContainer = ref<HTMLElement | null>(null);
    let cy: Core | null = null;

    const nameById = computed<Record<string, string>>(() => {
        const out: Record<string, string> = {};
        for (const n of graph.value?.nodes ?? []) out[n.id] = n.name;
        return out;
    });

    function groupNameFor(groupId: string | null | undefined): string | null {
        if (!groupId) return null;
        return stockGroups.value.find((g) => g.stock_group_id === groupId)?.name ?? null;
    }

    function toggleGroup(id: string) {
        const next = new Set(selectedGroupIds.value);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        selectedGroupIds.value = next;
        rebuildElements();
    }

    function substitutesOf(nodeId: string): GraphEdge[] {
        return (graph.value?.edges ?? []).filter((e) => e.a === nodeId || e.b === nodeId);
    }

    function otherId(pair: GraphEdge, me: string): string {
        return pair.a === me ? pair.b : pair.a;
    }

    // Resolve theme tokens once per build; cytoscape doesn't react to CSS
    // var changes inside its inline style, so we read them at element-build
    // time and rebuild on theme switch.
    //
    // Critically, getPropertyValue returns the *literal* CSS value, which
    // for our tokens is modern hsl(h s% l%) syntax (no commas). Cytoscape's
    // colour parser doesn't accept that form and silently falls back to
    // black — that was the "black highlight on black text" bug. We
    // normalise every value through a hidden canvas, which gets us a
    // canonical "#rrggbb"/"rgba(...)" cytoscape can parse reliably.
    const colourCanvas = typeof document === 'undefined'
        ? null : document.createElement('canvas').getContext('2d');
    function normaliseColour(raw: string): string {
        if (!colourCanvas) return raw;
        try {
            colourCanvas.fillStyle = '#000';     // reset so a bad value can't carry over
            colourCanvas.fillStyle = raw;
            return colourCanvas.fillStyle;
        } catch {
            return raw;
        }
    }
    function themeTokens() {
        const cs = typeof document === 'undefined' ? null : getComputedStyle(document.documentElement);
        const read = (name: string, fallback: string) =>
            normaliseColour((cs?.getPropertyValue(name).trim() || fallback));
        return {
            negative: read('--semantic-negative', '#c85a4f'),
            warning: read('--semantic-warning', '#e89a45'),
            borderMuted: read('--border-strong', '#ddd5bd'),
            surfaceSunken: read('--surface-sunken', '#dccfae'),
            edge: read('--border-strong', '#bcae8d'),
            accent: read('--brand-primary', '#f4b740'),
            textPrimary: read('--text-primary', '#2e2820'),
            surfacePage: read('--surface-page', '#fdfaf3'),
            chart: [
                read('--chart-1', '#17b073'),
                read('--chart-2', '#006a80'),
                read('--chart-3', '#fed224'),
                read('--chart-4', '#e89a45'),
                read('--chart-5', '#5b8db8'),
                read('--chart-6', '#a07cc8'),
            ],
        };
    }
    let themeCache = themeTokens();

    function levelColour(level: string | null): string {
        const l = (level ?? '').toLowerCase();
        if (l.includes('out')) return themeCache.negative;
        if (l.includes('low')) return themeCache.warning;
        return themeCache.borderMuted;
    }

    function groupColour(groupId: string | null | undefined): string {
        if (!groupId) return themeCache.surfaceSunken;
        let hash = 0;
        for (let i = 0; i < groupId.length; i++) {
            hash = (hash * 31 + groupId.charCodeAt(i)) | 0;
        }
        return themeCache.chart[Math.abs(hash) % themeCache.chart.length]!;
    }

    // ── Build cytoscape elements from the (filtered) graph + toggles ────
    function buildElements(): ElementDefinition[] {
        if (!graph.value) return [];
        const needle = search.value.trim().toLowerCase();
        const groupFilter = selectedGroupIds.value;

        const adjacency = new Map<string, number>();
        for (const e of graph.value.edges) {
            adjacency.set(e.a, (adjacency.get(e.a) ?? 0) + 1);
            adjacency.set(e.b, (adjacency.get(e.b) ?? 0) + 1);
        }

        const nodesById = new Map(graph.value.nodes.map((n) => [n.id, n]));
        const includedNodeIds = new Set<string>();
        for (const node of graph.value.nodes) {
            if (groupFilter.size > 0 && (!node.group_id || !groupFilter.has(node.group_id))) {
                continue;
            }
            if (!showIsolated.value && (adjacency.get(node.id) ?? 0) === 0) {
                continue;
            }
            includedNodeIds.add(node.id);
        }

        const els: ElementDefinition[] = [];
        for (const id of includedNodeIds) {
            const node = nodesById.get(id)!;
            const matchesSearch = needle.length === 0 || node.name.toLowerCase().includes(needle);
            els.push({
                data: {
                    id: node.id,
                    label: node.name,
                    level: node.level ?? '',
                    groupColour: groupColour(node.group_id),
                    levelColour: levelColour(node.level),
                },
                classes: matchesSearch ? '' : 'dimmed',
            });
        }
        for (const edge of graph.value.edges) {
            if (!includedNodeIds.has(edge.a) || !includedNodeIds.has(edge.b)) continue;
            els.push({
                data: {
                    id: `${edge.a}__${edge.b}`,
                    source: edge.a,
                    target: edge.b,
                    notes: edge.notes ?? '',
                },
            });
        }
        return els;
    }

    function layoutOpts(): LayoutOptions {
        switch (layoutName.value) {
            case 'concentric':
                return { name: 'concentric', minNodeSpacing: 30, animate: false } as LayoutOptions;
            case 'breadthfirst':
                return { name: 'breadthfirst', spacingFactor: 1.2, animate: false } as LayoutOptions;
            case 'cose':
            default:
                return { name: 'cose', animate: false, randomize: false, idealEdgeLength: () => 80 } as LayoutOptions;
        }
    }

    function rerunLayout() {
        if (!cy) return;
        cy.layout(layoutOpts()).run();
    }

    function rebuildElements() {
        if (!cy) return;
        // Re-read theme tokens — themeCache is consumed by buildElements()
        // for node group + level colours, and getting it fresh here means
        // a theme switch reflects on the next rebuild (e.g. when the user
        // returns to the page or toggles a filter).
        themeCache = themeTokens();
        const positions = new Map<string, { x: number; y: number }>();
        cy.nodes().forEach((n) => { positions.set(n.id(), { ...n.position() }); });
        cy.elements().remove();
        cy.add(buildElements());
        // Restore positions so the layout stays stable when toggling filters
        // / adding a single edge.
        cy.nodes().forEach((n) => {
            const p = positions.get(n.id());
            if (p) n.position(p);
        });
        // Only run layout for newly-added nodes (ones without restored pos).
        const newNodes = cy.nodes().filter((n) => !positions.has(n.id()));
        if (newNodes.length > 0) {
            newNodes.layout(layoutOpts()).run();
        }
    }

    function initCytoscape() {
        if (!graphContainer.value) return;
        themeCache = themeTokens();
        cy = cytoscape({
            container: graphContainer.value,
            elements: buildElements(),
            wheelSensitivity: 0.2,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': 'data(groupColour)',
                        'border-color': 'data(levelColour)',
                        'border-width': 3,
                        label: 'data(label)',
                        'font-size': 11,
                        color: themeCache.textPrimary,
                        'text-valign': 'bottom',
                        'text-margin-y': 6,
                        'text-background-color': themeCache.surfacePage,
                        'text-background-opacity': 0.85,
                        'text-background-padding': '2px',
                        width: 28,
                        height: 28,
                    },
                },
                {
                    selector: 'node.dimmed',
                    style: { opacity: 0.18 },
                },
                {
                    selector: 'edge',
                    style: {
                        'line-color': themeCache.edge,
                        width: 1.6,
                        'curve-style': 'bezier',
                    },
                },
                {
                    selector: 'edge:selected',
                    style: { 'line-color': themeCache.accent, width: 3 },
                },
                {
                    selector: 'node:selected',
                    style: { 'border-color': themeCache.accent, 'border-width': 5 },
                },
            ],
            layout: layoutOpts(),
        });
        cy.on('tap', 'node', (evt) => {
            const id = evt.target.id() as string;
            const node = (graph.value?.nodes ?? []).find((n) => n.id === id) ?? null;
            selectedNode.value = node;
            selectedEdge.value = null;
            selectedKind.value = node ? 'node' : 'none';
            newSubstituteId.value = null;
            newSubstituteNotes.value = '';
        });
        cy.on('tap', 'edge', (evt) => {
            const data = evt.target.data() as { source: string; target: string; notes: string };
            const edge = (graph.value?.edges ?? []).find(
                (e) => e.a === data.source && e.b === data.target,
            ) ?? null;
            selectedEdge.value = edge;
            selectedNode.value = null;
            selectedKind.value = edge ? 'edge' : 'none';
            edgeNotesDraft.value = edge?.notes ?? '';
        });
        cy.on('tap', (evt) => {
            // Background tap clears.
            if (evt.target === cy) clearSelection();
        });
    }

    function clearSelection() {
        selectedKind.value = 'none';
        selectedNode.value = null;
        selectedEdge.value = null;
    }

    // ── Loaders ─────────────────────────────────────────────────────────
    async function loadAll() {
        loadError.value = null;
        try {
            const [g, groups] = await Promise.all([
                subsApi.getGraphAsync(),
                groupApi.getAllAsync(),
                stockItems.value.length === 0
                    ? stockItemStore.getStockItemsAsync()
                    : Promise.resolve(),
            ]);
            graph.value = g;
            stockGroups.value = groups;
        } catch {
            loadError.value = 'Could not load the substitutes graph.';
        }
    }

    function addableOptions(forNodeId: string): { label: string; value: string }[] {
        const cached = addableOptionsCache.value.get(forNodeId);
        if (cached) return cached;
        return baseAddableOptions(forNodeId);
    }

    function baseAddableOptions(forNodeId: string): { label: string; value: string }[] {
        const existing = new Set<string>();
        existing.add(forNodeId);
        for (const e of substitutesOf(forNodeId)) {
            existing.add(otherId(e, forNodeId));
        }
        return stockItems.value
            .filter((item) => !existing.has(item.stock_item_id))
            .map((item) => ({ label: item.name, value: item.stock_item_id }))
            .slice(0, 50);
    }

    function filterAddable(input: string, doneFn: (cb: () => void) => void) {
        const needle = input.trim().toLowerCase();
        doneFn(() => {
            if (!selectedNode.value) return;
            const baseIds = new Set(baseAddableOptions(selectedNode.value.id).map((o) => o.value));
            const matches = needle.length === 0
                ? baseAddableOptions(selectedNode.value.id)
                : stockItems.value
                    .filter((item) => baseIds.has(item.stock_item_id))
                    .filter((item) => item.name.toLowerCase().includes(needle))
                    .map((item) => ({ label: item.name, value: item.stock_item_id }))
                    .slice(0, 50);
            addableOptionsCache.value.set(selectedNode.value.id, matches);
        });
    }

    // ── Mutations ───────────────────────────────────────────────────────
    async function addPair() {
        if (!selectedNode.value || !newSubstituteId.value) return;
        try {
            await subsApi.upsertPairAsync({
                a: selectedNode.value.id,
                b: newSubstituteId.value,
                notes: newSubstituteNotes.value.trim() || null,
            });
            Notify.create({ type: 'positive', position: 'bottom-right', message: 'Substitute added.' });
            await refreshAfterMutation();
        } catch {
            Notify.create({ type: 'negative', position: 'bottom-right', message: 'Could not add substitute.' });
        }
    }

    async function removePair(a: string, b: string) {
        try {
            await subsApi.deletePairAsync(a, b);
            Notify.create({ type: 'info', position: 'bottom-right', message: 'Substitute removed.' });
            await refreshAfterMutation();
        } catch {
            Notify.create({ type: 'negative', position: 'bottom-right', message: 'Could not remove substitute.' });
        }
    }

    async function saveEdgeNotes() {
        if (!selectedEdge.value) return;
        try {
            await subsApi.upsertPairAsync({
                a: selectedEdge.value.a,
                b: selectedEdge.value.b,
                notes: edgeNotesDraft.value.trim() || null,
            });
            Notify.create({ type: 'positive', position: 'bottom-right', message: 'Notes saved.' });
            await refreshAfterMutation();
        } catch {
            Notify.create({ type: 'negative', position: 'bottom-right', message: 'Could not save notes.' });
        }
    }

    async function refreshAfterMutation() {
        const wasSelectedId = selectedNode.value?.id ?? null;
        const wasEdgeKey = selectedEdge.value
            ? `${selectedEdge.value.a}__${selectedEdge.value.b}` : null;
        graph.value = await subsApi.getGraphAsync();
        await nextTick();
        rebuildElements();
        // Re-resolve the selection so the side panel keeps showing the
        // freshly-updated row instead of a stale snapshot.
        if (wasSelectedId) {
            const node = graph.value.nodes.find((n) => n.id === wasSelectedId) ?? null;
            selectedNode.value = node;
        }
        if (wasEdgeKey) {
            const [a, b] = wasEdgeKey.split('__');
            selectedEdge.value = graph.value.edges.find((e) => e.a === a && e.b === b) ?? null;
            edgeNotesDraft.value = selectedEdge.value?.notes ?? '';
            if (!selectedEdge.value) clearSelection();
        }
        newSubstituteId.value = null;
        newSubstituteNotes.value = '';
    }

    function goToStock(id: string) {
        void router.push(`/stock/${id}`);
    }

    function openFirstSubstituteFlow() {
        // Pick the first stock item with the largest "running out" surface,
        // or just the alphabetic-first if we don't have richer signals.
        const first = [...stockItems.value].sort((a, b) => a.name.localeCompare(b.name))[0];
        if (!first) return;
        selectedNode.value = {
            id: first.stock_item_id,
            name: first.name,
            level: first.stock_level_name ?? null,
            group_id: null,
        };
        selectedKind.value = 'node';
    }

    // ── Reactive plumbing ──────────────────────────────────────────────
    watch(search, () => rebuildElements());
    watch(showIsolated, () => rebuildElements());
    watch(graph, () => {
        if (cy) rebuildElements();
    });

    onMounted(async () => {
        await loadAll();
        await nextTick();
        initCytoscape();
    });
    onUnmounted(() => {
        if (cy) {
            cy.destroy();
            cy = null;
        }
    });
</script>

<style scoped>
    .subs-page {
        padding: 24px 24px 96px;
        background: var(--surface-page);
        color: var(--text-primary);
        min-height: 100%;
    }
    .subs-header { margin-bottom: 16px; }
    .subs-title { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .subs-sub {
        margin: 4px 0 0;
        color: var(--text-secondary);
        font-size: 0.92rem;
        max-width: 60ch;
    }
    .subs-toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 14px;
        margin-bottom: 16px;
    }
    .subs-search { flex: 1 1 240px; max-width: 320px; }
    .subs-group-chips { display: flex; flex-wrap: wrap; gap: 4px; flex: 1 1 240px; }
    .subs-body {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 360px;
        gap: 18px;
        min-height: 540px;
    }
    @media (max-width: 900px) {
        .subs-body { grid-template-columns: 1fr; }
    }
    .subs-graph {
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 14px;
        min-height: 540px;
        height: 60vh;
    }
    .subs-side {
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 14px;
        padding: 14px 16px;
        align-self: start;
    }
    .subs-side-head {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .subs-side-name { font-size: 1.05rem; }
    .subs-side-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
    .subs-side-sub {
        margin: 14px 0 6px;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-secondary);
    }
    .subs-side-list { list-style: none; margin: 0; padding: 0; }
    .subs-side-list li {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        gap: 6px;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid var(--surface-sunken);
    }
    .subs-side-other {
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .subs-side-note {
        color: var(--text-secondary);
        font-size: 0.78rem;
        text-align: right;
    }
    .subs-side-pair {
        display: flex;
        align-items: center;
        padding: 8px 0;
    }
    .subs-side-pair-name {
        font-weight: 600;
        cursor: pointer;
        color: var(--text-primary);
    }
    .subs-side-pair-name:hover { color: var(--brand-primary); text-decoration: underline; }
    .subs-empty-inline { color: var(--text-secondary); font-size: 0.88rem; padding: 8px 0; }
    .subs-empty {
        margin-top: 16px;
        padding: 18px 22px;
        background: var(--surface-component);
        border: 1px dashed var(--border-strong);
        border-radius: 14px;
        text-align: center;
    }
    .subs-empty-title { font-weight: 600; font-size: 1.05rem; margin: 0 0 4px; }
</style>
