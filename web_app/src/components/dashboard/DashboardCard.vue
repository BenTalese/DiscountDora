<template>
    <!-- The shared dashboard card shell (R-001 — extracted from DashboardPage so
         each card is composed, not inlined). Renders as a real <router-link>
         when `to` is set (the whole card is one keyboard-focusable control) or a
         plain <article> otherwise. The header is icon + title + an optional
         `#action` slot (a link/text/control on the right); the body is the
         default slot. Card BODY styling stays in the parent page — slotted
         content keeps the parent's scope — so this component only owns the
         shell chrome. -->
    <component
        :is="to ? 'router-link' : 'article'"
        class="dora-card"
        :class="{ 'dora-card-clickable': !!to }"
        v-bind="to ? { to } : {}"
    >
        <header class="dora-card-head">
            <q-icon v-if="icon" :name="icon" size="22px" class="dora-card-icon" />
            <h3 class="dora-card-title"><slot name="title">{{ title }}</slot></h3>
            <slot name="action" />
        </header>
        <slot />
    </component>
</template>

<script lang="ts" setup>
    // `to` (a route path) turns the whole card into a router-link. `title` is
    // the common case; pass the `#title` slot instead for a rich title (e.g. a
    // trailing count). `#action` is the header's right-side content.
    defineProps<{
        icon?: string;
        title?: string;
        to?: string;
    }>();
</script>

<style scoped lang="scss">
    /* Self-contained: references the GLOBAL theme tokens directly (not the
       dashboard page's private `--c-*` aliases), so the shell is correct even
       though scoped styles don't inherit the page's custom-property aliases. */
    .dora-card {
        /* `display:block` + inherit/none let a clickable card render as a real
           <router-link> (an <a>) without inline-anchor layout or link chrome —
           the whole card is one keyboard-focusable, middle-clickable control
           (R-011, a11y). Harmless on the non-clickable <article> cards. */
        display: block;
        color: inherit;
        text-decoration: none;
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-radius: 18px;
        padding: 18px 20px 20px;
        height: 100%;
        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease;
        box-shadow: var(--elevation-card);
    }
    .dora-card-clickable {
        cursor: pointer;
    }
    .dora-card-clickable:hover {
        transform: translateY(-2px);
        box-shadow: var(--elevation-card-hover);
        border-color: var(--border-strong);
    }
    .dora-card-head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
    }
    .dora-card-icon {
        color: var(--brand-primary);
    }
    .dora-card-title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        flex: 1;
        letter-spacing: 0.005em;
    }
    /* `:deep` because the `#action` slot content (defined in the parent) carries
       the parent's scope, not this component's — the shell still owns the
       action's resting/hover look so it's consistent across every card. */
    :deep(.dora-card-action) {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
        opacity: 0.85;
        transition: color 0.18s ease, opacity 0.18s ease;
    }
    .dora-card-clickable:hover :deep(.dora-card-action) {
        color: var(--brand-primary);
        opacity: 1;
    }
    :deep(.dora-card-link) {
        color: var(--brand-primary);
        text-decoration: none;
        font-weight: 600;
    }
    :deep(.dora-card-link:hover) {
        text-decoration: underline;
    }

    /* Respect reduced motion (the parent page's media query can't reach these
       extracted elements). */
    @media (prefers-reduced-motion: reduce) {
        .dora-card {
            transition: none !important;
        }
        .dora-card-clickable:hover {
            transform: none !important;
        }
        :deep(.dora-card-action) {
            transition: none !important;
        }
    }
</style>
