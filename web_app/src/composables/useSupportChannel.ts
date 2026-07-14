import { computed, ref } from 'vue';

// FU-370 — the install's support / "Report an issue" channel, read once
// per session from the /api/health `support` block. Mirrors the module-level
// shape of `useImagePolicy` / `useScanningEnabled` (ADR-002: one composable
// per concern, one health probe, shared reactive answer).
//
// The channel is a hardcoded commit-and-done switch on the backend (see
// `dora_api/features/support/support_channel.py`); the client just reflects
// whatever it emits. Both strings empty ⇒ `hasChannel` is false and every
// "Report an issue" affordance stays hidden (C-cross "gone, not greyed").
//
// The report *target* helpers (`supportHref` / `buildSupportPrefill`) live
// here too so HelpPage, PageErrorState, and the DoraBot intent share one
// implementation of the pre-fill contract (R-003) rather than each rolling
// their own URL/mailto assembly.

export interface SupportChannel {
    /** External report URL (opens in a new tab). Wins over email. */
    url: string;
    /** mailto: fallback address; used only when `url` is blank. */
    email: string;
}

export interface SupportPrefill {
    /** Pre-filled subject / issue title. */
    subject?: string;
    /** Pre-filled body. */
    body?: string;
}

const channel = ref<SupportChannel>({ url: '', email: '' });
const loaded = ref(false);
let inflight: Promise<void> | null = null;

function load(): Promise<void> {
    if (!inflight) {
        // Lazy import: `supportHref` / `currentSupportChannel` are pure and get
        // imported by the (node-env, network-free) doraIntents eval suite. A
        // top-level HealthApiService import would drag axios + quasar (which
        // touch `window`) into that suite and break it, so the health client is
        // pulled only when a real probe actually runs (browser only).
        inflight = import('src/services/api/healthApiService')
            .then(({ default: HealthApiService }) => new HealthApiService().getInfoAsync())
            .then((info) => {
                const server = info.support;
                if (!server) return;
                channel.value = {
                    url: (server.url || '').trim(),
                    email: (server.email || '').trim(),
                };
            })
            .catch(() => {
                // Health probe failure ⇒ leave the channel empty. The report
                // affordance just stays hidden; nothing else breaks.
            })
            .finally(() => {
                loaded.value = true;
            });
    }
    return inflight;
}

/** Read-only snapshot for non-Vue callers (e.g. the DoraBot intent handler,
 *  which is a plain module function). Returns the current channel even if the
 *  probe hasn't resolved yet (empty strings until it does). */
export function currentSupportChannel(): SupportChannel {
    return channel.value;
}

/** Build the href the "Report an issue" button should open, applying the
 *  pre-fill contract (proposal §4.4). Prefers the URL; falls back to mailto:.
 *  Returns '' when no channel is configured (caller should render nothing). */
export function supportHref(
    ch: SupportChannel,
    prefill: SupportPrefill = {},
): string {
    const { subject, body } = prefill;
    if (ch.url) {
        // GitHub Issues honours `title` + `body`; Tally / Google Forms ignore
        // them (harmless). The base URL may already carry a query (e.g. the
        // GitHub `?template=` param), so append with the right separator.
        const params = new URLSearchParams();
        if (subject) params.set('title', subject);
        if (body) params.set('body', body);
        const qs = params.toString();
        if (!qs) return ch.url;
        return ch.url + (ch.url.includes('?') ? '&' : '?') + qs;
    }
    if (ch.email) {
        const params = new URLSearchParams();
        if (subject) params.set('subject', subject);
        if (body) params.set('body', body);
        const qs = params.toString();
        return `mailto:${ch.email}${qs ? `?${qs}` : ''}`;
    }
    return '';
}

export function useSupportChannel() {
    void load();
    const hasChannel = computed(() => !!(channel.value.url || channel.value.email));
    return { channel, hasChannel, loaded };
}
