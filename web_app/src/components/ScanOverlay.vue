<template>
    <q-dialog
        v-model="modelOpen"
        persistent
        maximized
        transition-show="fade"
        transition-hide="fade"
    >
        <div class="scan-overlay">
            <!-- ── Camera viewport ──────────────────────────────────── -->
            <video ref="videoRef" class="scan-video" muted playsinline autoplay />

            <!-- ── Dim overlay + crosshair box ──────────────────────── -->
            <div class="scan-mask">
                <div class="scan-target" :class="{ flash: flashKind }" :data-flash="flashKind" />
            </div>

            <!-- ── Recent-decode banner (auto-fades) ────────────────── -->
            <transition name="fade">
                <div v-if="lastDecodeBanner" class="scan-banner">
                    <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
                    Decoded
                    <code class="q-ml-xs">{{ truncate(lastDecodeBanner) }}</code>
                </div>
            </transition>

            <!-- ── Top bar ──────────────────────────────────────────── -->
            <div class="scan-topbar">
                <div class="scan-status">
                    <span v-if="cameraError" class="scan-error">{{ cameraError }}</span>
                    <span v-else-if="!cameraReady">Starting camera…</span>
                    <span v-else>Point at a barcode or QR</span>
                </div>
                <div class="scan-actions">
                    <q-btn
                        v-if="torchSupported"
                        flat
                        round
                        :icon="torchOn ? 'flashlight_on' : 'flashlight_off'"
                        color="white"
                        @click="toggleTorch"
                    />
                    <q-btn
                        flat
                        round
                        :icon="ICONS.close"
                        color="white"
                        @click="onClose"
                    />
                </div>
            </div>

            <!-- ── Manual entry escape hatch ────────────────────────── -->
            <div class="scan-bottombar">
                <q-input
                    v-model="manualValue"
                    dense
                    dark
                    standout="bg-grey-9 text-white"
                    label="Or type a barcode"
                    label-color="grey-4"
                    @keyup.enter="onManualSubmit"
                >
                    <template #append>
                        <q-btn
                            flat
                            dense
                            no-caps
                            color="white"
                            label="Submit"
                            :disable="!manualValue.trim()"
                            @click="onManualSubmit"
                        />
                    </template>
                </q-input>
            </div>
        </div>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import type { BrowserMultiFormatReader, IScannerControls } from '@zxing/browser';
    import { ref, watch, onBeforeUnmount, computed } from 'vue';

    interface Props {
        modelValue: boolean;
        /** Close the overlay automatically after the first successful
         *  decode. Useful for "scan to navigate" flows; off by default so
         *  the user can keep scanning. */
        closeOnDecode?: boolean;
    }
    const props = withDefaults(defineProps<Props>(), {
        closeOnDecode: false,
    });
    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'decoded', value: string): void;
    }>();

    const modelOpen = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v),
    });

    const videoRef = ref<HTMLVideoElement | null>(null);
    const cameraReady = ref(false);
    const cameraError = ref<string | null>(null);
    const flashKind = ref<'' | 'good' | 'bad'>('');
    const manualValue = ref('');
    const torchSupported = ref(false);
    const torchOn = ref(false);
    // Short-lived banner content; reset by a timer 1.5 s after the last
    // successful decode.
    const lastDecodeBanner = ref<string | null>(null);
    let bannerTimer: ReturnType<typeof setTimeout> | null = null;

    // The active reader + media stream so we can clean them up on close.
    // Lazy-loaded so the chunk only ships when the dialog opens.
    let codeReader: BrowserMultiFormatReader | null = null;
    let controls: IScannerControls | null = null;
    let stream: MediaStream | null = null;
    let audioCtx: AudioContext | null = null;

    // Debounce identical decodes for 2 seconds. Without this, holding a
    // code in front of the camera fires the lookup once per frame.
    const DEBOUNCE_MS = 2000;
    let lastDecoded: string | null = null;
    let lastDecodedAt = 0;

    watch(modelOpen, async (open) => {
        if (open) {
            await startScanner();
        } else {
            stopScanner();
        }
    });

    onBeforeUnmount(() => {
        if (bannerTimer) clearTimeout(bannerTimer);
        void stopScanner();
    });

    async function startScanner() {
        cameraError.value = null;
        cameraReady.value = false;
        torchOn.value = false;
        try {
            const { BrowserMultiFormatReader } = await import('@zxing/browser');
            codeReader = new BrowserMultiFormatReader();

            // Pick a back-facing camera when one is exposed; otherwise just
            // use whatever the browser hands us first.
            const devices = await (
                await import('@zxing/browser')
            ).BrowserCodeReader.listVideoInputDevices().catch(() => []);
            const preferred =
                devices.find((d) => /back|rear|environment/i.test(d.label))
                ?? devices[0];

            controls = await codeReader.decodeFromVideoDevice(
                preferred?.deviceId,
                videoRef.value ?? undefined,
                (result) => {
                    if (!result) return;
                    const text = result.getText?.() ?? String(result);
                    handleDecoded(text);
                },
            );
            cameraReady.value = true;
            // Capture the live MediaStream so we can probe the video track
            // for torch capability.
            stream = (videoRef.value?.srcObject as MediaStream) ?? null;
            const track = stream?.getVideoTracks?.()[0];
            const caps = track?.getCapabilities?.() as
                | (MediaTrackCapabilities & { torch?: boolean })
                | undefined;
            torchSupported.value = Boolean(caps?.torch);
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            // NotAllowedError / NotFoundError land here. Surface a friendly
            // hint rather than the raw browser exception name.
            if (/permission|notallowed/i.test(message)) {
                cameraError.value =
                    'Camera permission denied. Enable it in your browser settings to scan.';
            } else if (/notfound|nomatch/i.test(message)) {
                cameraError.value =
                    'No camera available. Try the manual-entry box below.';
            } else {
                cameraError.value = `Couldn't start the camera: ${message}`;
            }
        }
    }

    function stopScanner() {
        try {
            controls?.stop?.();
        } catch { /* ignore */ }
        controls = null;
        try {
            stream?.getTracks?.().forEach((t) => t.stop());
        } catch { /* ignore */ }
        stream = null;
        codeReader = null;
        torchOn.value = false;
        torchSupported.value = false;
        cameraReady.value = false;
    }

    function handleDecoded(text: string) {
        const now = Date.now();
        if (text === lastDecoded && now - lastDecodedAt < DEBOUNCE_MS) return;
        lastDecoded = text;
        lastDecodedAt = now;
        showBanner(text);
        void flashAndChime('good');
        emit('decoded', text);
        if (props.closeOnDecode) modelOpen.value = false;
    }

    function showBanner(text: string) {
        lastDecodeBanner.value = text;
        if (bannerTimer) clearTimeout(bannerTimer);
        bannerTimer = setTimeout(() => { lastDecodeBanner.value = null; }, 1500);
    }

    function truncate(value: string): string {
        return value.length > 28 ? `${value.slice(0, 28)}…` : value;
    }

    function onManualSubmit() {
        const value = manualValue.value.trim();
        if (!value) return;
        manualValue.value = '';
        // Don't dedup manual entries — the user typed it on purpose.
        lastDecoded = null;
        showBanner(value);
        void flashAndChime('good');
        emit('decoded', value);
        if (props.closeOnDecode) modelOpen.value = false;
    }

    /** Short visual + audio cue. Tone uses Web Audio so we don't ship a
     *  bundled .wav. `kind` picks pitch (good = high, bad = low). */
    function flashAndChime(kind: 'good' | 'bad') {
        flashKind.value = kind;
        setTimeout(() => { flashKind.value = ''; }, 250);
        try {
            if (!audioCtx) {
                const Ctor =
                    window.AudioContext ??
                    (window as unknown as { webkitAudioContext?: typeof AudioContext })
                        .webkitAudioContext;
                if (!Ctor) return;
                audioCtx = new Ctor();
            }
            const ctx = audioCtx;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.value = kind === 'good' ? 880 : 240;
            gain.gain.setValueAtTime(0.0001, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.015);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.15);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.18);
        } catch {
            // Browsers without WebAudio (or with autoplay blocks) — silent.
        }
    }

    /** Public method for callers (e.g. unknown-barcode flow) to signal a
     *  problem without closing the overlay. */
    function flashBad() {
        void flashAndChime('bad');
    }

    async function toggleTorch() {
        if (!torchSupported.value || !stream) return;
        const track = stream.getVideoTracks?.()[0];
        if (!track) return;
        try {
            torchOn.value = !torchOn.value;
            await track.applyConstraints({
                advanced: [{ torch: torchOn.value }],
            } as unknown as MediaTrackConstraints);
        } catch {
            // Some Android cameras lie about torch capability. Don't fail
            // the whole overlay; just flip the toggle back.
            torchOn.value = !torchOn.value;
        }
    }

    function onClose() {
        modelOpen.value = false;
    }

    defineExpose({ flashBad });
</script>

<style scoped>
    .scan-overlay {
        position: relative;
        width: 100vw;
        height: 100vh;
        background: #000;
        overflow: hidden;
    }
    .scan-video {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .scan-mask {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(
            ellipse 38% 28% at center,
            transparent 0%,
            transparent 60%,
            var(--overlay-scrim) 60%
        );
        pointer-events: none;
    }
    .scan-target {
        width: min(70vw, 320px);
        height: min(40vh, 220px);
        border: 2px solid rgba(255, 255, 255, 0.85);
        border-radius: 12px;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.35);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .scan-target.flash[data-flash='good'] {
        border-color: #4caf50;
        box-shadow: 0 0 0 9999px rgba(0, 80, 0, 0.45);
    }
    .scan-target.flash[data-flash='bad'] {
        border-color: #ef5350;
        box-shadow: 0 0 0 9999px rgba(80, 0, 0, 0.45);
    }
    .scan-topbar {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        padding: 10px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        color: var(--text-inverse);
        background: linear-gradient(var(--overlay-scrim), transparent);
    }
    .scan-status {
        font-size: 14px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
    }
    .scan-error { color: #ffb4ab; }
    .scan-actions { display: flex; gap: 4px; }
    .scan-bottombar {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 12px;
        background: linear-gradient(transparent, var(--overlay-scrim));
    }
    .scan-banner {
        position: absolute;
        top: 56px;
        left: 50%;
        transform: translateX(-50%);
        padding: 6px 14px;
        background: rgba(76, 175, 80, 0.92);
        color: var(--text-inverse);
        border-radius: 999px;
        font-size: 13px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .fade-enter-active, .fade-leave-active { transition: opacity 0.18s ease; }
    .fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
