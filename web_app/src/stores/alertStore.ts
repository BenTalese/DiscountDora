import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Alert, Alerts } from 'src/models/alert';
import AlertApiService from 'src/services/api/alertApiService';
import { useAuthStore } from 'src/stores/authStore';
import { computed, readonly, ref } from 'vue';

const api = new AlertApiService();

// Snoozes live client-side: alerts are derived from current state on the
// backend, and we'd rather not migrate a new column for what's effectively
// a per-device "hide this for a week". Worst case the user clears their
// browser data and snoozed alerts reappear — fine.
const SNOOZE_KEY = (userId: string) => `dora.alerts.snoozes.${userId}`;

type SnoozeMap = Record<string, string>; // alert_id → ISO date (snoozed until, exclusive)

function loadSnoozes(userId: string): SnoozeMap {
    try {
        const raw = localStorage.getItem(SNOOZE_KEY(userId));
        if (!raw) return {};
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') return parsed as SnoozeMap;
        return {};
    } catch {
        return {};
    }
}

function saveSnoozes(userId: string, snoozes: SnoozeMap) {
    try {
        localStorage.setItem(SNOOZE_KEY(userId), JSON.stringify(snoozes));
    } catch {
        // localStorage may be unavailable in private windows; degrade silently.
    }
}

function pruneExpired(snoozes: SnoozeMap): SnoozeMap {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const cleaned: SnoozeMap = {};
    for (const [alertId, untilIso] of Object.entries(snoozes)) {
        const until = new Date(untilIso);
        if (Number.isFinite(until.getTime()) && until.getTime() > today.getTime()) {
            cleaned[alertId] = untilIso;
        }
    }
    return cleaned;
}

// Cached alerts shared across the app: the header bell badge, the
// notifications panel, and Dora's "what needs my attention?" intent all
// pull from the same store so they can't disagree.
export const useAlertStore = defineStore('alert', () => {
    const authStore = useAuthStore();

    const rawAlerts = ref<Alerts>({
        items: [],
        high_count: 0,
        medium_count: 0,
        low_count: 0,
    });
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    const userId = computed(() => authStore.currentUser?.user_id ?? 'anonymous');
    const snoozes = ref<SnoozeMap>(loadSnoozes(userId.value));

    function isSnoozed(alertId: string): boolean {
        const untilIso = snoozes.value[alertId];
        if (!untilIso) return false;
        const until = new Date(untilIso);
        if (!Number.isFinite(until.getTime())) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return until.getTime() > today.getTime();
    }

    // The "visible" view filters snoozed entries out and recomputes the
    // counts so the bell badge respects them.
    const alerts = computed<Alerts>(() => {
        const items = rawAlerts.value.items.filter((a) => !isSnoozed(a.alert_id));
        let high = 0;
        let medium = 0;
        let low = 0;
        for (const a of items) {
            if (a.severity === 'high') high++;
            else if (a.severity === 'medium') medium++;
            else low++;
        }
        return { items, high_count: high, medium_count: medium, low_count: low };
    });

    const snoozedCount = computed(
        () => rawAlerts.value.items.length - alerts.value.items.length,
    );

    // High + medium count drives the bell badge — low-severity items
    // (e.g. one stocktake overdue) shouldn't visually nag.
    const badgeCount = computed(() => alerts.value.high_count + alerts.value.medium_count);
    const totalCount = computed(() => alerts.value.items.length);

    const refreshAsync = async () => {
        loading.value = true;
        loadError.value = null;
        try {
            rawAlerts.value = await api.getAlertsAsync();
            // Re-load snoozes on refresh so another tab's snooze sticks
            // here too, and prune expired ones so the map doesn't grow.
            const pruned = pruneExpired(loadSnoozes(userId.value));
            snoozes.value = pruned;
            saveSnoozes(userId.value, pruned);
        } catch (err) {
            loadError.value = String(err);
        } finally {
            loading.value = false;
        }
    };

    /** Snooze a single alert for `days` (default 7) from today. */
    function snoozeAlert(alertId: string, days = 7) {
        const until = new Date();
        until.setHours(0, 0, 0, 0);
        until.setDate(until.getDate() + days);
        const next: SnoozeMap = { ...snoozes.value, [alertId]: until.toISOString() };
        snoozes.value = next;
        saveSnoozes(userId.value, next);
    }

    /** Undo a snooze (e.g. "Show snoozed"). */
    function unsnoozeAlert(alertId: string) {
        if (!(alertId in snoozes.value)) return;
        const next = { ...snoozes.value };
        delete next[alertId];
        snoozes.value = next;
        saveSnoozes(userId.value, next);
    }

    /** Currently-snoozed entries from the live alert list. */
    const snoozedAlerts = computed<Alert[]>(() =>
        rawAlerts.value.items.filter((a) => isSnoozed(a.alert_id)),
    );

    /** ISO date string for the snooze on a given alert, or null. */
    function snoozedUntil(alertId: string): string | null {
        return snoozes.value[alertId] ?? null;
    }

    return {
        alerts,
        loading: readonly(loading),
        loadError: readonly(loadError),
        badgeCount,
        totalCount,
        snoozedCount,
        snoozedAlerts,
        refreshAsync,
        isSnoozed,
        snoozedUntil,
        snoozeAlert,
        unsnoozeAlert,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAlertStore, import.meta.hot));
}
