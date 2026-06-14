<template>
    <!--
        C-4 Chunk 2 — generic name-only vocabulary editor (cuisine, category).
        Owns the list + create/rename/delete dialogs; the parent supplies the
        items and the api calls via events, then refetches. Dietary tags have
        an extra grouping field and are edited separately.
    -->
    <q-card flat bordered>
        <q-card-section class="row items-center">
            <div>
                <div class="text-h6">{{ title }}</div>
                <div class="text-caption dora-text-muted">
                    {{ description }} {{ items.length }} {{ items.length === 1 ? noun : nounPlural }}.
                </div>
            </div>
            <q-space />
            <q-btn
                color="primary"
                no-caps
                :icon="ICONS.add"
                :label="`New ${noun}`"
                :loading="busy"
                @click="onCreate"
            />
        </q-card-section>

        <q-separator />

        <q-list separator>
            <q-item v-for="(item, index) in items" :key="item.id" class="q-py-sm">
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
                        <!-- C-2.A — optional reorder affordance (slot order is
                             user-facing). Opt-in via `reorderable`; the other
                             vocab cards omit it and are unchanged. -->
                        <template v-if="reorderable">
                            <q-btn
                                flat
                                dense
                                round
                                :icon="ICONS.arrow_upward"
                                :disable="index === 0"
                                @click="emit('reorder', item.id, 'up')"
                            >
                                <q-tooltip>Move up</q-tooltip>
                            </q-btn>
                            <q-btn
                                flat
                                dense
                                round
                                :icon="ICONS.arrow_downward"
                                :disable="index === items.length - 1"
                                @click="emit('reorder', item.id, 'down')"
                            >
                                <q-tooltip>Move down</q-tooltip>
                            </q-btn>
                        </template>
                        <q-btn flat dense round :icon="ICONS.edit" @click="startRename(item)">
                            <q-tooltip>Rename</q-tooltip>
                        </q-btn>
                        <q-btn flat dense round :icon="ICONS.delete_outline" @click="onDelete(item)">
                            <q-tooltip>Delete</q-tooltip>
                        </q-btn>
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
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { ref } from 'vue';

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
            // C-2.A — opt in to the up/down reorder controls (meal slots).
            reorderable?: boolean;
            // What uses an item (for the count caption + delete warning). FK
            // vocabs use the default "recipe"; meal slots are free-text labels
            // on entries, so they pass "entry" + `preservesLabel`.
            usageLabel?: string;
            // When true the delete warning says usages keep their label (slots,
            // no FK) rather than the FK-nulled "the recipes themselves stay".
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
