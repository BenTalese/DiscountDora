<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <q-btn flat round dense :icon="ICONS.arrow_back" @click="goBack" />
            <div class="q-ml-sm col text-caption dora-text-muted">
                Saved list shapes you can drop into a new shop in one click.
                {{ templates.length }} template{{ templates.length === 1 ? '' : 's' }}.
            </div>
            <BaseButton
                variant="primary"
                :icon="ICONS.add"
                label="New template"
                @click="onCreate"
            />
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div v-if="loading && templates.length === 0" class="text-center q-py-xl">
            <AppSpinner size="48px" />
        </div>

        <div v-else-if="templates.length === 0" class="text-center dora-text-muted q-py-xl">
            <q-icon :name="ICONS.bookmarks" size="60px" class="q-mb-sm" />
            <div>
                No templates yet. Create one to capture a recurring shop pattern
                (e.g. "Weekly essentials").
            </div>
        </div>

        <div v-else class="row q-col-gutter-md">
            <div
                v-for="template in templates"
                :key="template.template_id"
                class="col-12 col-sm-6 col-md-4"
            >
                <q-card flat bordered class="template-card">
                    <q-card-section class="row items-start">
                        <div class="col">
                            <div class="text-h6">
                                <span v-if="editingId !== template.template_id">
                                    {{ template.name }}
                                </span>
                                <q-input
                                    v-else
                                    v-model="renameDraft"
                                    dense
                                    outlined
                                    autofocus
                                    @blur="saveRename(template)"
                                    @keydown.enter.prevent="saveRename(template)"
                                    @keydown.esc.prevent="editingId = null"
                                />
                            </div>
                            <div class="text-caption dora-text-muted">
                                {{ template.line_count }} item{{ template.line_count === 1 ? '' : 's' }}
                                · updated {{ formatDate(template.updated_at) }}
                            </div>
                        </div>
                        <q-btn flat round dense :icon="ICONS.more_vert">
                            <q-menu transition-show="jump-down" transition-hide="jump-up">
                                <q-list dense style="min-width: 200px">
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click="onUse(template)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.playlist_add_check" color="primary" />
                                        </q-item-section>
                                        <q-item-section>
                                            <q-item-label>Use template</q-item-label>
                                            <q-item-label caption>Create a new list</q-item-label>
                                        </q-item-section>
                                    </q-item>
                                    <q-separator />
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click="startRename(template)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.edit" />
                                        </q-item-section>
                                        <q-item-section>Rename</q-item-section>
                                    </q-item>
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click="onView(template)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.open_in_new" />
                                        </q-item-section>
                                        <q-item-section>Edit items</q-item-section>
                                    </q-item>
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click="onDelete(template)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon :name="ICONS.delete" color="negative" />
                                        </q-item-section>
                                        <q-item-section class="text-negative">
                                            Delete template
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-card-section>
                </q-card>
            </div>
        </div>

        <!-- Edit-items dialog ──────────────────────────────────────────── -->
        <BaseDialog v-model="editorOpen" :maximized="$q.screen.lt.sm" card-style="min-width: 480px; max-width: 720px; width: 100%">
                <q-card-section class="row items-center q-pb-none">
                    <div class="col">
                        <div class="text-h6">{{ editingDetail?.name ?? 'Loading…' }}</div>
                        <div class="text-caption dora-text-muted">
                            {{ editingDetail?.lines.length ?? 0 }} item{{
                                editingDetail?.lines.length === 1 ? '' : 's'
                            }}
                        </div>
                    </div>
                    <q-btn flat round dense :icon="ICONS.close" v-close-popup />
                </q-card-section>

                <q-separator />

                <q-card-section v-if="editingDetail">
                    <q-select
                        v-model="lineAddSelection"
                        use-input
                        input-debounce="200"
                        :options="addableStockItems"
                        option-value="stock_item_id"
                        option-label="name"
                        emit-value
                        map-options
                        outlined
                        dense
                        clearable
                        label="Add a stock item…"
                        @filter="onLineFilter"
                        @update:model-value="onAddTemplateLine"
                    >
                        <template #no-option>
                            <q-item>
                                <q-item-section class="dora-text-muted">
                                    No matching stock items.
                                </q-item-section>
                            </q-item>
                        </template>
                    </q-select>

                    <q-list bordered separator class="q-mt-md">
                        <q-item
                            v-for="line in editingDetail.lines"
                            :key="line.line_id"
                        >
                            <q-item-section>
                                <q-item-label>{{ line.stock_item_name }}</q-item-label>
                            </q-item-section>
                            <q-item-section side style="min-width: 130px">
                                <div class="row items-center q-gutter-xs no-wrap">
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        size="sm"
                                        :icon="ICONS.remove"
                                        :disable="(line.quantity ?? 0) <= 0"
                                        @click="adjustLineQuantity(line, -1)"
                                    />
                                    <q-input
                                        :model-value="line.quantity ?? ''"
                                        dense
                                        borderless
                                        type="number"
                                        :min="0"
                                        input-class="text-center"
                                        style="width: 48px"
                                        placeholder="—"
                                        @blur="onTemplateQtyBlur(line, $event)"
                                        @keydown.enter.prevent="
                                            ($event.target as HTMLInputElement).blur()
                                        "
                                    />
                                    <q-btn
                                        flat
                                        round
                                        dense
                                        size="sm"
                                        :icon="ICONS.add"
                                        @click="adjustLineQuantity(line, 1)"
                                    />
                                </div>
                            </q-item-section>
                            <q-item-section side>
                                <q-btn
                                    flat
                                    round
                                    dense
                                    :icon="ICONS.delete_outline"
                                    @click="onRemoveLine(line.line_id)"
                                />
                            </q-item-section>
                        </q-item>
                        <q-item v-if="editingDetail.lines.length === 0">
                            <q-item-section class="dora-text-muted text-center">
                                No items on this template yet.
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>

                <q-separator />

                <q-card-actions align="right">
                    <q-btn flat no-caps label="Done" v-close-popup />
                </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useQuasar } from 'quasar';
    import type {
        TemplateDetail,
        TemplateLine,
        TemplateSummary
    } from 'src/models/shoppingListTemplate';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const router = useRouter();
    const api = new ShoppingListTemplateApiService();
    const stockItemStore = useStockItemStore();

    const templates = ref<TemplateSummary[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    const editingId = ref<string | null>(null);
    const renameDraft = ref('');

    const editorOpen = ref(false);
    const editingDetail = ref<TemplateDetail | null>(null);
    const lineAddSelection = ref<string | null>(null);
    const lineFilter = ref('');

    const addableStockItems = computed(() => {
        const existing = new Set(
            (editingDetail.value?.lines ?? []).map((l) => l.stock_item_id)
        );
        const q = lineFilter.value.toLowerCase();
        return stockItemStore.stockItems
            .filter((si) => !existing.has(si.stock_item_id))
            .filter((si) => !q || si.name.toLowerCase().includes(q))
            .map((si) => ({ stock_item_id: si.stock_item_id, name: si.name }));
    });

    function formatDate(iso: string): string {
        try {
            return new Date(iso).toLocaleDateString();
        } catch {
            return iso;
        }
    }

    function goBack() {
        void router.push('/shopping-lists');
    }

    async function load() {
        loading.value = true;
        loadError.value = null;
        try {
            templates.value = await api.getAllAsync();
        } catch (err) {
            loadError.value = `Could not load templates: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    async function onCreate() {
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'New template',
                message: 'What is this template called? (e.g. "Weekly essentials")',
                prompt: { model: '', type: 'text' },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        try {
            const { template_id } = await api.createAsync({ name });
            await load();
            const created = templates.value.find((t) => t.template_id === template_id);
            if (created) await openEditor(created);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create template.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function startRename(template: TemplateSummary) {
        editingId.value = template.template_id;
        renameDraft.value = template.name;
    }

    async function saveRename(template: TemplateSummary) {
        const next = renameDraft.value.trim();
        if (!next || next === template.name) {
            editingId.value = null;
            return;
        }
        try {
            await api.updateAsync(template.template_id, { name: next });
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not rename.',
                caption: describeApiError(err) || '',
            });
        } finally {
            editingId.value = null;
        }
    }

    async function onDelete(template: TemplateSummary) {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${template.name}"?`,
                message: 'This removes the template. Shopping lists previously created from it are unaffected.',
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await api.deleteAsync(template.template_id);
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onUse(template: TemplateSummary) {
        try {
            const result = await api.instantiateAsync(template.template_id, {});
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Created list with ${result.line_count} item${
                    result.line_count === 1 ? '' : 's'
                }.`,
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create list.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onView(template: TemplateSummary) {
        await openEditor(template);
    }

    async function openEditor(template: TemplateSummary) {
        editingDetail.value = null;
        editorOpen.value = true;
        try {
            editingDetail.value = await api.getDetailAsync(template.template_id);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load template.',
                caption: describeApiError(err) || '',
            });
            editorOpen.value = false;
        }
    }

    function onLineFilter(value: string, update: (cb: () => void) => void) {
        update(() => {
            lineFilter.value = value;
        });
    }

    async function onAddTemplateLine(stockItemId: string | null) {
        if (!stockItemId || !editingDetail.value) return;
        lineAddSelection.value = null;
        try {
            await api.addLineAsync(editingDetail.value.template_id, {
                stock_item_id: stockItemId,
            });
            // Reload detail and refresh summary count.
            await Promise.all([
                api.getDetailAsync(editingDetail.value.template_id).then((d) => {
                    editingDetail.value = d;
                }),
                load(),
            ]);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not add item.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function setLineQuantity(line: TemplateLine, next: number | null) {
        if (!editingDetail.value || line.quantity === next) return;
        const previous = line.quantity;
        line.quantity = next;
        try {
            await api.updateLineAsync(editingDetail.value.template_id, line.line_id, {
                quantity: next,
            });
        } catch (err) {
            line.quantity = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update quantity.',
                caption: describeApiError(err) || '',
            });
        }
    }

    async function adjustLineQuantity(line: TemplateLine, delta: number) {
        const current = line.quantity ?? 0;
        await setLineQuantity(line, Math.max(0, current + delta));
    }

    function onTemplateQtyBlur(line: TemplateLine, event: Event) {
        // Mirrors the shopping-list quantity input behaviour: blank ⇒ null,
        // valid integer ⇒ persist, garbage ⇒ revert.
        const target = event.target as HTMLInputElement;
        const raw = target.value.trim();
        if (raw === '') {
            void setLineQuantity(line, null);
            return;
        }
        const parsed = Number.parseInt(raw, 10);
        if (Number.isFinite(parsed) && parsed >= 0) {
            void setLineQuantity(line, parsed);
        } else {
            // Reset the visible value back to the canonical one.
            const current = line.quantity;
            line.quantity = null;
            void Promise.resolve().then(() => {
                line.quantity = current;
            });
        }
    }

    async function onRemoveLine(lineId: string) {
        if (!editingDetail.value) return;
        try {
            await api.deleteLineAsync(editingDetail.value.template_id, lineId);
            await Promise.all([
                api.getDetailAsync(editingDetail.value.template_id).then((d) => {
                    editingDetail.value = d;
                }),
                load(),
            ]);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove item.',
                caption: describeApiError(err) || '',
            });
        }
    }

    onMounted(async () => {
        await load();
        if (stockItemStore.stockItems.length === 0) {
            await stockItemStore.getStockItemsAsync();
        }
    });
</script>

<style scoped>
    .template-card {
        transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .template-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px var(--overlay-active);
    }
</style>
