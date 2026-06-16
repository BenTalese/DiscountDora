// C-cross Chunk 1 — install-wide feature flags.
//
// Reads `/api/health` once per session and exposes the `features.*`
// dictionary as reactive booleans. Every consumer reads through this
// composable — never a parallel store, never a direct AppSetting fetch
// (ADR-002 pattern: one composable per feature *family*, not per flag).
//
// `refresh()` re-probes; call it from the admin Features panel after a
// successful PATCH so the cached answer doesn't drift from the row.

import { computed, ref } from 'vue';
import HealthApiService from 'src/services/api/healthApiService';

type FeatureFlagMap = Record<string, boolean>;

const flagsRaw = ref<FeatureFlagMap>({});
const loaded = ref(false);
let inflight: Promise<void> | null = null;

function load(): Promise<void> {
    if (!inflight) {
        inflight = new HealthApiService()
            .getInfoAsync()
            .then((info) => {
                flagsRaw.value = { ...info.features };
            })
            .catch(() => {
                // Network failure → leave the previous map intact (likely
                // empty on first call); consumers will see every flag as
                // false until the next refresh succeeds. Intentionally a
                // no-op — we keep whatever flags we already had.
            })
            .finally(() => {
                loaded.value = true;
            });
    }
    return inflight;
}

function readFlag(name: string): boolean {
    return !!flagsRaw.value[name];
}

export function useFeatureFlags() {
    void load();
    function refresh(): Promise<void> {
        loaded.value = false;
        inflight = null;
        return load();
    }
    return {
        flagsLoaded: loaded,
        // Named-flag computeds keep call sites concise + type-safe at the
        // read site without exposing the raw map shape. Add more as new
        // flags ship — keys here mirror the backend `_feature_flags()` map.
        auth: computed(() => readFlag('auth')),
        audit: computed(() => readFlag('audit')),
        scanning: computed(() => readFlag('scanning')),
        multiUser: computed(() => readFlag('multi_user')),
        email: computed(() => readFlag('email')),
        assistant: computed(() => readFlag('assistant')),
        mealPlanning: computed(() => readFlag('meal_planning')),
        money: computed(() => readFlag('money')),
        nutrition: computed(() => readFlag('nutrition')),
        companionIngestion: computed(() => readFlag('companion_ingestion')),
        dealsEmail: computed(() => readFlag('deals_email')),
        // Onboarding C-5.3 — products feature (linked products, price history,
        // ingestion). Per-surface gating when off is FU-182.
        products: computed(() => readFlag('products')),
        // C-cross Chunk 3 — derived capability (admin configured a
        // nutrition source). Gates the per-user `complex` mode toggle.
        nutritionComplexAvailable: computed(() => readFlag('nutrition_complex_available')),
        refresh,
    };
}
