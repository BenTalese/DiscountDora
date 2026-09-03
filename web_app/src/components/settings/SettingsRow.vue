<template>
    <div
        class="settings-row"
        :class="{ 'settings-row--stacked': stacked, 'settings-row--inline': inline }"
    >
        <div class="settings-row__info">
            <div v-if="label || $slots.label" class="settings-row__label">
                <slot name="label">{{ label }}</slot>
            </div>
            <div v-if="help || $slots.help" class="settings-row__help">
                <slot name="help">{{ help }}</slot>
            </div>
        </div>
        <div class="settings-row__control">
            <slot />
        </div>
    </div>
</template>

<script setup lang="ts">
    // IMPL_PLAN_SETTINGS_REBUILD §2.5 — single row inside a SettingsSection:
    // left = label + optional one-line help; right = control. Collapses to
    // label-above-control on narrow viewports (Phase 5 verifies).
    defineProps<{
        label?: string;
        help?: string;
        /** Force label-above-control at every width. */
        stacked?: boolean;
        /**
         * Keep the control on the right at every width, including mobile.
         * For narrow controls (a toggle, a short select) the automatic mobile
         * stack wastes a whole line and reads as a list of orphaned switches —
         * owner feedback 2026-09-03. Rows holding a wide control (a text input)
         * still want the stack, so this stays opt-in rather than the default.
         */
        inline?: boolean;
    }>();
</script>

<style scoped lang="scss">
    .settings-row {
        display: flex;
        /* Owner feedback 2026-08-29 — *"the toggles don't seem to be inline
           with the option text. Seems to be a broader issue across the board
           in the settings area."* They weren't: a q-toggle's box is ~40px tall
           against an ~18px label line, so top-aligning the two put the toggle's
           track a full 11px below the label it belongs to — on every row of
           every settings page. Centre against the info block instead, which is
           exact for the one-line rows (the common case) and reads correctly
           when a `help` line is present too. D-018 — alignment is consistent
           within a surface, and this is the surface's own primitive, so the
           fix belongs here rather than on any one page. */
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 6px 0;
    }
    .settings-row__info {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .settings-row__label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.3;
    }
    .settings-row__help {
        font-size: 0.8125rem;
        color: var(--text-secondary);
        line-height: 1.35;
    }
    .settings-row__control {
        flex: 0 0 auto;
        min-width: 0;
        max-width: 60%;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .settings-row--stacked,
    .settings-row--stacked.settings-row {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }
    .settings-row--stacked .settings-row__control {
        max-width: 100%;
        width: 100%;
    }

    @media (max-width: 599px) {
        .settings-row:not(.settings-row--inline) {
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
        }
        .settings-row:not(.settings-row--inline) .settings-row__control {
            max-width: 100%;
            width: 100%;
        }
        /* Inline rows keep the two-column shape; the gap tightens so a long
           label still gets most of the width. */
        .settings-row--inline {
            gap: 12px;
        }
        .settings-row--inline .settings-row__control {
            max-width: 55%;
        }
    }
</style>
