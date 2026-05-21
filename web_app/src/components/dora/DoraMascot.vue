<template>
    <div class="dora-mascot" :class="`dora-mood-${mood}`">
        <q-avatar :size="sizePx" square class="dora-mascot-face">
            <img src="../../assets/logo-mascot.png" alt="Dora" />
        </q-avatar>
        <div class="dora-mood-badge" :class="`dora-mood-badge-${mood}`">
            <q-icon :name="moodIcon" size="14px" />
        </div>
    </div>
</template>

<script lang="ts" setup>
    // Mood is intentionally a fixed set rather than freeform — the intent
    // handler maps each reply to one of these so the avatar's expression
    // stays a constrained, predictable signal to the user. The type lives
    // in doraTypes.ts because <script setup> doesn't export named bindings.
    import type { DoraMood } from 'src/components/dora/doraTypes';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{ mood?: DoraMood; size?: number }>(),
        { mood: 'happy', size: 56 }
    );

    const sizePx = computed(() => `${props.size}px`);

    const moodIcon = computed(() => {
        switch (props.mood) {
            case 'thinking':
                return 'psychology';
            case 'confused':
                return 'help_outline';
            case 'excited':
                return 'celebration';
            case 'curious':
                return 'travel_explore';
            default:
                return 'mood';
        }
    });
</script>

<style scoped>
    .dora-mascot {
        position: relative;
        display: inline-flex;
    }
    .dora-mascot-face {
        background: white;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    }
    .dora-mood-badge {
        position: absolute;
        right: -4px;
        bottom: -4px;
        background: white;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
        color: #555;
        transition: color 180ms ease, transform 180ms ease;
    }
    .dora-mood-badge-happy {
        color: var(--q-primary);
    }
    .dora-mood-badge-thinking {
        color: var(--q-secondary);
        transform: scale(0.95);
    }
    .dora-mood-badge-confused {
        color: var(--q-warning);
    }
    .dora-mood-badge-excited {
        color: var(--q-accent);
        transform: scale(1.08);
    }
    .dora-mood-badge-curious {
        color: var(--q-info);
    }
</style>
