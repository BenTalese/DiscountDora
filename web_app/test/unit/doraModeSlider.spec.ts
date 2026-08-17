// @vitest-environment jsdom
/**
 * FU-520 component layer — DoraModeSlider, the two-position Basic/AI pill
 * that flips the assistant's `llm_enabled` (v-model boolean; the parent
 * owns the settings API call, R-003). Pure presentation + emit, so no
 * module mocks — mounted with the real Quasar plugin per
 * stockLevelDot.spec.ts; QTooltip stubbed passthrough so its text is
 * assertable without hover activation.
 */
import { mount } from '@vue/test-utils';
import { QIcon, Quasar } from 'quasar';
import { describe, expect, it } from 'vitest';

import DoraModeSlider from 'src/components/dora/DoraModeSlider.vue';
import { expectAccessible } from './_axe';

const TooltipStub = { template: '<div class="tooltip-stub"><slot /></div>' };

function mountSlider(props: Record<string, unknown>) {
    return mount(DoraModeSlider, {
        props: { modelValue: false, ...props },
        global: {
            plugins: [Quasar],
            components: { QIcon },
            stubs: { QTooltip: TooltipStub },
        },
    });
}

describe('DoraModeSlider', () => {
    it('renders the AI position as a checked switch', () => {
        const wrapper = mountSlider({ modelValue: true });

        expect(wrapper.classes()).toContain('dora-mode-slider--ai');
        expect(wrapper.classes()).not.toContain('dora-mode-slider--basic');
        expect(wrapper.attributes('role')).toBe('switch');
        expect(wrapper.attributes('aria-checked')).toBe('true');
        expect(wrapper.find('.tooltip-stub').text())
            .toBe('AI mode on — tap to switch to Basic.');
    });

    it('renders the Basic position as unchecked with the flip tooltip', () => {
        const wrapper = mountSlider({ modelValue: false });

        expect(wrapper.classes()).toContain('dora-mode-slider--basic');
        expect(wrapper.attributes('aria-checked')).toBe('false');
        expect(wrapper.find('.tooltip-stub').text())
            .toBe('Basic mode on — tap to switch to AI.');
    });

    it('tap emits the flipped value both ways', async () => {
        const off = mountSlider({ modelValue: false });
        await off.trigger('click');
        expect(off.emitted('update:modelValue')).toEqual([[true]]);

        const on = mountSlider({ modelValue: true });
        await on.trigger('click');
        expect(on.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('toggles from the keyboard via Space and Enter', async () => {
        const wrapper = mountSlider({ modelValue: false });

        await wrapper.trigger('keydown', { key: ' ' });
        await wrapper.trigger('keydown', { key: 'Enter' });

        expect(wrapper.emitted('update:modelValue')).toEqual([[true], [true]]);
    });

    it('disabled: inert, reason in the tooltip', async () => {
        const wrapper = mountSlider({
            modelValue: false,
            disabled: true,
            disabledReason: 'Add an API key in Settings to enable AI.',
        });

        expect(wrapper.classes()).toContain('dora-mode-slider--disabled');
        expect(wrapper.classes()).not.toContain('dora-mode-slider--actionable');
        expect(wrapper.attributes('aria-disabled')).toBe('true');
        expect(wrapper.find('.tooltip-stub').text())
            .toBe('Add an API key in Settings to enable AI.');

        await wrapper.trigger('click');
        await wrapper.trigger('keydown', { key: ' ' });
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
        expect(wrapper.emitted('disabled-activate')).toBeUndefined();
    });

    // The control stays reachable by keyboard even while disabled: it carries
    // `aria-disabled` rather than native disabled semantics precisely so the
    // actionable variant below can be activated. See the D-016 carve-out note
    // in the component.
    it('stays in the tab order while disabled', () => {
        expect(mountSlider({ modelValue: false, disabled: true }).attributes('tabindex'))
            .toBe('0');
    });

    it('actionable-disabled: activating emits disabled-activate, never a flip', async () => {
        const wrapper = mountSlider({
            modelValue: false,
            disabled: true,
            disabledIsActionable: true,
            disabledReason: 'Connect a language model in Settings → Assistant first.',
        });

        expect(wrapper.classes()).toContain('dora-mode-slider--actionable');
        // The reason alone is a dead end on touch, so the tooltip also says
        // what tapping will do.
        expect(wrapper.find('.tooltip-stub').text())
            .toBe('Connect a language model in Settings → Assistant first. Tap to open Settings.');

        await wrapper.trigger('click');
        await wrapper.trigger('keydown', { key: 'Enter' });

        expect(wrapper.emitted('disabled-activate')).toHaveLength(2);
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('actionable-disabled with no reason still explains the tap', () => {
        expect(
            mountSlider({ modelValue: false, disabled: true, disabledIsActionable: true })
                .find('.tooltip-stub').text(),
        ).toBe('Tap to set AI mode up in Settings.');
    });

    it('disabled without a reason renders no tooltip at all', () => {
        const wrapper = mountSlider({ modelValue: false, disabled: true });

        expect(wrapper.find('.tooltip-stub').exists()).toBe(false);
    });

    // FU-542 — accessibility. This is a custom ARIA switch (role="switch" +
    // aria-checked), so axe checks the role/state are valid and the control
    // is named — across on, off, and disabled.
    it('has no accessibility violations (AI / on)', async () => {
        await expectAccessible(mountSlider({ modelValue: true }).element);
    });

    it('has no accessibility violations (Basic / off)', async () => {
        await expectAccessible(mountSlider({ modelValue: false }).element);
    });

    it('has no accessibility violations (disabled with reason)', async () => {
        await expectAccessible(
            mountSlider({ modelValue: false, disabled: true, disabledReason: 'AI is off for this install.' }).element,
        );
    });
});
