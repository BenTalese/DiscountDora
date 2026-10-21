<template>
    <!--
        Settings rebuild Phase 4 (§2.9) — the one place "the user" is drawn.
        Shows the uploaded profile picture when present; otherwise a
        per-consumer fallback (the menu-bar keeps the person icon, the
        Account header + admin rows keep initials). The `imgFailed` latch
        drops a broken <img> to the fallback rather than a broken-image glyph
        (mirrors StockItemRow); it resets when the store's image-version
        counter bumps after an upload / clear.
    -->
    <q-avatar
        :size="size"
        :color="showImage ? undefined : color"
        :text-color="showImage ? undefined : textColor"
    >
        <img
            v-if="showImage"
            :src="src"
            :alt="alt"
            @error="imgFailed = true"
        />
        <q-icon
            v-else-if="fallback === 'icon'"
            :name="fallbackIcon"
        />
        <template v-else>{{ initial }}</template>
    </q-avatar>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import { userImageUrl } from 'src/services/api/authApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            userId: string;
            hasImage: boolean;
            size?: string;
            // Per-consumer fallback when there's no picture: the menu-bar
            // button keeps the `person` icon (the feedback explicitly asks to
            // preserve it); larger avatars show initials.
            fallback?: 'icon' | 'initials';
            // Only used when fallback === 'initials'.
            username?: string;
            fallbackIcon?: string;
            // Optional q-avatar styling for the fallback (initials/icon) state.
            // `| undefined` so callers can pass `cond ? 'accent' : undefined`
            // under exactOptionalPropertyTypes (e.g. admin-vs-non-admin rows).
            color?: string | undefined;
            textColor?: string | undefined;
        }>(),
        { size: '32px', fallback: 'icon' },
    );

    const authStore = useAuthStore();
    const imgFailed = ref(false);

    // Reactive cache-buster: any upload / clear bumps the store counter, which
    // both refreshes the URL and clears a stale failure latch.
    const version = computed(() => authStore.imageVersionOf(props.userId));
    watch(version, () => { imgFailed.value = false; });
    // A fresh `hasImage=true` (e.g. another surface uploaded) should also
    // re-attempt the image.
    watch(() => props.hasImage, (has) => { if (has) imgFailed.value = false; });

    const showImage = computed(() => props.hasImage && !imgFailed.value);
    const src = computed(() => userImageUrl(props.userId, version.value));
    const fallbackIcon = computed(() => props.fallbackIcon ?? ICONS.person);
    const alt = computed(() => props.username ?? 'Profile picture');
    const initial = computed(() => {
        const name = props.username ?? '';
        return name.length > 0 ? name.charAt(0).toUpperCase() : '?';
    });
</script>
