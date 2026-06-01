<template>
    <q-page padding>
        <div class="text-h5 q-mb-md">Piper TTS test</div>

        <q-banner v-if="error" class="bg-red-2 text-red-9 q-mb-md" rounded>
            {{ error }}
        </q-banner>

        <q-input
            v-model="text"
            type="textarea"
            autogrow
            outlined
            label="Text to speak"
            class="q-mb-md"
        />

<div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Speed (length_scale)</div>
                <q-slider v-model="lengthScale" :min="0.5" :max="2" :step="0.05" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ lengthScale.toFixed(2) }}</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">Piper speed knob: &gt;1 slower, &lt;1 faster.</div>
        </div>

        <div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Noise (noise_scale)</div>
                <q-slider v-model="noiseScale" :min="0" :max="1" :step="0.05" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ noiseScale.toFixed(2) }}</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">Higher = more variation in timbre.</div>
        </div>

        <div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Cadence (noise_w)</div>
                <q-slider v-model="noiseW" :min="0" :max="1.5" :step="0.05" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ noiseW.toFixed(2) }}</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">Phoneme-duration jitter. Higher = draggier, more drawled rhythm.</div>
        </div>

        <div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Sentence pause</div>
                <q-slider v-model="sentenceSilence" :min="0" :max="2" :step="0.05" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ sentenceSilence.toFixed(2) }}s</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">Silence inserted between sentences.</div>
        </div>

        <div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Pitch (semitones)</div>
                <q-slider v-model="pitchSemitones" :min="-12" :max="12" :step="1" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ pitchSemitones }}</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">True pitch shift (ffmpeg, server-side). Negative = deeper. Speed unchanged.</div>
        </div>

        <div class="q-mb-md">
            <div class="row items-center q-gutter-sm">
                <div style="min-width: 140px">Playback rate</div>
                <q-slider v-model="playbackRate" :min="0.5" :max="2" :step="0.05" label label-always class="col" />
                <div style="min-width: 48px; text-align: right">{{ playbackRate.toFixed(2) }}</div>
            </div>
            <div class="text-caption text-grey q-ml-sm">Browser-side. Shifts pitch + speed together (chipmunk/slow-mo effect).</div>
        </div>

        <div class="row q-gutter-sm q-mb-md">
            <q-btn flat color="accent" label="Goofy preset" @click="goofyPreset" />
            <q-btn flat label="Chipmunk preset" @click="chipmunkPreset" />
        </div>

        <div class="row q-gutter-sm q-mb-md">
            <q-btn
                color="primary"
                label="Speak"
                :loading="loading"
                :disable="!text.trim()"
                @click="speak"
            />
            <q-btn flat label="Stop" :disable="!playing" @click="stop" />
            <q-btn flat label="Reset" @click="reset" />
        </div>

        <audio ref="audioEl" @play="playing = true" @ended="playing = false" @pause="playing = false" />
    </q-page>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { resolveBaseURL } from 'src/services/api/axiosHttpClient';

const text = ref('Hello, I am Dora. Adjust the sliders to change how I sound. Gawrsh!');
const lengthScale = ref(1);
const noiseScale = ref(0.667);
const noiseW = ref(0.8);
const sentenceSilence = ref(0.2);
const pitchSemitones = ref(0);
const playbackRate = ref(1);
const loading = ref(false);
const playing = ref(false);
const error = ref<string | null>(null);
const audioEl = ref<HTMLAudioElement | null>(null);
let currentUrl: string | null = null;

watch(playbackRate, (v) => {
    if (audioEl.value) audioEl.value.playbackRate = v;
});

async function speak() {
    error.value = null;
    loading.value = true;
    try {
        const res = await fetch(`${resolveBaseURL('dora')}/tts`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text.value,
                length_scale: lengthScale.value,
                noise_scale: noiseScale.value,
                noise_w: noiseW.value,
                sentence_silence: sentenceSilence.value,
                pitch_semitones: pitchSemitones.value,
            }),
        });
        if (!res.ok) {
            let msg = `Synthesis failed (HTTP ${res.status}).`;
            try {
                const parsed = await res.json() as { error?: string; hint?: string };
                if (parsed.error) msg = parsed.error;
                if (parsed.hint) msg += ` ${parsed.hint}`;
            } catch { /* keep default */ }
            error.value = msg;
            return;
        }
        const blob = await res.blob();
        if (currentUrl) URL.revokeObjectURL(currentUrl);
        currentUrl = URL.createObjectURL(blob);
        const el = audioEl.value;
        if (el) {
            el.src = currentUrl;
            el.playbackRate = playbackRate.value;
            await el.play();
        }
    } catch (err: unknown) {
        error.value = err instanceof Error ? err.message : 'Synthesis failed.';
    } finally {
        loading.value = false;
    }
}

function stop() {
    const el = audioEl.value;
    if (el) {
        el.pause();
        el.currentTime = 0;
    }
}

function reset() {
    lengthScale.value = 1;
    noiseScale.value = 0.667;
    noiseW.value = 0.8;
    sentenceSilence.value = 0.2;
    pitchSemitones.value = 0;
    playbackRate.value = 1;
}

function goofyPreset() {
    lengthScale.value = 1.35;
    noiseScale.value = 0.9;
    noiseW.value = 1.3;
    sentenceSilence.value = 0.5;
    pitchSemitones.value = -7;
    playbackRate.value = 0.95;
}

function chipmunkPreset() {
    lengthScale.value = 0.85;
    noiseScale.value = 0.5;
    noiseW.value = 0.6;
    sentenceSilence.value = 0.1;
    pitchSemitones.value = 8;
    playbackRate.value = 1.1;
}

onBeforeUnmount(() => {
    stop();
    if (currentUrl) URL.revokeObjectURL(currentUrl);
});
</script>
