import { onBeforeUnmount, ref } from 'vue';
import { useAuthStore } from 'src/stores/authStore';
import TtsApiService from 'src/services/api/ttsApiService';

/**
 * Speech output for Dora — used by Cook mode (announces the current step) and
 * Dora chat (speaks her replies when the user has output enabled).
 *
 * Two engines, chosen per-user (`voice_engine`):
 *   - `piper`   — POST /api/tts for a natural neural voice, played back through
 *                 an <audio> element. The user's `voice_id` picks the voice.
 *   - `browser` — the built-in Web SpeechSynthesis API (the original path).
 *
 * Piper is preferred when selected, but if it isn't configured/installed
 * server-side (the endpoint 503s) or the request otherwise fails, we fall back
 * to the browser voice for that utterance — so Dora is never silent. `speak()`
 * is idempotent: calling it again (or `cancel()`) supersedes any in-flight or
 * playing utterance, including a slow Piper fetch that hasn't resolved yet.
 *
 * `available.value` is true when *any* output path is usable: browser
 * SpeechSynthesis OR a server-configured Piper. It starts at the synchronous
 * browser-only answer; the per-session Piper probe (deduped across
 * composable instances) flips it true async if Piper alone would work, so the
 * Settings → Voice toggle and the chat mute button appear on browsers without
 * SpeechSynthesis (FU-289).
 */
const ttsProbe = new TtsApiService();
// Cached per session — `configured` is install-time server state, not
// per-request. Resolves true when Piper would handle a `speak()`.
let piperConfiguredProbe: Promise<boolean> | null = null;
function probePiperConfigured(): Promise<boolean> {
    piperConfiguredProbe ??= ttsProbe
        .getVoicesAsync()
        .then((r) => r.configured === true)
        .catch(() => false);
    return piperConfiguredProbe;
}

// iOS / WKWebView audio-unlock primer.
//
// iOS Safari (and the macOS WKWebView the desktop bundle uses on Mac)
// enforce a strict user-gesture rule for `HTMLAudioElement.play()`. The
// gesture-permission "credit" is consumed the first time `play()` is
// called after user interaction, and it can be REVOKED by an intervening
// `await` that spans more than ~a few hundred ms. Two flows this bites:
//   - Dora chat reply: LLM round-trip (`await`) → Piper synth fetch
//     (`await`) → new `<audio>` → `audio.play()`. On iOS, by the time
//     we call `play()` the gesture is often gone.
//   - Cook-mode timer-fired narration: no gesture at all (timer callback
//     is not a user activation). This can't be fixed by a primer alone;
//     documented at the caller.
//
// Fix: on the first user interaction in the tab session, play a very-
// short silent muted audio blob to prime the browser's autoplay policy.
// Subsequent `Audio.play()` calls in the same session inherit the
// credit — including calls that happen across `await`s. On every other
// platform this is a harmless no-op (Chrome/Firefox/Android don't gate
// on gesture-per-play for muted audio).
//
// A 44-byte WAV header + one zero PCM sample encoded as a data URL.
// Chosen over `AudioContext.createBuffer` because AudioContext.resume()
// hits the same iOS gesture wall and adds a heavier dep for a one-time
// primer. Keeping it as a data URL means no fetch, no CORS, no delay.
const SILENT_WAV_DATA_URL =
    'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';

let audioUnlocked = false;
let audioUnlockRegistered = false;
function unlockAudioOnFirstGesture(): void {
    if (audioUnlockRegistered || typeof document === 'undefined') return;
    audioUnlockRegistered = true;

    const events: Array<keyof DocumentEventMap> =
        ['pointerdown', 'touchstart', 'keydown', 'click'];
    const cleanup = (): void => {
        for (const type of events) document.removeEventListener(type, primer, true);
    };
    const primer = (): void => {
        // One-shot: drop listeners immediately so subsequent gestures
        // don't re-run this no-op. The listeners survive `once: false`
        // because we register on multiple event types — cleanup removes
        // them from all types together.
        cleanup();
        if (audioUnlocked) return;
        try {
            const audio = new Audio(SILENT_WAV_DATA_URL);
            audio.muted = true;
            const p = audio.play();
            if (p != null && typeof p.then === 'function') {
                p.then(() => {
                    audioUnlocked = true;
                    // Stop immediately — we only needed the play() call
                    // itself to claim the gesture credit.
                    audio.pause();
                }).catch(() => {
                    // A play() rejection here means the gesture didn't
                    // count (e.g. programmatic dispatch, unusual browser
                    // state). We accept the one-shot cost — trying every
                    // gesture would leak listeners on non-iOS platforms
                    // that never needed the primer in the first place.
                });
            } else {
                // Legacy browsers where play() returned undefined.
                audioUnlocked = true;
            }
        } catch {
            // Some environments throw before returning a promise —
            // treat the same as a rejected promise (one-shot done).
        }
    };
    for (const type of events) {
        document.addEventListener(type, primer, {
            passive: true,
            capture: true,
        });
    }
}

export function useSpeechOutput() {
    // register the iOS audio-unlock primer once per session on
    // the first `useSpeechOutput()` instantiation (which is early — the
    // MainLayout mounts Dora chat + cook mode both consume this).
    // Idempotent across composable instances.
    unlockAudioOnFirstGesture();

    const browserAvailable =
        typeof window !== 'undefined' && 'speechSynthesis' in window;
    const available = ref<boolean>(browserAvailable);
    const speaking = ref<boolean>(false);

    // If the browser already covers it, no need to probe. Otherwise ask the
    // server whether Piper is configured — when yes, flip `available` true so
    // the output toggle stops hiding on browsers without SpeechSynthesis.
    if (!browserAvailable) {
        void probePiperConfigured().then((piperOk) => {
            if (piperOk) available.value = true;
        });
    }

    const authStore = useAuthStore();
    const ttsApi = new TtsApiService();

    let currentAudio: HTMLAudioElement | null = null;
    let currentUrl: string | null = null;
    // Monotonic token bumped by every speak()/cancel(). A Piper fetch that
    // resolves after a newer call is discarded instead of talking over the
    // current utterance.
    let seq = 0;

    function stopAudio() {
        if (currentAudio) {
            currentAudio.onplay = null;
            currentAudio.onended = null;
            currentAudio.onpause = null;
            currentAudio.onerror = null;
            currentAudio.pause();
            currentAudio = null;
        }
        if (currentUrl) {
            URL.revokeObjectURL(currentUrl);
            currentUrl = null;
        }
    }

    function speakBrowser(text: string) {
        if (!browserAvailable) return;
        const synth = window.speechSynthesis;
        // Cancel any current utterance so the new one starts cleanly —
        // letting them queue makes "next step" → "next step" stutter.
        synth.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.onstart = () => { speaking.value = true; };
        utter.onend = () => { speaking.value = false; };
        utter.onerror = () => { speaking.value = false; };
        synth.speak(utter);
    }

    /** Returns true when Piper handled the utterance (played, or was
     * superseded by a newer call); false when it failed and the caller should
     * fall back to the browser voice. */
    async function playPiper(text: string, voiceId: string, token: number): Promise<boolean> {
        try {
            const blob = await ttsApi.synthesizeAsync(text, voiceId);
            if (token !== seq) return true; // superseded — don't play or fall back
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            currentAudio = audio;
            currentUrl = url;
            audio.onplay = () => { speaking.value = true; };
            audio.onended = () => {
                speaking.value = false;
                if (currentAudio === audio) stopAudio();
            };
            audio.onpause = () => { speaking.value = false; };
            audio.onerror = () => { speaking.value = false; };
            await audio.play();
            return true;
        } catch {
            return false;
        }
    }

    function speak(text: string) {
        const trimmed = text.trim();
        if (!trimmed) return;
        cancel(); // bumps seq, stops any audio + synthesis
        const token = seq;
        const user = authStore.currentUser;
        const engine = user?.voice_engine ?? 'piper';
        const voiceId = user?.voice_id ?? 'amy';
        if (engine === 'piper') {
            void playPiper(trimmed, voiceId, token).then((handled) => {
                // Only fall back if Piper failed AND we're still the current
                // utterance (a newer speak()/cancel() would have bumped seq).
                if (!handled && token === seq) speakBrowser(trimmed);
            });
            return;
        }
        speakBrowser(trimmed);
    }

    function cancel() {
        seq += 1;
        stopAudio();
        if (browserAvailable) window.speechSynthesis.cancel();
        speaking.value = false;
    }

    // Stop talking when the component using us tears down — a Dora chat that
    // closes mid-reply should not keep narrating into an empty page.
    onBeforeUnmount(() => {
        cancel();
    });

    return {
        available,
        speaking,
        speak,
        cancel,
    };
}
