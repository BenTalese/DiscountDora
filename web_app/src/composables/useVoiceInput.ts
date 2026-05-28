import { onBeforeUnmount, ref } from 'vue';

/**
 * P2-13 — Web Speech API wrapper for speech-to-text.
 *
 * Two callsites today: Dora chat (push-to-talk: start on mic press,
 * stop on press-again or final result), and Cook mode (continuous:
 * stays listening so the user can keep saying "next" / "previous"
 * hands-free). The `continuous` option flips between the two; defaults
 * to false (push-to-talk) so the cheaper / less-permission-anxious
 * mode is the default.
 *
 * Browser support: Chrome desktop + Chrome Android have it natively.
 * Safari/iOS exposes `webkitSpeechRecognition` but emits final results
 * less reliably; the page should fall back to typing when
 * `available.value === false`. We never throw on missing API support —
 * the caller just sees `available=false` and can choose to hide the UI.
 *
 * Permission failures (user denies the mic prompt) are surfaced through
 * `error.value`; the caller can render a friendly message rather than
 * a silent failure.
 */

type SpeechRecognitionLike = {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start: () => void;
    stop: () => void;
    onresult: ((event: SpeechResultEvent) => void) | null;
    onend: (() => void) | null;
    onerror: ((event: { error?: string }) => void) | null;
};

type SpeechResultEvent = {
    results: ArrayLike<
        ArrayLike<{ transcript: string }> & { isFinal: boolean }
    >;
};

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
    if (typeof window === 'undefined') return null;
    const w = window as unknown as {
        SpeechRecognition?: SpeechRecognitionCtor;
        webkitSpeechRecognition?: SpeechRecognitionCtor;
    };
    return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export type UseVoiceInputOptions = {
    /** When true, keep listening across pauses (Cook mode). When false,
     *  one shot — auto-stops after the first final result (push-to-talk
     *  on the Dora mic). */
    continuous?: boolean;
    /** BCP-47 tag. Defaults to en-AU to match the rest of the app. */
    lang?: string;
    /** Fires for every result (interim or final) so the caller can
     *  render a live transcript. */
    onInterim?: (text: string) => void;
    /** Fires once per final result. The caller decides what to do with
     *  it (append to a prompt, dispatch a command, etc.). */
    onFinal?: (text: string) => void;
};

export function useVoiceInput(options: UseVoiceInputOptions = {}) {
    const continuous = options.continuous ?? false;
    const lang = options.lang ?? 'en-AU';

    const ctor = getRecognitionCtor();
    const available = ref<boolean>(ctor !== null);
    const listening = ref<boolean>(false);
    const transcript = ref<string>('');
    const error = ref<string | null>(null);

    let recognition: SpeechRecognitionLike | null = null;
    // `intentionalStop` distinguishes a user-requested stop from a
    // browser-side `onend` (which we restart in continuous mode).
    let intentionalStop = false;

    function buildRecognition(): SpeechRecognitionLike | null {
        if (!ctor) return null;
        const r = new ctor();
        r.continuous = continuous;
        r.interimResults = true;
        r.lang = lang;
        r.onresult = (event) => {
            // Walk the results: emit interim text for the live caption,
            // and fire `onFinal` per final result. Web Speech delivers
            // a cumulative result list across the session, so we
            // iterate from 0 and trust `isFinal` to gate emissions.
            let interim = '';
            for (let i = 0; i < event.results.length; i++) {
                const res = event.results[i];
                if (!res) continue;
                const alt = res[0];
                if (!alt) continue;
                if (res.isFinal) {
                    const text = alt.transcript.trim();
                    if (text) {
                        transcript.value = text;
                        options.onFinal?.(text);
                    }
                } else {
                    interim += alt.transcript;
                }
            }
            if (interim) {
                transcript.value = interim.trim();
                options.onInterim?.(interim.trim());
            }
        };
        r.onend = () => {
            // In continuous mode the browser may stop after a long
            // silence. Restart unless the user asked to stop.
            if (continuous && !intentionalStop && listening.value) {
                try {
                    r.start();
                    return;
                } catch {
                    // Some browsers throw when start() is called too
                    // quickly after stop; fall through to "stopped".
                }
            }
            listening.value = false;
            intentionalStop = false;
        };
        r.onerror = (e) => {
            error.value = e.error ?? 'unknown';
            listening.value = false;
        };
        return r;
    }

    function start() {
        if (!ctor) return;
        if (listening.value) return;
        error.value = null;
        transcript.value = '';
        intentionalStop = false;
        recognition = buildRecognition();
        if (!recognition) return;
        try {
            recognition.start();
            listening.value = true;
        } catch (e) {
            // Most commonly "InvalidStateError" — a prior session
            // hadn't fully torn down. Wait a tick and retry once.
            setTimeout(() => {
                try {
                    recognition?.start();
                    listening.value = true;
                } catch {
                    error.value = e instanceof Error ? e.message : 'failed';
                    listening.value = false;
                }
            }, 100);
        }
    }

    function stop() {
        intentionalStop = true;
        if (recognition) {
            try {
                recognition.stop();
            } catch {
                /* ignore — stop after start race */
            }
        }
        listening.value = false;
    }

    function toggle() {
        if (listening.value) stop();
        else start();
    }

    // Defensive cleanup — if the component is unmounted mid-listen we
    // don't want a dangling recognition holding the mic indicator on
    // in the browser chrome.
    onBeforeUnmount(() => {
        if (listening.value) stop();
        recognition = null;
    });

    return {
        available,
        listening,
        transcript,
        error,
        start,
        stop,
        toggle,
    };
}
