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
 * `available.value` reflects browser SpeechSynthesis support (the universal
 * fallback); the per-page output toggle hides when it's false.
 */
export function useSpeechOutput() {
    const browserAvailable =
        typeof window !== 'undefined' && 'speechSynthesis' in window;
    const available = ref<boolean>(browserAvailable);
    const speaking = ref<boolean>(false);

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
