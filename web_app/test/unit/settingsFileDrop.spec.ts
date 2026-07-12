// @vitest-environment jsdom
/**
 * FU-520 component layer — SettingsFileDrop, the shared drop-zone /
 * file-picker used by the Settings import surfaces. v-model'd File with
 * `pick`/`clear` events; the parent owns the actual upload (R-003).
 * Mounted with the real Quasar components per stockLevelDot.spec.ts. The
 * hidden input's native `.click()` is spied and no-opped so the zone
 * click test doesn't recursively re-dispatch through jsdom.
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
        expect(wrapper.attributes('role')).toBe('button');
        expect(wrapper.attributes('tabindex')).toBe('0');
    });

    it('clicking the zone forwards to the hidden input', async () => {
        const wrapper = mountDrop();
        const click = vi
            .spyOn(wrapper.find('input').element, 'click')
            .mockImplementation(() => {});

        await wrapper.trigger('click');
        await wrapper.trigger('keydown', { key: 'Enter' });

        expect(click).toHaveBeenCalledTimes(2);
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
        // @click.stop — clearing must not bubble into onZoneClick.
        expect(click).not.toHaveBeenCalled();
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

    it('ignores clicks and drops while busy', async () => {
        const wrapper = mountDrop({ loading: true });
        const click = vi
            .spyOn(wrapper.find('input').element, 'click')
            .mockImplementation(() => {});

        await wrapper.trigger('click');
        await wrapper.trigger('drop', { dataTransfer: { files: [csvFile()] } });

        expect(click).not.toHaveBeenCalled();
        expect(wrapper.emitted('pick')).toBeUndefined();
    });
});

describe('SettingsFileDrop — disabled state', () => {
    it('is inert: no picker, no drag highlight, no drop, out of tab order', async () => {
        const wrapper = mountDrop({ disabled: true });
        const click = vi
            .spyOn(wrapper.find('input').element, 'click')
            .mockImplementation(() => {});

        expect(wrapper.classes()).toContain('file-drop--disabled');
        expect(wrapper.attributes('tabindex')).toBe('-1');
        expect(wrapper.find('input').attributes('disabled')).toBeDefined();

        await wrapper.trigger('click');
        await wrapper.trigger('dragover');
        expect(wrapper.classes()).not.toContain('file-drop--dragging');
        await wrapper.trigger('drop', { dataTransfer: { files: [csvFile()] } });

        expect(click).not.toHaveBeenCalled();
        expect(wrapper.emitted('pick')).toBeUndefined();
    });

    // FU-542 — accessibility. A file drop-zone with a hidden <input type=file>
    // is a classic a11y trap. axe found two issues here: the input was
    // unlabelled (FIXED — it's now aria-hidden + tabindex=-1, since the
    // wrapping role="button" div is the real exposed control), and a
    // `nested-interactive` (the native file input is interactive and sits
    // inside the interactive drop-zone). The nested-interactive needs the
    // label-wrap accessible-file-input refactor — logged as FU-545 — so it's
    // out of scope for this test-infra FU. The disabled state (input
    // non-interactive) is fully clean and guards the label fix.
    it('has no accessibility violations (disabled)', async () => {
        await expectAccessible(mountDrop({ disabled: true }).element);
    });
});
