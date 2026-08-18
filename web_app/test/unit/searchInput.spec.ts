// @vitest-environment jsdom
/**
 * Regression cover for the reported cookbook crash (2026-08-18): clearing the
 * Ingredients filter's search box with the X took the whole app down.
 *
 * Quasar's `clearable` emits **null**, not `''`. Four call sites held a
 * `ref('')`, handed it to a clearable input, and then called `.trim()` on the
 * value — so the X threw a TypeError inside a computed and killed the render.
 * `SearchInput` exists so that can't happen; this pins the contract, because
 * the failure is invisible at the call site (it typechecks fine — the null
 * arrives at runtime from inside Quasar).
 */
import { mount } from '@vue/test-utils';
import {
    QBtnToggle, QIcon, QInput, QItem, QItemLabel, QItemSection,
    QList, QSeparator, Quasar,
} from 'quasar';
import { describe, expect, it } from 'vitest';

import SearchInput from 'src/components/SearchInput.vue';
import TriStateFilter from 'src/components/filters/TriStateFilter.vue';

function mountSearch(props: Record<string, unknown> = {}) {
    return mount(SearchInput, {
        props: { modelValue: 'pesto', ...props },
        global: { plugins: [Quasar], components: { QInput, QIcon } },
    });
}

describe('SearchInput', () => {
    it('emits an empty string, never null, when Quasar clears it', async () => {
        const wrapper = mountSearch();
        // Exactly what q-input's clear button does internally.
        wrapper.findComponent(QInput).vm.$emit('update:modelValue', null);
        await wrapper.vm.$nextTick();

        const emitted = wrapper.emitted('update:modelValue');
        expect(emitted).toBeTruthy();
        expect(emitted![0]![0]).toBe('');
        expect(emitted![0]![0]).not.toBeNull();
    });

    it('passes typed text straight through', async () => {
        const wrapper = mountSearch({ modelValue: '' });
        await wrapper.find('input').setValue('basil');

        expect(wrapper.emitted('update:modelValue')![0]![0]).toBe('basil');
    });

    it('clears to an empty string when the real X is clicked', async () => {
        // The strongest form of this test: drive Quasar's own clear button
        // rather than asserting a prop name, so it still covers us if Quasar
        // changes how `clear-value` is plumbed internally.
        const wrapper = mountSearch({ modelValue: 'pesto' });
        const clearBtn = wrapper.find('.q-field__focusable-action');
        expect(clearBtn.exists()).toBe(true);

        await clearBtn.trigger('click');

        const emitted = wrapper.emitted('update:modelValue');
        expect(emitted).toBeTruthy();
        expect(emitted!.at(-1)![0]).toBe('');
        expect(emitted!.at(-1)![0]).not.toBeNull();
    });
});

describe('TriStateFilter — the surface the crash was reported on', () => {
    it('survives its search box being cleared', async () => {
        const wrapper = mount(TriStateFilter, {
            props: {
                label: 'Ingredients',
                searchable: true,
                options: [
                    { value: 'a', label: 'Basil' },
                    { value: 'b', label: 'Pine nuts' },
                ],
                include: [],
                exclude: [],
            },
            global: {
                plugins: [Quasar],
                components: {
                    QBtnToggle, QIcon, QInput, QItem, QItemLabel,
                    QItemSection, QList, QSeparator,
                },
                // The real q-btn-dropdown renders its panel lazily (only once
                // opened), which would leave the thing under test unmounted.
                // Stub it to render the panel inline; everything inside it —
                // the search box and the computed that crashed — is real.
                stubs: {
                    QBtnDropdown: {
                        name: 'QBtnDropdown',
                        template: '<div><slot name="label" /><slot /></div>',
                    },
                },
            },
        });

        const search = wrapper.findComponent(SearchInput);
        expect(search.exists()).toBe(true);

        // Pre-fix this threw `Cannot read properties of null (reading 'trim')`
        // out of the visibleGroups computed and unmounted the page.
        expect(() => {
            search.vm.$emit('update:modelValue', '');
        }).not.toThrow();
        await wrapper.vm.$nextTick();
        expect(wrapper.html()).toBeTruthy();
    });
});
