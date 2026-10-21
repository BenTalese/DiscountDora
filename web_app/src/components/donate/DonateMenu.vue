<template>
    <q-menu
        class="donate-menu"
        :anchor="anchor"
        :self="self"
        transition-show="jump-up"
        transition-hide="jump-down"
    >
        <q-list class="donate-menu__list">
            <q-item
                v-for="platform in DONATION_PLATFORMS"
                :key="platform.label"
                v-close-popup
                clickable
                tag="a"
                :href="platform.url"
                target="_blank"
                rel="noopener noreferrer"
            >
                <q-item-section avatar>
                    <q-icon :name="platform.icon" :style="{ color: 'var(--donate)' }" />
                </q-item-section>
                <q-item-section>{{ platform.label }}</q-item-section>
            </q-item>
        </q-list>
    </q-menu>
</template>

<script lang="ts" setup>
    import type { QMenuProps } from 'quasar';
    import { DONATION_PLATFORMS } from 'src/config/donationLinks';

    // Shared popover listing every donation channel (R-003 — one menu behind
    // all three <DonateButton> placements). Anchor/self are configurable so a
    // toolbar trigger can drop the menu below itself while the bottom-left
    // floating trigger opens it upward.
    withDefaults(
        defineProps<{
            anchor?: QMenuProps['anchor'];
            self?: QMenuProps['self'];
        }>(),
        {
            anchor: 'bottom middle',
            self: 'top middle',
        },
    );
</script>

<style scoped>
    .donate-menu__list {
        padding: 6px 0;
        min-width: 240px;
    }
</style>
