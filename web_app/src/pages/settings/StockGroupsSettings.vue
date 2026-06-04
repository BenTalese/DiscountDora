<template>
    <q-card flat bordered>
        <q-card-section class="row items-center">
            <div>
                <div class="text-h6">Stock groups</div>
                <div class="text-caption dora-text-muted">
                    Tag your stock items so they're easier to filter on the
                    overview. {{ groups.length }} group{{ groups.length === 1 ? '' : 's' }}.
                </div>
            </div>
            <q-space />
            <q-btn
                color="primary"
                no-caps
                :icon="ICONS.add"
                label="New group"
                :loading="creating"
                @click="onCreate"
            />
        </q-card-section>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mx-md q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-separator />

        <q-list separator>
            <q-item v-for="group in groups" :key="group.stock_group_id" class="q-py-sm">
                <q-item-section avatar>
                    <q-icon :name="ICONS.label" />
                </q-item-section>
                <q-item-section>
                    <q-item-label v-if="editingId !== group.stock_group_id">
                        {{ group.name }}
                    </q-item-label>
                    <q-input
                        v-else
                        v-model="renameDraft"
                        dense
                        outlined
                        autofocus
                        @blur="saveRename(group)"
                        @keydown.enter.prevent="saveRename(group)"
                        @keydown.esc.prevent="editingId = null"
                    />
                    <q-item-label caption>
                        {{ group.item_count ?? 0 }} item{{
                            (group.item_count ?? 0) === 1 ? '' : 's'
                        }}
                    </q-item-label>
                </q-item-section>
                <q-item-section side>
                    <div class="row q-gutter-xs">
                        <q-btn
                            flat
                            dense
                            round
                            :icon="ICONS.edit"
                            @click="startRename(group)"
                        >
                            <q-tooltip>Rename</q-tooltip>
                        </q-btn>
                        <q-btn
                            flat
                            dense
                            round
                            :icon="ICONS.delete_outline"
                            @click="onDelete(group)"
                        >
                            <q-tooltip>Delete</q-tooltip>
                        </q-btn>
                    </div>
                </q-item-section>
            </q-item>
            <q-item v-if="!loading && groups.length === 0">
                <q-item-section class="dora-text-muted text-center">
                    No groups yet. Create one to start tagging stock items.
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && groups.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import type { StockGroup } from 'src/models/stockGroup';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import { onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const api = new StockGroupApiService();

    const groups = ref<StockGroup[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const creating = ref(false);

    const editingId = ref<string | null>(null);
    const renameDraft = ref('');

    async function load() {
        loading.value = true;
        loadError.value = null;
        try {
            groups.value = await api.getAllAsync();
        } catch (err) {
            loadError.value = `Could not load: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    async function onCreate() {
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'New stock group',
                message: 'What is this group called? (e.g. "Dairy", "Snacks")',
                prompt: { model: '', type: 'text' },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        creating.value = true;
        try {
            await api.createAsync({ name });
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create.',
                caption: describeApiError(err) || '',
            });
        } finally {
            creating.value = false;
        }
    }

    function startRename(group: StockGroup) {
        editingId.value = group.stock_group_id;
        renameDraft.value = group.name;
    }

    async function saveRename(group: StockGroup) {
        const next = renameDraft.value.trim();
        if (!next || next === group.name) {
            editingId.value = null;
            return;
        }
        try {
            await api.updateAsync(group.stock_group_id, { name: next });
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

    async function onDelete(group: StockGroup) {
        const count = group.item_count ?? 0;
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${group.name}"?`,
                message:
                    count > 0
                        ? `${count} item${
                              count === 1 ? '' : 's'
                          } currently in this group will lose their group tag. The items themselves stay.`
                        : 'Nothing currently uses this group.',
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await api.deleteAsync(group.stock_group_id);
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

    onMounted(load);
</script>
