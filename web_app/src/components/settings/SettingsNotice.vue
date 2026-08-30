<template>
    <!--
        Owner feedback 2026-08-29 (Voice) — *"make the not supported text more
        like a warning card, more obvious"*. The "this can't work here" notes
        were flat muted paragraphs indistinguishable from help text, so the one
        line explaining why a toggle is dead read as decoration.

        `ChannelSetupNote` is the same card with Notifications' specific
        SMTP/VAPID copy baked in; this is the generic one for everywhere else.
        Tone `warning` = something on this device or install can't do the thing;
        `info` = it works, here's a caveat worth knowing.
    -->
    <q-banner
        class="settings-notice"
        :class="tone === 'warning' ? 'dora-bg-warning-soft' : 'dora-bg-info-soft'"
        rounded
    >
        <template #avatar>
            <q-icon
                :name="tone === 'warning' ? ICONS.warning_amber : ICONS.info_outline"
                size="22px"
                :class="tone === 'warning' ? 'text-warning' : 'text-info'"
            />
        </template>

        <div class="settings-notice__body">
            <div v-if="title" class="settings-notice__title">{{ title }}</div>
            <div class="settings-notice__text"><slot /></div>
            <div v-if="$slots.actions" class="settings-notice__actions">
                <slot name="actions" />
            </div>
        </div>
    </q-banner>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';

    withDefaults(
        defineProps<{
            title?: string;
            tone?: 'warning' | 'info';
        }>(),
        { title: '', tone: 'warning' },
    );
</script>

<style scoped lang="scss">
    .settings-notice {
        margin: 4px 0 6px;
    }
    .settings-notice__body {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .settings-notice__title {
        font-weight: 500;
        color: var(--text-primary);
    }
    .settings-notice__text {
        margin: 0;
        color: var(--text-primary);
        font-size: 0.875rem;
        line-height: 1.45;
        max-width: 70ch;
    }
    .settings-notice__actions {
        margin-top: 4px;
    }
</style>
