<template>
    <component
        :is="tag"
        ref="el"
        role="button"
        :tabindex="disabled ? -1 : 0"
        :aria-label="label"
        :aria-disabled="disabled ? 'true' : undefined"
        @keydown.enter.prevent="activate"
        @keydown.space.prevent="activate"
    >
        <slot />
    </component>
</template>

<script lang="ts" setup>
    /**
     * A run of text that is also the control that edits it.
     *
     * Inline-edit surfaces reach for `<span tabindex="0">` because the target
     * has to sit *inside* a sentence, a heading or a table cell, where a
     * `<button>` is either invalid (it can't contain a `<p>`) or drags in
     * styling that breaks the line. The cost is that the span is focusable but
     * announces nothing, and Enter/Space do nothing — which is a keyboard and
     * screen-reader dead end on every editable value on the page.
     *
     * So: `role="button"`, a mandatory accessible name, and keyboard
     * activation that dispatches a real click. The click matters — `QPopupEdit`
     * opens off a click on its parent element, so synthesising one is what
     * makes the keyboard path identical to the pointer path instead of a
     * second, subtly different code path.
     *
     * `label` is required on purpose. "Recipe name" tells a screen-reader user
     * what the button edits; the rendered value alone tells them only what it
     * currently says.
     */
    import { ref } from 'vue';

    withDefaults(
        defineProps<{
            /** Accessible name — what this edits, not its current value. */
            label: string;
            /** Must be phrasing content's parent where the slot holds block
             *  elements; `span` everywhere else. */
            tag?: 'span' | 'div' | 'p' | 'h1' | 'h2';
            disabled?: boolean;
        }>(),
        { tag: 'span', disabled: false },
    );

    const el = ref<HTMLElement | { $el: HTMLElement } | null>(null);

    function activate() {
        const node = el.value;
        if (!node) return;
        const dom = node instanceof HTMLElement ? node : node.$el;
        dom?.click();
    }
</script>

<style scoped lang="scss">
    /* A6 / D-016 — the focus ring is the component's job, because the reason
       this exists at all is that the bare spans had none. Everything else
       (colour, the dotted underline) is the consuming surface's. */
    [role='button'] {
        cursor: pointer;

        &:focus-visible {
            outline: 2px solid var(--focus-ring);
            outline-offset: 2px;
            border-radius: var(--radius-xs);
        }

        &[aria-disabled='true'] {
            cursor: default;
        }
    }
</style>
