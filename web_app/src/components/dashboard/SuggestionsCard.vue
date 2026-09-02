<template>
    <DashboardCard :icon="ICONS.dora_voice" title="Dora suggests">
        <template #action>
            <span v-if="count > SHOWN" class="dora-card-action">
                +{{ count - SHOWN }} more in chat
            </span>
        </template>
        <!-- Calm empty state instead of vanishing when Dora has nothing to
             suggest — R-014's inversion, and a separate pattern from R-029
             (hide-when-off): a happy zero isn't an opt-out. -->
        <div v-if="count === 0" class="dora-empty dora-empty-ok">
            <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
            Nothing to suggest right now — you're on top of things.
        </div>
        <div v-else class="dora-suggest-list">
            <div
                v-for="suggestion in suggestions.slice(0, SHOWN)"
                :key="`${suggestion.kind}:${suggestion.dedup_key}`"
                class="dora-suggest-row"
                :class="`dora-suggest-${suggestion.severity}`"
            >
                <div class="dora-suggest-title">{{ suggestion.title }}</div>
                <div class="dora-suggest-body">{{ suggestion.body }}</div>
                <div class="row q-gutter-xs q-mt-xs">
                    <BaseButton
                        v-if="suggestion.primary_action"
                        variant="primary"
                        dense
                        size="sm"
                        :label="suggestion.primary_action.label"
                        @click="emit('accept', suggestion)"
                    />
                    <BaseButton
                        variant="ghost"
                        dense
                        size="sm"
                        label="Dismiss"
                        @click="emit('dismiss', suggestion)"
                    />
                </div>
            </div>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * A peek at Dora's top suggestions, with the rest in chat.
     *
     * The store is shared with the Dora launcher badge and the chat panel, so a
     * dismiss or snooze here propagates everywhere — which is why the page hands
     * the list down and takes the verbs back rather than this component talking
     * to the store directly.
     *
     * Extracted from `DashboardPage.vue` (FU-829).
     */
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import type { DoraSuggestion } from 'src/services/api/suggestionsApiService';

    defineProps<{
        /** `readonly` because the store exposes its list as such — the card only
         *  ever reads and slices it. */
        suggestions: readonly DoraSuggestion[];
        /** Total available, which can exceed what's shown. */
        count: number;
    }>();

    const emit = defineEmits<{
        (e: 'accept', suggestion: DoraSuggestion): void;
        (e: 'dismiss', suggestion: DoraSuggestion): void;
    }>();

    /** How many fit on a card before "more in chat" earns its place. */
    const SHOWN = 2;
</script>

<style scoped lang="scss">
    /* P2-04 — suggestion rows. Severity drives the left border; the rest of the
       visual weight is on the title and the primary action. Moved with the card
       (R-027) and off the page's `--c-*` aliases (R-060). */
    .dora-suggest-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-suggest-row {
        padding: 8px 10px;
        border-radius: 10px;
        background: var(--surface-elevated);
        border-left: 3px solid var(--brand-primary);
    }
    .dora-suggest-row.dora-suggest-high { border-left-color: var(--semantic-negative); }
    .dora-suggest-row.dora-suggest-medium { border-left-color: var(--semantic-warning); }
    .dora-suggest-row.dora-suggest-low { border-left-color: var(--brand-primary); }
    .dora-suggest-title {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .dora-suggest-body {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 2px;
    }
</style>
