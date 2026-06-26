<template>
    <div class="page-error-state column items-center justify-center q-pa-xl">
        <q-icon :name="icon" :color="iconColor" size="72px" class="q-mb-md" />
        <div class="text-h5 q-mb-sm text-center">{{ title }}</div>
        <div class="text-body2 dora-text-muted text-center" style="max-width: 480px">
            {{ description }}
        </div>
        <div
            v-if="correlationId"
            class="text-caption dora-text-muted q-mt-sm correlation-id"
        >
            Reference:
            <code>{{ correlationId }}</code>
        </div>
        <div class="q-mt-lg row q-gutter-sm justify-center wrap">
            <BaseButton
                v-if="showReload"
                :icon="ICONS.refresh"
                label="Reload page"
                @click="onReload"
            />
            <BaseButton
                v-if="showDashboard"
                variant="secondary"
                :icon="ICONS.home"
                label="Go to dashboard"
                to="/"
            />
            <!-- Repo is private — the "Report this" button used to
                 pre-fill a GitHub issue with the error + correlation
                 id. With no public issue tracker, the report flow
                 lives wherever the operator has set it up; the
                 button is hidden until that surface exists. -->

        </div>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** Top-line variant. Drives the icon + default copy. */
            variant?: 'render' | 'server' | 'not_found' | 'navigation';
            /** Override the title; otherwise picked from the variant. */
            title?: string;
            description?: string;
            /** Server correlation id (X-Request-Id), if known. */
            correlationId?: string | null;
            /** The underlying Error object, when present — used in the GH
             *  issue body for triage. */
            error?: Error | null;
            showReload?: boolean;
            showDashboard?: boolean;
            showReport?: boolean;
        }>(),
        {
            variant: 'render',
            title: '',
            description: '',
            correlationId: null,
            error: null,
            showReload: true,
            showDashboard: true,
            showReport: true,
        },
    );

    const title = computed(() => {
        if (props.title) return props.title;
        switch (props.variant) {
            case 'not_found':
                return "We couldn't find that page.";
            case 'server':
                return 'The server tripped on its way over.';
            case 'navigation':
                return "We couldn't open that page.";
            case 'render':
            default:
                return 'Something went wrong on this screen.';
        }
    });

    const description = computed(() => {
        if (props.description) return props.description;
        switch (props.variant) {
            case 'not_found':
                return "The link you followed might be stale, or the page may have moved. Head back to the dashboard or use the menu to find what you need.";
            case 'server':
                return "Something on the server didn't respond as expected. The team's been notified — try again, or come back in a few minutes.";
            case 'navigation':
                return "The page failed to load. Reloading usually does the trick.";
            case 'render':
            default:
                return "This screen ran into an unexpected error. Reloading the page is the fastest fix; if it keeps happening, please tell us about it with the reference below.";
        }
    });

    const icon = computed(() => {
        switch (props.variant) {
            case 'not_found':
                return 'travel_explore';
            case 'server':
                return 'cloud_off';
            case 'navigation':
                return 'block';
            case 'render':
            default:
                return 'error_outline';
        }
    });

    const iconColor = computed(() => {
        switch (props.variant) {
            case 'not_found':
                return 'grey-7';
            case 'render':
                return 'negative';
            case 'server':
                return 'warning';
            default:
                return 'grey-7';
        }
    });

    // `reportUrl` retired with the GitHub issues link (repo is now
    // private). If a self-host operator wires up an internal report
    // sink, restore a similar pre-fill helper pointing at it.

    function onReload() {
        if (typeof window !== 'undefined') {
            window.location.reload();
        }
    }
</script>

<style scoped>
    .page-error-state {
        min-height: 60vh;
    }
    .correlation-id code {
        background: var(--overlay-active);
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 0.85em;
    }
</style>
