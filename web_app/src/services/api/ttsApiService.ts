import AxiosHttpClient, { resolveBaseURL } from './axiosHttpClient';

/** Download/availability state of a voice. `downloadable` = in the catalog but
 * its model isn't fetched yet; `downloading` = fetch in flight; `ready` = model
 * present; `error` = last fetch failed (retryable). */
export type TtsVoiceStatus = 'downloadable' | 'downloading' | 'ready' | 'error';

/** One voice from the server catalog (GET /api/tts/voices). The catalog +
 * tuning are owned server-side (voice_catalog.py); the SPA only ever picks a
 * voice by `id`. Models are downloaded on demand (see downloadVoiceAsync). */
export type TtsVoice = {
    id: string;
    label: string;
    description: string;
    gender: 'female' | 'male' | 'neutral';
    size_bytes: number;
    status: TtsVoiceStatus;
    // Usable for synthesis right now (downloaded AND the Piper binary present).
    available: boolean;
    error: string | null;
};

export type TtsVoicesResponse = {
    // True when Piper can actually speak right now (binary + at least one
    // model present). When false the SPA falls back to the browser voice.
    configured: boolean;
    // Whether the Piper binary is present at all — lets the UI distinguish
    // "no voice downloaded yet" from "engine not installed on this server".
    piper_available: boolean;
    default_voice_id: string;
    voices: TtsVoice[];
};

/** Optional Piper knob overrides for a one-off synthesis (settings Preview).
 * Chat / cook mode omit these and let the server apply the voice's defaults. */
export type TtsParams = {
    length_scale?: number;
    noise_scale?: number;
    noise_w?: number;
    sentence_silence?: number;
    pitch_semitones?: number;
};

export default class TtsApiService {
    private httpClient = new AxiosHttpClient();

    getVoicesAsync = async (): Promise<TtsVoicesResponse> =>
        await this.httpClient.get<TtsVoicesResponse>('/tts/voices');

    /** Kick off a server-side download of a voice's model. Idempotent; returns
     * the resulting status (`ready` if already present, else `downloading`).
     * Poll getVoicesAsync to watch it complete. */
    downloadVoiceAsync = async (
        voiceId: string,
    ): Promise<{ id: string; status: TtsVoiceStatus }> =>
        await this.httpClient.post<{ id: string; status: TtsVoiceStatus }>(
            `/tts/voices/${voiceId}/download`, {},
        );

    /**
     * Synthesize `text` with the given Piper `voice` and return the audio as a
     * Blob. Uses a raw `fetch` (not the axios client) because the response is
     * binary WAV, not JSON. Throws on any non-2xx — notably a 503 when Piper
     * isn't configured — so callers can fall back to browser speech.
     */
    synthesizeAsync = async (
        text: string,
        voice: string,
        params: TtsParams = {},
    ): Promise<Blob> => {
        const res = await fetch(`${resolveBaseURL()}/tts`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, voice, ...params }),
        });
        if (!res.ok) {
            // Surface the server hint when present (e.g. the 503 setup note).
            let detail = `TTS request failed (HTTP ${res.status}).`;
            try {
                const parsed = (await res.json()) as { error?: string; hint?: string };
                if (parsed.error) detail = parsed.hint ? `${parsed.error} ${parsed.hint}` : parsed.error;
            } catch { /* non-JSON body — keep the default */ }
            const err = new Error(detail) as Error & { status?: number };
            err.status = res.status;
            throw err;
        }
        return await res.blob();
    };
}
