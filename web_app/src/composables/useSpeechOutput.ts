import { onBeforeUnmount, ref } from 'vue';

/**
 * P2-13 — Web SpeechSynthesis wrapper.
 *
 * Two callsites: Cook mode (announces the current step) and Dora chat
 * (speaks Dora's replies when the user has output enabled). The
 * composable is *not* tied to a single utterance — `speak(text)` is
 * idempotent enough that calling it twice in a row cancels the prior
 * utterance and starts the new one, which is what every call site
 * happens to want.
 *
 * `available.value` is false on browsers without `window.speechSynthesis`
 * (rare these days but possible) so the caller can hide the toggle
 * rather than offering a button that does nothing.
 */

export function useSpeechOutput() {
    const available = ref<boolean>(
        typeof window !== 'undefined' && 'speechSynthesis' in window,
    );
    const speaking = ref<boolean>(false);

    function speak(text: string) {
        if (!available.value) return;
        const trimmed = text.trim();
        if (!trimmed) return;
        const synth = window.speechSynthesis;
        // Cancel any current utterance so the new one starts cleanly —
        // letting them queue makes "next step" → "next step" stutter.
        synth.cancel();
        const utter = new SpeechSynthesisUtterance(trimmed);
        utter.onstart = () => { speaking.value = true; };
        utter.onend = () => { speaking.value = false; };
        utter.onerror = () => { speaking.value = false; };
        synth.speak(utter);
    }

    function cancel() {
        if (!available.value) return;
        window.speechSynthesis.cancel();
        speaking.value = false;
    }

    // Stop talking when the component using us tears down — a Dora
    // chat that closes mid-reply should not keep narrating into an
    // empty page.
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
