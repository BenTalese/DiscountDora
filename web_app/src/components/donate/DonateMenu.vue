<template>
    <q-menu
        class="donate-menu"
        :anchor="anchor"
        :self="self"
        transition-show="jump-up"
        transition-hide="jump-down"
    >
        <div class="donate-menu__head">
            <q-icon :name="ICONS.favorite" size="22px" class="donate-menu__heart" />
            <div class="donate-menu__head-text">
                <div class="donate-menu__title">Support Dora</div>
                <div class="donate-menu__sub">
                    Dora is free &amp; open-source — donations keep her going 💗
                </div>
            </div>
        </div>

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
                <q-item-section side>
                    <q-icon :name="ICONS.open_in_new" size="16px" />
                </q-item-section>
            </q-item>
        </q-list>
    </q-menu>
</template>

<script lang="ts" setup>
    import type { QMenuProps } from 'quasar';
    import { ICONS } from 'src/style/icons';
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
    .donate-menu__head {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 14px 16px 10px;
        max-width: 280px;
    }
    .donate-menu__heart {
        color: var(--donate);
        flex: 0 0 auto;
        margin-top: 2px;
    }
    .donate-menu__title {
        font-weight: 700;
        font-size: 1rem;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .donate-menu__sub {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 2px;
    }
    .donate-menu__list {
        padding-bottom: 6px;
        min-width: 240px;
    }
</style>
