<template>
    <nav class="rail" aria-label="Onboarding progress — jump to any step">
        <template v-for="(section, sIdx) in sections" :key="section.key">
            <span v-if="sIdx > 0" class="rail-divider" aria-hidden="true"></span>
            <div class="rail-section">
                <span class="rail-section-label">{{ section.label }}</span>
                <div class="rail-dots">
                    <button
                        v-for="(dot, dIdx) in section.dots"
                        :key="dot.key"
                        type="button"
                        class="rail-dot"
                        :class="{
                            'is-active': isActive(section.key, dIdx),
                            'is-done': isDone(sIdx, dIdx),
                        }"
                        :aria-label="`${section.label}: ${dot.label}`"
                        :aria-current="isActive(section.key, dIdx) ? 'step' : undefined"
                        @click="emit('jump', section.key, dIdx)"
                    >
                        <span class="rail-dot-mark" aria-hidden="true"></span>
                    </button>
                </div>
            </div>
        </template>
    </nav>
</template>

<script lang="ts" setup>
    // A persistent, fully non-linear progress rail. Nothing is gated — every
    // dot is a jump target. Doubles as the "how far through" indicator.
    interface RailDot {
        key: string;
        label: string;
    }
    interface RailSection {
        key: string;
        label: string;
        dots: RailDot[];
    }

    const props = defineProps<{
        sections: RailSection[];
        activeSection: string;
        activeIndex: number;
    }>();
    const emit = defineEmits<{ jump: [sectionKey: string, index: number] }>();

    function isActive(sectionKey: string, index: number) {
        return sectionKey === props.activeSection && index === props.activeIndex;
    }

    // "Done" = anything before the active position in reading order (earlier
    // section, or earlier dot in the active section).
    function isDone(sectionIndex: number, dotIndex: number) {
        const activeSectionIndex = props.sections.findIndex(
            (s) => s.key === props.activeSection,
        );
        if (sectionIndex < activeSectionIndex) return true;
        if (sectionIndex > activeSectionIndex) return false;
        return dotIndex < props.activeIndex;
    }
</script>

<style scoped>
    .rail {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        flex-wrap: wrap;
        justify-content: center;
    }
    .rail-divider {
        width: 18px;
        height: 1px;
        background: var(--border-default);
    }
    .rail-section {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
    }
    .rail-section-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
    }
    .rail-dots {
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .rail-dot {
        border: none;
        background: transparent;
        padding: 6px; /* generous hit target around a small mark */
        cursor: pointer;
        line-height: 0;
        border-radius: var(--radius-full);
    }
    .rail-dot:focus-visible {
        outline: none;
        box-shadow: 0 0 0 2px var(--brand-accent-soft);
    }
    .rail-dot-mark {
        display: block;
        width: 8px;
        height: 8px;
        border-radius: var(--radius-full);
        background: var(--border-strong);
        transition: background var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease-spring);
    }
    .rail-dot:hover .rail-dot-mark {
        background: var(--brand-primary);
    }
    .rail-dot.is-done .rail-dot-mark {
        background: var(--brand-primary);
    }
    .rail-dot.is-active .rail-dot-mark {
        background: var(--brand-accent);
        transform: scale(1.5);
    }
</style>
