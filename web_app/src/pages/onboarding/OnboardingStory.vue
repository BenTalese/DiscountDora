<template>
    <div class="story">
        <!-- Persistent escape: skip the whole wizard. -->
        <div class="story-top">
            <BaseButton
                variant="ghost"
                class="dora-text-secondary"
                :icon="ICONS.skip_next"
                label="Skip"
                @click="emit('skip')"
            />
        </div>

        <div class="story-stage">
            <transition name="scene-fade" mode="out-in">
                <OnboardingScene
                    :key="currentScene.id"
                    :kicker="currentScene.kicker"
                    :headline="currentScene.headline"
                    :sub="currentScene.sub"
                >
                    <!-- Scene 2: the hero loop. -->
                    <OnboardingLoop
                        v-if="currentScene.visual === 'loop'"
                        :persona="persona"
                        @update:persona="emit('update:persona', $event)"
                    />

                    <!-- Scene 1: the problem — scattered, dim domain glyphs. -->
                    <div
                        v-else-if="currentScene.visual === 'problem'"
                        class="story-glyph story-glyph--scatter"
                        aria-hidden="true"
                    >
                        <q-icon :name="ICONS.inventory_2" class="g g--a" />
                        <q-icon :name="ICONS.shopping_cart" class="g g--b" />
                        <q-icon :name="ICONS.receipt_long" class="g g--c" />
                        <q-icon :name="ICONS.help_outline" class="g g--q" />
                    </div>

                    <!-- Scene 3: Dora the brain. -->
                    <div
                        v-else-if="currentScene.visual === 'brain'"
                        class="story-glyph"
                    >
                        <DoraMascot mood="thinking" :size="132" />
                    </div>

                    <!-- Scene 4: you're in control — persona teaser. -->
                    <div
                        v-else
                        class="story-glyph story-glyph--control"
                        aria-hidden="true"
                    >
                        <q-icon :name="ICONS.tune" class="g g--big" />
                        <div class="story-pills">
                            <span class="story-pill">Cooking</span>
                            <span class="story-pill">Spend</span>
                            <span class="story-pill">Everything</span>
                        </div>
                    </div>
                </OnboardingScene>
            </transition>
        </div>

        <!-- Scene nav. The shared step rail (in the wizard) is the non-linear
             map; these are the in-scene forward/back + the jump to setup. -->
        <div class="story-nav">
            <BaseButton
                variant="ghost"
                :icon="ICONS.arrow_back"
                label="Back"
                :disable="sceneIndex === 0"
                @click="back"
            />
            <q-space />
            <BaseButton
                v-if="!isLast"
                variant="ghost"
                class="dora-text-secondary"
                label="Skip to setup"
                :icon-right="ICONS.east"
                @click="emit('enter-setup')"
            />
            <BaseButton
                variant="primary"
                :label="isLast ? 'Set up in about a minute' : 'Next'"
                :icon-right="isLast ? ICONS.east : ICONS.arrow_forward"
                @click="next"
            />
        </div>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import OnboardingLoop from 'src/components/onboarding/OnboardingLoop.vue';
    import OnboardingScene from 'src/components/onboarding/OnboardingScene.vue';
    import { useReducedMotion } from 'src/composables/useReducedMotion';
    import {
        NARRATIVE_SCENES,
        type PersonaPreviewKey,
    } from 'src/pages/onboarding/onboardingContent';
    import { ICONS } from 'src/style/icons';
    import { computed, onBeforeUnmount, watch } from 'vue';

    const props = defineProps<{
        /** Current scene (v-model) so the shared rail can jump non-linearly. */
        sceneIndex: number;
        /** Previewed persona (v-model) — remembered for the C-5.3 fork. */
        persona: PersonaPreviewKey;
    }>();
    const emit = defineEmits<{
        'update:sceneIndex': [number];
        'update:persona': [PersonaPreviewKey];
        'enter-setup': [];
        skip: [];
    }>();

    const prefersReducedMotion = useReducedMotion();

    const currentScene = computed(
        () => NARRATIVE_SCENES[props.sceneIndex] ?? NARRATIVE_SCENES[0]!,
    );
    const isLast = computed(() => props.sceneIndex >= NARRATIVE_SCENES.length - 1);

    // Going Back (or any reverse review) stops autoplay so we never yank the
    // user forward while they're re-reading. Forward Next keeps it flowing.
    let autoCancelled = false;

    function go(index: number) {
        const clamped = Math.min(Math.max(index, 0), NARRATIVE_SCENES.length - 1);
        emit('update:sceneIndex', clamped);
    }
    function next() {
        if (isLast.value) {
            emit('enter-setup');
            return;
        }
        go(props.sceneIndex + 1);
    }
    function back() {
        autoCancelled = true;
        go(props.sceneIndex - 1);
    }

    // Auto-advance: arm a timer for scenes that opt in, unless the user asked
    // for reduced motion or has taken manual control. The hero loop scene has
    // autoAdvanceMs = null, so autoplay naturally pauses there for exploration.
    let advanceTimer: ReturnType<typeof setTimeout> | null = null;
    function clearTimer() {
        if (advanceTimer !== null) {
            clearTimeout(advanceTimer);
            advanceTimer = null;
        }
    }
    function arm() {
        clearTimer();
        if (prefersReducedMotion.value || autoCancelled || isLast.value) return;
        const ms = currentScene.value.autoAdvanceMs;
        if (ms === null) return;
        advanceTimer = setTimeout(() => go(props.sceneIndex + 1), ms);
    }

    watch(() => props.sceneIndex, arm, { immediate: true });
    onBeforeUnmount(clearTimer);
</script>

<style scoped>
    .story {
        display: flex;
        flex-direction: column;
        min-height: min(78vh, 640px);
        gap: var(--space-4);
    }
    .story-top {
        display: flex;
        justify-content: flex-end;
    }
    .story-stage {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--space-4) 0;
    }
    .story-nav {
        display: flex;
        align-items: center;
        gap: var(--space-2);
    }

    /* ── Scene glyphs ──────────────────────────────────────────────── */
    .story-glyph {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: clamp(160px, 32vh, 260px);
    }
    .story-glyph--scatter {
        position: relative;
        width: clamp(200px, 50vw, 280px);
    }
    .story-glyph--scatter .g {
        position: absolute;
        color: var(--text-muted);
        opacity: 0.6;
    }
    .story-glyph--scatter .g--a {
        font-size: 56px;
        left: 4%;
        top: 8%;
    }
    .story-glyph--scatter .g--b {
        font-size: 48px;
        right: 6%;
        top: 22%;
    }
    .story-glyph--scatter .g--c {
        font-size: 44px;
        left: 22%;
        bottom: 6%;
    }
    .story-glyph--scatter .g--q {
        font-size: 88px;
        left: 50%;
        top: 46%;
        transform: translate(-50%, -50%);
        color: var(--brand-accent);
        opacity: 0.95;
    }
    .story-glyph--control {
        flex-direction: column;
        gap: var(--space-4);
    }
    .story-glyph--control .g--big {
        font-size: 84px;
        color: var(--brand-primary);
    }
    .story-pills {
        display: flex;
        gap: var(--space-2);
        flex-wrap: wrap;
        justify-content: center;
    }
    .story-pill {
        padding: 4px var(--space-3);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-pill);
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-secondary);
        background: var(--surface-component);
    }

    /* ── Scene cross-fade ──────────────────────────────────────────── */
    .scene-fade-enter-active {
        transition: opacity var(--motion-slow) var(--motion-ease-out),
            transform var(--motion-slow) var(--motion-ease-out);
    }
    .scene-fade-leave-active {
        transition: opacity var(--motion-normal) var(--motion-ease-in),
            transform var(--motion-normal) var(--motion-ease-in);
    }
    .scene-fade-enter-from {
        opacity: 0;
        transform: translateY(var(--motion-slide-distance));
    }
    .scene-fade-leave-to {
        opacity: 0;
        transform: translateY(calc(-1 * var(--motion-slide-distance)));
    }
</style>
