// Planned demand — "the plan needs this, and you haven't got it".
// Server-owned (R-003): the counts, the batch allocation, the urgency grading
// and the sentence are all computed in
// `dora_api/features/stock_items/planned_demand.py`. The client renders.
//
// Deliberately NOT part of `pantryBelief.ts`, and not merged into the belief:
// the belief says what is on the shelf, this says what the plan is going to
// want. Two questions, two clocks. See that module's docstring.

/** How the demand grades against the recorded level. Out outranks Low. */
export type PlannedDemandUrgency = 'none' | 'watch' | 'blocking';

export interface PlannedDemand {
    /** Upcoming un-consumed plan entries whose recipe requires this item. */
    planned_meals: number;
    /** Of those, how many an already-cooked batch pool covers. */
    covered_meals: number;
    /** planned - covered: the meals somebody still has to cook. */
    needed_meals: number;
    /** ISO date of the first *uncovered* meal; null when all are covered. */
    earliest_needed: string | null;
    /** Distinct recipe names, soonest first (capped server-side). */
    recipe_names: string[];
    urgency: PlannedDemandUrgency;
    /** The one-line "why", in Dora's voice. */
    reason: string;
}

export interface PlannedDemandResponse {
    /** How far ahead the signal looks, in days. */
    horizon_days: number;
    /** Keyed by stock_item_id. Items with no demand are absent, not zeroed. */
    demand: Record<string, PlannedDemand>;
}
