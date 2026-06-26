<template>
    <div class="settings-page">
        <SettingsPageHeader :title="title" :description="rolledDescription">
            <template #actions>
                <BaseButton
                    :icon="ICONS.add"
                    :label="`New ${noun}`"
                    :loading="busy"
                    @click="onCreate"
                />
            </template>
        </SettingsPageHeader>

        <q-list class="vocab-list" separator>
            <q-item v-for="(item, index) in items" :key="item.id" class="vocab-list__item">
                <q-item-section avatar>
                    <q-icon :name="ICONS.label" />
                </q-item-section>
                <q-item-section>
                    <q-item-label v-if="editingId !== item.id">{{ item.name }}</q-item-label>
                    <q-input
                        v-else
                        v-model="renameDraft"
                        dense
                        outlined
                        autofocus
                        @blur="saveRename(item)"
                        @keydown.enter.prevent="saveRename(item)"
                        @keydown.esc.prevent="editingId = null"
                    />
                    <q-item-label caption>
                        {{ item.recipe_count ?? 0 }}
                        {{ usageLabel }}{{ (item.recipe_count ?? 0) === 1 ? '' : 's' }}
                    </q-item-label>
                </q-item-section>
                <q-item-section side>
                    <div class="row q-gutter-xs items-center">
                        <template v-if="reorderable">
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.arrow_upward"
                                :disable="index === 0"
                                @click="emit('reorder', item.id, 'up')"
                            >
                                <q-tooltip>Move up</q-tooltip>
                            </BaseButton>
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.arrow_downward"
                                :disable="index === items.length - 1"
                                @click="emit('reorder', item.id, 'down')"
                            >
                                <q-tooltip>Move down</q-tooltip>
                            </BaseButton>
                        </template>
                        <BaseButton variant="icon" :icon="ICONS.edit" @click="startRename(item)">
                            <q-tooltip>Rename</q-tooltip>
                        </BaseButton>
                        <BaseButton variant="icon" :icon="ICONS.delete_outline" @click="onDelete(item)">
                            <q-tooltip>Delete</q-tooltip>
                        </BaseButton>
                    </div>
                </q-item-section>
            </q-item>
            <q-item v-if="!loading && items.length === 0">
                <q-item-section class="dora-text-muted text-center">
                    No {{ nounPlural }} yet. Create one to start tagging recipes.
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && items.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { computed, ref } from 'vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    type VocabItem = { id: string; name: string; recipe_count?: number };

    const props = withDefaults(
        defineProps<{
            title: string;
            description: string;
            noun: string;
            nounPlural: string;
            items: VocabItem[];
            loading: boolean;
            busy: boolean;
            reorderable?: boolean;
            usageLabel?: string;
            preservesLabel?: boolean;
        }>(),
        { reorderable: false, usageLabel: 'recipe', preservesLabel: false },
    );

    const emit = defineEmits<{
        (e: 'create', name: string): void;
        (e: 'rename', id: string, name: string): void;
        (e: 'delete', id: string): void;
        (e: 'reorder', id: string, direction: 'up' | 'down'): void;
    }>();

    const rolledDescription = computed(() => {
        const count = props.items.length;
        const word = count === 1 ? props.noun : props.nounPlural;
        return `${props.description} ${count} ${word}.`;
    });

    const $q = useQuasar();
    const editingId = ref<string | null>(null);
    const renameDraft = ref('');

    async function onCreate() {
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: `New ${props.noun}`,
                message: `What is this ${props.noun} called?`,
                prompt: { model: '', type: 'text' },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (name) emit('create', name);
    }

    function startRename(item: VocabItem) {
        editingId.value = item.id;
        renameDraft.value = item.name;
    }

    function saveRename(item: VocabItem) {
        const next = renameDraft.value.trim();
        editingId.value = null;
        if (next && next !== item.name) emit('rename', item.id, next);
    }

    async function onDelete(item: VocabItem) {
        const count = item.recipe_count ?? 0;
        const plural = count === 1 ? '' : 's';
        const usageMessage = props.preservesLabel
            ? `${count} ${props.usageLabel}${plural} use this ${props.noun}; they'll keep the label.`
            : `${count} ${props.usageLabel}${plural} using this ${props.noun} will lose it. The ${props.usageLabel}s themselves stay.`;
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${item.name}"?`,
                message:
                    count > 0
                        ? usageMessage
                        : `Nothing currently uses this ${props.noun}.`,
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (ok) emit('delete', item.id);
    }
</script>

<style scoped lang="scss">
    .settings-page {
        display: flex;
        flex-direction: column;
        position: relative;
    }
    .vocab-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .vocab-list__item {
        padding: 10px 4px;
    }
</style>
