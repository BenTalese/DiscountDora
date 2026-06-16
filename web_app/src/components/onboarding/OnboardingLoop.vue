<template>
    <div
        class="loop"
        :class="{ 'loop--revealing': !nodesShown }"
        role="group"
        :aria-label="`The Dora loop: ${stageLabels}, with Dora at the centre`"
    >
        <!-- The ring + nodes. Square, scales with width; nodes sit on the ring. -->
        <div class="loop-ring">
            <svg class="loop-ring-line" viewBox="0 0 100 100" aria-hidden="true">
                <circle
                    class="loop-ring-circle"
                    :class="{ 'is-drawing': shouldAnimate }"
                    cx="50"
                    cy="50"
                    r="38"
                    pathLength="1"
                />
            </svg>

            <!-- Stage nodes -->
            <button
                v-for="(stage, i) in LOOP_STAGES"
                :key="stage.key"
                type="button"
                class="loop-node"
                :class="{ 'is-shown': nodesShown, 'is-active': focusedKey === stage.key }"
                :style="nodeStyle(i)"
                :disabled="!interactive"
                :aria-pressed="focusedKey === stage.key"
                :aria-label="`${stage.label}. ${stage.sell}`"
                @click="focus(stage.key)"
            >
                <q-icon :name="stage.icon" class="loop-node-icon" />
                <span class="loop-node-label">{{ stage.label }}</span>
            </button>

            <!-- Dora at the centre + the provisional Insight candidate -->
            <div class="loop-centre" :class="{ 'is-shown': nodesShown }">
                <button
                    type="button"
                    class="loop-dora"
                    :class="{ 'is-active': focusedKey === 'centre' }"
                    :disabled="!interactive"
                    :aria-pressed="focusedKey === 'centre'"
                    :aria-label="`${LOOP_CENTRE.label}. ${activePreview.centreSell}`"
                    @click="focus('centre')"
                >
                    <DoraMascot :mood="doraMood" :size="64" />
                </button>

                <transition name="dora-fade">
                    <button
                        v-if="activePreview.insight"
                        type="button"
                        class="loop-insight"
                        :class="{ 'is-active': focusedKey === 'insight' }"
                        :disabled="!interactive"
                        :aria-pressed="focusedKey === 'insight'"
                        :aria-label="`${LOOP_INSIGHT.label} (${LOOP_INSIGHT.comingNote}). ${LOOP_INSIGHT.sell}`"
                        @click="focus('insight')"
                    >
                        <q-icon :name="LOOP_INSIGHT.icon" size="16px" />
                        <span>{{ LOOP_INSIGHT.label }}</span>
                        <span class="loop-insight-tag">soon</span>
                    </button>
                </transition>
            </div>
        </div>

        <!-- Detail panel — what the focused stage does. Announced politely. -->
        <div class="loop-detail" role="status" aria-live="polite">
            <template v-if="focusedKey">
                <div class="loop-detail-title">{{ detail.title }}</div>
                <p class="loop-detail-body">{{ detail.body }}</p>
                <p v-if="detail.note" class="loop-detail-note">{{ detail.note }}</p>
            </template>
            <p v-else class="loop-detail-hint">
                Tap a stage — or Dora in the middle — to see how it works.
            </p>
        </div>

        <!-- Persona preview — illustrative only (no flags set here; that's C-5.3). -->
        <div
            v-if="revealed && interactive"
            class="loop-personas"
            role="radiogroup"
            aria-label="Preview how Dora shapes for each persona"
        >
            <span class="loop-personas-label">Preview&nbsp;for</span>
            <button
                v-for="preview in PERSONA_PREVIEWS"
                :key="preview.key"
                type="button"
                class="loop-persona"
                :class="{ 'is-selected': preview.key === localPersona }"
                role="radio"
                :aria-checked="preview.key === localPersona"
                @click="selectPersona(preview.key)"
            >
                {{ preview.label }}
            </button>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import type { DoraMood } from 'src/components/dora/doraTypes';
    import { useReducedMotion } from 'src/composables/useReducedMotion';
    import {
        DEFAULT_PERSONA_PREVIEW,
        LOOP_CENTRE,
        LOOP_INSIGHT,
        LOOP_STAGES,
        PERSONA_PREVIEWS,
        type LoopStageKey,
        type PersonaPreviewKey,
    } from 'src/pages/onboarding/onboardingContent';
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** Selected persona preview (v-model). */
            persona?: PersonaPreviewKey;
            /** Play the one-time draw-in reveal. Finish-step recap passes false. */
            autoplay?: boolean;
            /** Allow tapping stages / switching persona. */
            interactive?: boolean;
        }>(),
        { persona: DEFAULT_PERSONA_PREVIEW, autoplay: true, interactive: true },
    );
    const emit = defineEmits<{ 'update:persona': [PersonaPreviewKey] }>();

    const prefersReducedMotion = useReducedMotion();

    // Animate only when we're allowed to AND the user hasn't asked for less
    // motion. Otherwise we jump straight to the final, fully-revealed state.
    const shouldAnimate = computed(
        () => props.autoplay && props.interactive && !prefersReducedMotion.value,
    );

    const nodesShown = ref(!shouldAnimate.value);
    const revealed = ref(!shouldAnimate.value);
    const focusedKey = ref<LoopStageKey | 'centre' | 'insight' | null>(null);

    const localPersona = ref<PersonaPreviewKey>(props.persona);
    watch(
        () => props.persona,
        (next) => {
            localPersona.value = next;
        },
    );
    const activePreview = computed(
        () =>
            PERSONA_PREVIEWS.find((p) => p.key === localPersona.value) ??
            PERSONA_PREVIEWS[PERSONA_PREVIEWS.length - 1]!,
    );

    const stageLabels = computed(() => LOOP_STAGES.map((s) => s.label).join(' → '));

    const doraMood = computed<DoraMood>(() =>
        focusedKey.value === 'insight' ? 'lightbulb' : 'happy',
    );

    // Place each stage node on the ring: start at top (−90°), step clockwise.
    const RING_RADIUS = 38; // % offset from centre — matches the SVG circle r.
    function nodeStyle(index: number) {
        const angle = (-90 + index * (360 / LOOP_STAGES.length)) * (Math.PI / 180);
        const left = 50 + RING_RADIUS * Math.cos(angle);
        const top = 50 + RING_RADIUS * Math.sin(angle);
        return {
            left: `${left}%`,
            top: `${top}%`,
            // Stagger the cascade-in once the ring has drawn.
            transitionDelay: nodesShown.value ? '0ms' : `${index * 90}ms`,
        };
    }

    const detail = computed(() => {
        const key = focusedKey.value;
        if (key === 'centre') {
            return { title: LOOP_CENTRE.label, body: activePreview.value.centreSell, note: '' };
        }
        if (key === 'insight') {
            return { title: LOOP_INSIGHT.label, body: LOOP_INSIGHT.sell, note: LOOP_INSIGHT.comingNote };
        }
        const stage = LOOP_STAGES.find((s) => s.key === key);
        return stage
            ? { title: stage.label, body: stage.sell, note: '' }
            : { title: '', body: '', note: '' };
    });

    function focus(key: LoopStageKey | 'centre' | 'insight') {
        if (!props.interactive) return;
        focusedKey.value = key;
    }

    function selectPersona(key: PersonaPreviewKey) {
        localPersona.value = key;
        emit('update:persona', key);
        // If the user was reading the centre/insight copy, keep it in sync.
        if (focusedKey.value === 'insight' && !activePreview.value.insight) {
            focusedKey.value = 'centre';
        }
    }

    // Reveal choreography: the ring draws, then the nodes cascade in, then the
    // persona control appears. Pure setTimeout so reduced-motion can skip it.
    const RING_DRAW_MS = 900;
    const STAGGER_TOTAL_MS = LOOP_STAGES.length * 90 + 260;
    let nodeTimer: ReturnType<typeof setTimeout> | null = null;
    let revealTimer: ReturnType<typeof setTimeout> | null = null;

    onMounted(() => {
        if (!shouldAnimate.value) return;
        nodeTimer = setTimeout(() => {
            nodesShown.value = true;
        }, RING_DRAW_MS);
        revealTimer = setTimeout(() => {
            revealed.value = true;
        }, RING_DRAW_MS + STAGGER_TOTAL_MS);
    });

    onBeforeUnmount(() => {
        if (nodeTimer !== null) clearTimeout(nodeTimer);
        if (revealTimer !== null) clearTimeout(revealTimer);
    });
</script>

<style scoped>
    .loop {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-5);
        width: 100%;
    }

    /* ── Ring + nodes ──────────────────────────────────────────────── */
    .loop-ring {
        position: relative;
        width: clamp(280px, 72vw, 440px);
        aspect-ratio: 1;
    }

    .loop-ring-line {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
    }
    .loop-ring-circle {
        fill: none;
        stroke: var(--brand-accent);
        stroke-width: 0.7;
        opacity: 0.55;
    }
    .loop-ring-circle.is-drawing {
        stroke-dasharray: 1;
        stroke-dashoffset: 1;
        animation: ring-draw var(--motion-slow) var(--motion-ease-out) forwards;
        /* Start the draw after a beat so it reads as deliberate. */
        animation-delay: 120ms;
    }
    @keyframes ring-draw {
        to {
            stroke-dashoffset: 0;
        }
    }

    .loop-node {
        position: absolute;
        transform: translate(-50%, -50%) scale(var(--motion-scale-from));
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        width: 76px;
        padding: var(--space-2) var(--space-1);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg);
        background: var(--surface-component);
        color: var(--text-secondary);
        cursor: pointer;
        opacity: 0;
        transition: opacity var(--motion-normal) var(--motion-ease-out),
            transform var(--motion-normal) var(--motion-ease-spring),
            border-color var(--motion-fast) var(--motion-ease),
            color var(--motion-fast) var(--motion-ease),
            box-shadow var(--motion-fast) var(--motion-ease);
    }
    .loop-node.is-shown {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }
    .loop-node:hover:not(:disabled),
    .loop-node:focus-visible {
        border-color: var(--brand-primary);
        color: var(--text-primary);
        outline: none;
    }
    .loop-node.is-active {
        border-color: var(--brand-accent);
        color: var(--text-primary);
        box-shadow: 0 0 0 2px var(--brand-accent-soft),
            0 6px 18px var(--overlay-active);
    }
    .loop-node-icon {
        font-size: 22px;
        color: var(--brand-primary);
    }
    .loop-node-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* ── Centre: Dora + the provisional Insight candidate ──────────── */
    .loop-centre {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-2);
        opacity: 0;
        transition: opacity var(--motion-slow) var(--motion-ease-out);
    }
    .loop-centre.is-shown {
        opacity: 1;
    }
    .loop-dora {
        border: none;
        background: transparent;
        padding: var(--space-1);
        border-radius: var(--radius-full);
        cursor: pointer;
        line-height: 0;
        transition: box-shadow var(--motion-fast) var(--motion-ease);
    }
    .loop-dora:focus-visible {
        outline: none;
    }
    .loop-dora.is-active,
    .loop-dora:focus-visible {
        box-shadow: 0 0 0 3px var(--brand-accent-soft);
    }
    .loop-insight {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px var(--space-2);
        border: 1px dashed var(--brand-accent);
        border-radius: var(--radius-pill);
        background: var(--surface-elevated);
        color: var(--text-secondary);
        font-size: 0.7rem;
        font-weight: 600;
        cursor: pointer;
    }
    .loop-insight.is-active,
    .loop-insight:focus-visible {
        outline: none;
        box-shadow: 0 0 0 2px var(--brand-accent-soft);
    }
    .loop-insight-tag {
        text-transform: uppercase;
        font-size: 0.58rem;
        letter-spacing: 0.04em;
        opacity: 0.7;
    }

    /* ── Detail panel ──────────────────────────────────────────────── */
    .loop-detail {
        min-height: 4.5em;
        max-width: 30rem;
        text-align: center;
    }
    .loop-detail-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--brand-primary);
    }
    .loop-detail-body {
        margin: 4px 0 0;
        font-size: 1.02rem;
        line-height: 1.4;
        color: var(--text-primary);
    }
    .loop-detail-note {
        margin: 4px 0 0;
        font-size: 0.8rem;
        font-style: italic;
        color: var(--text-muted);
    }
    .loop-detail-hint {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-muted);
    }

    /* ── Persona preview control ───────────────────────────────────── */
    .loop-personas {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        padding: 4px;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-pill);
        background: var(--surface-component);
        flex-wrap: wrap;
        justify-content: center;
    }
    .loop-personas-label {
        font-size: 0.72rem;
        color: var(--text-muted);
        padding: 0 var(--space-2);
    }
    .loop-persona {
        border: none;
        background: transparent;
        color: var(--text-secondary);
        font-size: 0.82rem;
        font-weight: 600;
        padding: var(--space-1) var(--space-3);
        border-radius: var(--radius-pill);
        cursor: pointer;
        transition: background var(--motion-fast) var(--motion-ease),
            color var(--motion-fast) var(--motion-ease);
    }
    .loop-persona:hover,
    .loop-persona:focus-visible {
        color: var(--text-primary);
        outline: none;
    }
    .loop-persona.is-selected {
        background: var(--brand-primary);
        color: var(--surface-component);
    }

    /* Insight chip fade (lighter than the reveal — a UI affordance). */
    .dora-fade-enter-active,
    .dora-fade-leave-active {
        transition: opacity var(--motion-normal) var(--motion-ease);
    }
    .dora-fade-enter-from,
    .dora-fade-leave-to {
        opacity: 0;
    }
</style>
