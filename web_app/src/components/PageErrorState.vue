<template>
    <div class="page-error-state column items-center justify-center q-pa-xl">
        <q-icon
            :name="icon"
            :color="iconColor ?? undefined"
            :class="['q-mb-md', { 'dora-text-muted': !iconColor }]"
            size="72px"
        />
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
                @click="onDashboard"
            />
            <!-- FU-370 — pre-fills the configured support channel with the
                 error variant, path, correlation id, and message. Renders
                 only when the caller opts in (`showReport`) AND the operator
                 has configured a channel; dormant installs show nothing. -->
            <BaseButton
                v-if="showReport && hasChannel"
                variant="secondary"
                :icon="ICONS.bug_report"
                label="Report this"
                @click="onReport"
            />
        </div>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import {
        useSupportChannel,
        supportHref,
    } from 'src/composables/useSupportChannel';

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
                return "Something on the server didn't respond as expected. Try again, or come back in a few minutes.";
            case 'navigation':
                return "The page failed to load. Reloading usually does the trick.";
            case 'render':
            default:
                return "This screen ran into an unexpected error. Reloading the page is the fastest fix.";
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

    // R-002: neutral states return null so the template applies
    // `dora-text-muted` rather than a `grey-N` palette literal.
    const iconColor = computed<string | null>(() => {
        switch (props.variant) {
            case 'not_found':
                return null;
            case 'render':
                return 'negative';
            case 'server':
                return 'warning';
            default:
                return null;
        }
    });

    // FU-370 — restores the pre-fill helper the retired `reportUrl` used to
    // carry, now pointing at whatever channel the operator configured (see
    // useSupportChannel). Opens in a new tab (window.open keeps this a
    // BaseButton rather than a raw type="a" anchor).
    const { channel, hasChannel } = useSupportChannel();
    const reportBody = computed(() => {
        const lines = [
            'What I was doing: ',
            '',
            '---',
            `Path: ${route.path}`,
            `Screen: ${props.variant}`,
        ];
        if (props.correlationId) lines.push(`Reference: ${props.correlationId}`);
        if (props.error?.message) lines.push(`Error: ${props.error.message}`);
        return lines.join('\n');
    });
    const reportHref = computed(() =>
        supportHref(channel.value, {
            subject: `[Dora] Error — ${props.variant} on ${route.path}`,
            body: reportBody.value,
        }),
    );
    function onReport() {
        const href = reportHref.value;
        if (href && typeof window !== 'undefined') {
            window.open(href, '_blank', 'noopener');
        }
    }

    function onReload() {
        if (typeof window !== 'undefined') {
            window.location.reload();
        }
    }

    const route = useRoute();
    const router = useRouter();

    function onDashboard() {
        // Router-link no-ops when the target matches the current route, which
        // left the button dead when the error surfaced on the dashboard itself.
        // Reload in that case so the user still gets an escape hatch.
        if (route.path === '/') {
            onReload();
        } else {
            void router.push('/');
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
