// @vitest-environment jsdom
/**
 * FU-520 component layer — SettingsFileDrop, the shared drop-zone /
 * file-picker used by the Settings import surfaces. v-model'd File with
 * `pick`/`clear` events; the parent owns the actual upload (R-003).
 * Mounted with the real Quasar components per stockLevelDot.spec.ts.
 *
 * FU-545 reworked the interaction model to the accessible label-wrap pattern:
 * the wrapper is a <label> and the native <input type="file"> (visually hidden,
 * still focusable) is the single interactive control the label forwards to
 * natively — no more role="button" / tabindex / programmatic `inputEl.click()`.
 * That killed the `nested-interactive` axe violation, so the empty + filled
 * axe assertions (held back under FU-542) are now enabled alongside disabled.
 */
import { mount } from '@vue/test-utils';
import { QBtn, QIcon, QLinearProgress, QSpinner, Quasar } from 'quasar';
import { describe, expect, it, vi } from 'vitest';

import SettingsFileDrop from 'src/components/settings/SettingsFileDrop.vue';
import { expectAccessible } from './_axe';

const TooltipStub = { template: '<span class="tooltip-stub" />' };

function mountDrop(props: Record<string, unknown> = {}) {
    return mount(SettingsFileDrop, {
        props: { modelValue: null, label: 'Drop a backup here', ...props },
        global: {
            plugins: [Quasar],
            components: { QBtn, QIcon, QLinearProgress, QSpinner },
            stubs: { QTooltip: TooltipStub },
        },
    });
}

function csvFile(name = 'stock.csv', bytes = 1536): File {
    return new File(['x'.repeat(bytes)], name, { type: 'text/csv' });
}

/** Fires the hidden input's change with the given file selected. */
async function pickViaInput(wrapper: ReturnType<typeof mountDrop>, file: File) {
    const input = wrapper.find<HTMLInputElement>('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
        value: [file],
        configurable: true,
    });
    await input.trigger('change');
}

describe('SettingsFileDrop — idle state', () => {
    it('renders label, hint and passes the accept filter to the input', () => {
        const wrapper = mountDrop({ accept: '.csv,.json', hint: 'CSV or JSON' });

        expect(wrapper.text()).toContain('Drop a backup here');
        expect(wrapper.text()).toContain('CSV or JSON');
        expect(wrapper.find('input[type="file"]').attributes('accept'))
            .toBe('.csv,.json');
    });

    it('exposes a single labelled file input inside a non-interactive label (FU-545)', () => {
        const wrapper = mountDrop();

        // The wrapper is a <label>, not a role="button" widget, so there's no
        // interactive control nested inside another (the old violation).
        expect(wrapper.element.tagName).toBe('LABEL');
        expect(wrapper.attributes('role')).toBeUndefined();
        expect(wrapper.attributes('tabindex')).toBeUndefined();

        // The native input is the exposed control: labelled + in the a11y tree
        // (not aria-hidden), and enabled while idle so the label forwards to it.
        const input = wrapper.find('input[type="file"]');
        expect(input.attributes('aria-label')).toBe('Drop a backup here');
        expect(input.attributes('aria-hidden')).toBeUndefined();
        expect(input.attributes('disabled')).toBeUndefined();
    });
});

describe('SettingsFileDrop — picking a file', () => {
    it('input change emits update:modelValue + pick with the file', async () => {
        const wrapper = mountDrop();
        const file = csvFile();

        await pickViaInput(wrapper, file);

        expect(wrapper.emitted('update:modelValue')).toEqual([[file]]);
        expect(wrapper.emitted('pick')).toEqual([[file]]);
    });

    it('dragover highlights, dragleave calms, drop takes the first file', async () => {
        const wrapper = mountDrop();
        const file = csvFile();

        await wrapper.trigger('dragover');
        expect(wrapper.classes()).toContain('file-drop--dragging');

        await wrapper.trigger('dragleave');
        expect(wrapper.classes()).not.toContain('file-drop--dragging');

        await wrapper.trigger('drop', { dataTransfer: { files: [file] } });
        expect(wrapper.classes()).not.toContain('file-drop--dragging');
        expect(wrapper.emitted('pick')).toEqual([[file]]);
    });

    it('an empty drop emits nothing', async () => {
        const wrapper = mountDrop();

        await wrapper.trigger('drop', { dataTransfer: { files: [] } });

        expect(wrapper.emitted('pick')).toBeUndefined();
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });
});

describe('SettingsFileDrop — selected-file state', () => {
    it('shows filename + formatted size and the filled styling', () => {
        const wrapper = mountDrop({ modelValue: csvFile('stock.csv', 1536) });

        expect(wrapper.classes()).toContain('file-drop--filled');
        expect(wrapper.find('.file-drop__filename').text()).toBe('stock.csv');
        expect(wrapper.find('.file-drop__filesize').text()).toBe('1.5 KB');
    });

    it('formats sub-KB sizes in bytes', () => {
        const wrapper = mountDrop({ modelValue: csvFile('tiny.csv', 512) });

        expect(wrapper.find('.file-drop__filesize').text()).toBe('512 B');
    });

    it('the remove button clears without re-opening the picker', async () => {
        const wrapper = mountDrop({ modelValue: csvFile() });
        const click = vi
            .spyOn(wrapper.find('input').element, 'click')
            .mockImplementation(() => {});

        await wrapper.find('button').trigger('click');

        expect(wrapper.emitted('update:modelValue')).toEqual([[null]]);
        expect(wrapper.emitted('clear')).toHaveLength(1);
        // The Remove button is interactive content, so a native <label> never
        // forwards a click on it to the file input (FU-545, supersedes the old
        // @click.stop guard) — no picker re-open, no stray pick.
        expect(click).not.toHaveBeenCalled();
        expect(wrapper.emitted('pick')).toBeUndefined();
    });
});

describe('SettingsFileDrop — busy state', () => {
    it('shows the spinner and the loading text', () => {
        const wrapper = mountDrop({ loading: true, loadingText: 'Importing…' });

        expect(wrapper.find('.q-spinner').exists()).toBe(true);
        expect(wrapper.text()).toContain('Importing…');
        expect(wrapper.find('.q-linear-progress').exists()).toBe(false);
    });

    it('mid-upload progress renders the percentage bar', () => {
        const wrapper = mountDrop({ loading: true, progress: 0.4 });

        expect(wrapper.text()).toContain('Uploading 40%');
        expect(wrapper.find('.q-linear-progress').exists()).toBe(true);
    });

    it('disables the input while busy so the label cannot open the picker, and ignores drops', async () => {
        const wrapper = mountDrop({ loading: true });

        // The input is disabled, so a native label click no-ops — the picker
        // stays shut without any programmatic guard.
        expect(wrapper.find('input').attributes('disabled')).toBeDefined();

        await wrapper.trigger('drop', { dataTransfer: { files: [csvFile()] } });
        expect(wrapper.emitted('pick')).toBeUndefined();
    });
});

describe('SettingsFileDrop — disabled state', () => {
    it('is inert: input disabled, no drag highlight, no drop', async () => {
        const wrapper = mountDrop({ disabled: true });

        expect(wrapper.classes()).toContain('file-drop--disabled');
        // The disabled native input is out of the tab order and can't be
        // activated by the label — no separate wrapper tabindex to manage now.
        expect(wrapper.find('input').attributes('disabled')).toBeDefined();

        await wrapper.trigger('dragover');
        expect(wrapper.classes()).not.toContain('file-drop--dragging');
        await wrapper.trigger('drop', { dataTransfer: { files: [csvFile()] } });

        expect(wrapper.emitted('pick')).toBeUndefined();
    });

    // FU-542 / FU-545 — accessibility. A file drop-zone with a hidden
    // <input type=file> is a classic a11y trap. axe originally found two issues:
    // an unlabelled input, and a `nested-interactive` (an interactive file
    // input nested inside a role="button" drop-zone). Both are now fixed by the
    // FU-545 label-wrap pattern — a non-interactive <label> wrapping a single
    // labelled input — so all three states scan clean, not just disabled.
    it.each([
        ['idle', {}],
        ['filled', { modelValue: csvFile() }],
        ['disabled', { disabled: true }],
    ] as const)('has no accessibility violations (%s)', async (_name, props) => {
        await expectAccessible(mountDrop(props).element);
    });
});
