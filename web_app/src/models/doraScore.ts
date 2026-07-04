// P8-08 — wire shape for GET /api/dashboard/dora-score.
// Mirrors dora_api/domain/dora_score.py DoraScoreDto / DoraScoreComponent.
// The client only renders; the score, components, thresholds and
// trend hysteresis all live server-side (R-003).

/** R-010 closed set — mirrors DoraScoreComponentKey on the server.
 *  Used to route each component chip to a remediating action. */
export type DoraScoreComponentKey =
    | 'waste'
    | 'budget'
    | 'freshness'
    | 'runouts'
    | 'stocktake';

export type DoraScoreComponent = {
    key: DoraScoreComponentKey;
    label: string;
    /** 0-100 (higher = healthier), or null when this component has no
     *  data in the 30-day window and should be rendered dimmed
     *  (excluded from the composite, not zeroed). */
    score: number | null;
    /** One short server-authored sentence. Charter P3 — explainable. */
    reason: string;
};

export type DoraScoreTrendDirection = 'up' | 'down' | 'flat' | null;

export type DoraScore = {
    /** 0-100 composite, or null on brand-new installs where nothing
     *  scored. SPA renders "getting started" copy when null. */
    composite: number | null;
    components: DoraScoreComponent[];
    /** score - (score 7 days ago). null when trend unavailable. */
    trend_delta: number | null;
    trend_direction: DoraScoreTrendDirection;
    /** Days in the evaluation window (30 today). Travels for the
     *  card's caption; retuning window size doesn't need SPA changes. */
    window_days: number;
};
