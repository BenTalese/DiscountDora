<template>
    <BaseDialog v-model="cheatsheetOpen" card-style="width: 560px; max-width: 95vw">
            <q-card-section class="row items-center q-pb-none">
                <q-icon :name="ICONS.keyboard" size="24px" class="q-mr-sm" />
                <div class="text-h6">Keyboard shortcuts</div>
                <q-space />
                <q-btn flat dense round :icon="ICONS.close" v-close-popup />
            </q-card-section>

            <q-card-section style="max-height: 70vh; overflow-y: auto">
                <div v-if="shortcuts.length === 0" class="dora-text-muted">
                    No shortcuts are active on this screen.
                </div>
                <div v-for="group in groups" :key="group.scope" class="q-mb-md">
                    <div class="text-subtitle2 dora-text-secondary q-mb-xs">{{ group.scope }}</div>
                    <q-list dense>
                        <q-item v-for="s in group.items" :key="s.keys + s.description">
                            <q-item-section>{{ s.description }}</q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs">
                                    <kbd v-for="(k, i) in keyParts(s.keys)" :key="i" class="shortcut-key">
                                        {{ k }}
                                    </kbd>
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </div>
            </q-card-section>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useShortcutRegistry } from 'src/composables/useShortcut';
    import { computed } from 'vue';

    const { shortcuts, cheatsheetOpen } = useShortcutRegistry();

    // Group by scope, keeping 'Global' first.
    const groups = computed(() => {
        const byScope = new Map<string, typeof shortcuts>();
        for (const s of shortcuts) {
            const list = byScope.get(s.scope) ?? [];
            (list as unknown as typeof s[]).push(s);
            byScope.set(s.scope, list);
        }
        return [...byScope.entries()]
            .map(([scope, items]) => ({ scope, items }))
            .sort((a, b) => {
                if (a.scope === 'Global') return -1;
                if (b.scope === 'Global') return 1;
                return a.scope.localeCompare(b.scope);
            });
    });

    // 'g s' → ['g', 's']; 'space' → ['Space']; '/' → ['/'].
    function keyParts(keys: string): string[] {
        return keys.split(' ').map((k) => {
            if (k === 'space') return 'Space';
            if (k === 'escape') return 'Esc';
            if (k.startsWith('arrow')) return k.replace('arrow', '').replace(/^./, (c) => c.toUpperCase());
            if (k.length === 1) return k.toUpperCase();
            return k;
        });
    }
</script>

<style scoped>
    .shortcut-key {
        display: inline-block;
        min-width: 22px;
        text-align: center;
        padding: 2px 6px;
        border: 1px solid var(--q-grey-5, var(--border-strong));
        border-bottom-width: 2px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.8rem;
        background: var(--overlay-hover);
    }
</style>
