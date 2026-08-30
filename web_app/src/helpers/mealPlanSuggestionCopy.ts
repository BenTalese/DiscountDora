import type { SuggestionReasonChip } from 'src/models/mealPlan';

/**
 * Token → copy for the rail's "Dora suggests" reason line
 * (BRIEF_MEAL_PLANNER_RAIL_AND_SHELL §4.4).
 *
 * The server ships a **frozen token vocabulary** and no prose; the wording is
 * the client's. That split is deliberate (R-003): the server owns *why* a
 * recipe was picked, the UI owns how that is said, and neither can drift into
 * the other's job. A new reason must be added to `build_week.py` first — never
 * invented here.
 *
 * **`cookable_now` is worded around D6.** F43 objected to cookable-now on this
 * page at all — *"this is the planner, not the cookbook"* — and the owner
 * revised that on 2026-08-29, but only inside a suggestion: having all the
 * ingredients is a legitimate *reason to suggest something*, and the value of
 * the chip comes from having several such reasons rather than one. So the copy
 * deliberately avoids cookability language and states the planner-relevant
 * consequence instead. F43's objection still stands everywhere outside this
 * reason line — do not reintroduce a cookable-now badge on rail rows generally.
 */
const REASON_COPY: Record<SuggestionReasonChip, string> = {
    uses_expiring: "Uses stock that's expiring",
    cookable_now: 'Nothing to buy for this',
    favourite: 'A favourite',
    not_made_recently: "Haven't had in a while",
    variety: 'Adds variety',
    budget_friendly: 'Cheaper — keeps you on budget',
    // The server's neutral fallback: it was picked, but not for a reason worth
    // a sentence. Rendering "picked" would be noise, so the row falls back to
    // its normal meta line.
    picked: '',
};

export function suggestionReasonText(chip: SuggestionReasonChip): string {
    return REASON_COPY[chip] ?? '';
}
