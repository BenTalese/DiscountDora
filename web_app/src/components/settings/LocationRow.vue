<template>
    <q-item class="q-py-sm" :style="{ paddingLeft: `${16 + depth * 24}px` }">
        <q-item-section avatar style="min-width: 32px">
            <q-btn
                v-if="canHaveChildren"
                flat
                dense
                round
                size="sm"
                :icon="isExpanded ? ICONS.expand_more : ICONS.chevron_right"
                @click="$emit('toggle', node.location_id)"
            />
            <q-icon v-else :name="kindIcon" size="18px" color="grey-6" />
        </q-item-section>

        <q-item-section>
            <q-item-label v-if="editingId !== node.location_id" class="row items-center">
                <q-icon v-if="canHaveChildren" :name="kindIcon" size="16px" class="q-mr-xs" color="grey-7" />
                <span>{{ node.name }}</span>
                <q-chip dense square size="sm" color="grey-3" text-color="grey-8" class="q-ml-sm">
                    {{ node.kind }}
                </q-chip>
            </q-item-label>
            <q-input
                v-else
                :model-value="renameDraft"
                dense
                outlined
                autofocus
                @update:model-value="$emit('update:renameDraft', String($event ?? ''))"
                @blur="$emit('saveRename', node)"
                @keydown.enter.prevent="$emit('saveRename', node)"
                @keydown.esc.prevent="$emit('cancelRename')"
            />
            <q-item-label caption>
                {{ countLabel }}
            </q-item-label>
        </q-item-section>

        <q-item-section side>
            <div class="row q-gutter-xs">
                <q-btn
                    v-if="childKind"
                    flat
                    dense
                    round
                    :icon="ICONS.add"
                    @click="$emit('addChild', node)"
                >
                    <q-tooltip>Add {{ childKind }}</q-tooltip>
                </q-btn>
                <q-btn
                    flat
                    dense
                    round
                    :icon="ICONS.edit"
                    @click="$emit('startRename', node)"
                >
                    <q-tooltip>Rename</q-tooltip>
                </q-btn>
                <q-btn
                    flat
                    dense
                    round
                    :icon="ICONS.delete_outline"
                    @click="$emit('delete', node)"
                >
                    <q-tooltip>Delete</q-tooltip>
                </q-btn>
            </div>
        </q-item-section>
    </q-item>

    <template v-if="isExpanded">
        <LocationRow
            v-for="child in node.children"
            :key="child.location_id"
            :node="child"
            :depth="depth + 1"
            :expanded="expanded"
            :editing-id="editingId"
            :rename-draft="renameDraft"
            @toggle="(id) => $emit('toggle', id)"
            @start-rename="(n) => $emit('startRename', n)"
            @save-rename="(n) => $emit('saveRename', n)"
            @cancel-rename="$emit('cancelRename')"
            @update:rename-draft="(v) => $emit('update:renameDraft', v)"
            @add-child="(n) => $emit('addChild', n)"
            @delete="(n) => $emit('delete', n)"
        />
    </template>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';
    import type { LocationKind, LocationNode } from 'src/models/location';

    const props = defineProps<{
        node: LocationNode;
        depth: number;
        expanded: Set<string>;
        editingId: string | null;
        renameDraft: string;
    }>();

    defineEmits<{
        (e: 'toggle', id: string): void;
        (e: 'startRename', node: LocationNode): void;
        (e: 'saveRename', node: LocationNode): void;
        (e: 'cancelRename'): void;
        (e: 'update:renameDraft', value: string): void;
        (e: 'addChild', parent: LocationNode): void;
        (e: 'delete', node: LocationNode): void;
    }>();

    const isExpanded = computed(() => props.expanded.has(props.node.location_id));
    const canHaveChildren = computed(() => props.node.children.length > 0);

    const childKind = computed<LocationKind | null>(() => {
        if (props.node.kind === 'zone') return 'area';
        if (props.node.kind === 'area') return 'section';
        return null;
    });

    const kindIcon = computed(() => {
        if (props.node.kind === 'zone') return ICONS.place;
        if (props.node.kind === 'area') return ICONS.folder;
        return ICONS.splitscreen;
    });

    const countLabel = computed(() => {
        const direct = props.node.direct_item_count;
        const descendant = props.node.descendant_item_count;
        if (descendant === 0) return 'Empty';
        if (direct === descendant) {
            return `${direct} item${direct === 1 ? '' : 's'}`;
        }
        return `${direct} here · ${descendant} in total`;
    });
</script>
