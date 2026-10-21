// Shared mobile audio-unlock primitives.
//
// Mobile browsers (Android Chrome/Firefox, iOS Safari, macOS WKWebView)
// enforce a user-gesture rule for `HTMLAudioElement.play()`: the activation
// "credit" is consumed the first time play() runs, and an intervening `await`
// that spans more than a few hundred ms (an LLM round-trip, a TTS synth fetch)
// revokes it. So the common "click → await fetch → new Audio → play()" flow
// plays fine on desktop but throws NotAllowedError on a phone.
//
// Two complementary tools live here:
//   - SILENT_WAV_DATA_URL — a 44-byte silent WAV as a data URL (no fetch, no
//     CORS). useSpeechOutput plays it once on the first gesture of the session
//     to prime iOS's per-session credit.
//   - primeAudioForGesture(el) — primes a SPECIFIC element inside the current
//     gesture so a later `el.src = …; el.play()` on that same element is
//     allowed. This is what the settings Preview needs: the element that will
//     play the synth result must itself have seen a play() during the click.

// A 44-byte WAV header + one zero PCM sample, base64-encoded.
export const SILENT_WAV_DATA_URL =
    'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';

/**
 * Prime an <audio> element for playback later in the same task by starting a
 * silent play() on it right now — while the user gesture is still active. A
 * subsequent `el.src = realUrl; el.play()` on the SAME element then inherits
 * the activation, so it isn't blocked by the mobile autoplay policy after an
 * intervening `await`. Silent, so nothing is audible; the rejection (if the
 * platform still declines) is swallowed — worst case we're no worse off than
 * before. Harmless on desktop.
 */
export function primeAudioForGesture(el: HTMLAudioElement): void {
    try {
        el.src = SILENT_WAV_DATA_URL;
        const p: Promise<void> | undefined = el.play();
        // Legacy engines return undefined; modern ones a promise we must not
        // leave floating. `!= null` (not a bare `p &&`) keeps the promise out
        // of a boolean position — @typescript-eslint/no-misused-promises.
        if (p != null && typeof p.then === 'function') p.catch(() => { /* expected on decline */ });
    } catch {
        // Some engines throw before returning a promise — treat as a no-op.
    }
}
