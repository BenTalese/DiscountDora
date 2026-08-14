// @vitest-environment jsdom
/**
 * Owner-reported bug 2026-08-14: after picking the built-in device voice, the
 * one neural voice you could never get back to was the one you'd been using —
 * every *other* ready voice selected fine.
 *
 * Cause: selecting the device default keeps `voice_id` (so switching back
 * remembers your voice), but the card-click guard was a bare
 * `voice.id === modelValue`, which then matched the retained id and swallowed
 * the click. The template's `voice-card--active` test already had it right
 * (`!deviceDefaultActive && …`); the handler didn't.
 *
 * Pinned here rather than re-walked by hand because reproducing it live needs a
 * downloaded ~60MB voice model on the server.
 */
import { mount } from '@vue/test-utils';
import { QIcon, QTooltip, Quasar } from 'quasar';
import { describe, expect, it, vi } from 'vitest';

import VoicePicker from 'src/components/settings/VoicePicker.vue';
import type { TtsVoice } from 'src/services/api/ttsApiService';

vi.mock('src/services/api/ttsApiService', () => ({
    default: class { synthesizeAsync = vi.fn(); },
}));

function voice(id: string, status: TtsVoice['status'] = 'ready'): TtsVoice {
    return {
        id,
        label: id,
        description: `${id} description`,
        gender: 'female',
        status,
        size_bytes: 60 * 1024 * 1024,
    } as TtsVoice;
}

const VOICES = [voice('amy'), voice('ryan'), voice('jenny', 'downloadable')];

function mountPicker(props: Record<string, unknown>) {
    return mount(VoicePicker, {
        props: {
            modelValue: 'amy',
            voices: VOICES,
            piperAvailable: true,
            deviceDefaultActive: false,
            ...props,
        },
        global: { plugins: [Quasar], components: { QIcon, QTooltip } },
    });
}

/** The neural cards, in catalogue order (skips the built-in card, which sits
 *  outside the grid). */
function neuralCards(wrapper: ReturnType<typeof mountPicker>) {
    return wrapper.findAll('.voice-picker .voice-card');
}

describe('VoicePicker selection', () => {
    it('re-selects the remembered voice after the device default was chosen', async () => {
        // The regression: modelValue is still 'amy' while the browser engine is
        // active, so clicking Amy has to emit — it is not the live selection.
        const wrapper = mountPicker({ modelValue: 'amy', deviceDefaultActive: true });
        await neuralCards(wrapper)[0]!.trigger('click');
        expect(wrapper.emitted('update:modelValue')).toEqual([['amy']]);
    });

    it('still ignores a click on the voice that is genuinely selected', async () => {
        const wrapper = mountPicker({ modelValue: 'amy', deviceDefaultActive: false });
        await neuralCards(wrapper)[0]!.trigger('click');
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('selects a different ready voice in either engine state', async () => {
        for (const deviceDefaultActive of [false, true]) {
            const wrapper = mountPicker({ modelValue: 'amy', deviceDefaultActive });
            await neuralCards(wrapper)[1]!.trigger('click');
            expect(wrapper.emitted('update:modelValue')).toEqual([['ryan']]);
        }
    });

    it('ignores clicks on a voice that is not downloaded yet', async () => {
        const wrapper = mountPicker({ modelValue: 'amy', deviceDefaultActive: true });
        await neuralCards(wrapper)[2]!.trigger('click');
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('emits nothing when disabled', async () => {
        const wrapper = mountPicker({ modelValue: 'amy', deviceDefaultActive: true, disabled: true });
        await neuralCards(wrapper)[1]!.trigger('click');
        expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('does not re-emit the device default when it is already active', async () => {
        const wrapper = mountPicker({ deviceDefaultActive: true });
        await wrapper.find('.voice-card--basic').trigger('click');
        expect(wrapper.emitted('select-device-default')).toBeUndefined();
    });

    it('offers the device default when a neural voice is active', async () => {
        const wrapper = mountPicker({ deviceDefaultActive: false });
        await wrapper.find('.voice-card--basic').trigger('click');
        expect(wrapper.emitted('select-device-default')).toHaveLength(1);
    });

    it('separates the built-in voice from the neural grid', () => {
        const wrapper = mountPicker({});
        // The built-in card must not be a peer tile inside the neural grid —
        // that sameness is what made the two kinds hard to tell apart.
        expect(wrapper.find('.voice-picker .voice-card--basic').exists()).toBe(false);
        expect(wrapper.findAll('.voice-picker__group-label')).toHaveLength(2);
        expect(neuralCards(wrapper)).toHaveLength(VOICES.length);
    });
});
