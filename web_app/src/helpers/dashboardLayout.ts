// Dashboard layout persistence — parsing a stored `dashboard_layout` JSON
// string into the ordered / hidden card lists the page renders.
//
// Extracted from `DashboardPage.vue` (finalisation 08-R7) so the one rule here
// that is invisible in a browser has a spec: a card that shipped *after* the
// user last saved their layout is inserted at its registry position, not
// appended. The page comment always promised that; the loop appended, so
// every user with a saved layout got Kitchen health **last** when it shipped —
// the opposite of the 2026-09-08 ordering decision.
//
// A stored layout naming a retired id (`attention`, `calendar`, `savings`, …)
// simply drops it — `dashboardCards.spec.ts` keeps those ids retired.

import { CARD_DEFS, type CardId } from 'src/helpers/dashboardCards';

export type DashLayout = { order: CardId[]; hidden: CardId[] };

export const KNOWN_CARD_IDS = new Set<CardId>(CARD_DEFS.map((c) => c.id));

export function defaultOrder(): CardId[] {
    return CARD_DEFS.map((c) => c.id);
}

export function baseHiddenSet(): Set<CardId> {
    return new Set(CARD_DEFS.filter((c) => c.defaultHidden).map((c) => c.id));
}

/** Insert every registry card missing from `order` at its registry position:
 *  directly after the nearest *preceding* registry card that is present, or
 *  at the front when none is. Mutates and returns `order`. */
export function insertMissingAtRegistryPosition(order: CardId[]): CardId[] {
    CARD_DEFS.forEach((def, index) => {
        if (order.includes(def.id)) return;
        let insertAt = 0;
        for (let i = index - 1; i >= 0; i--) {
            const prev = CARD_DEFS[i]!.id;
            const at = order.indexOf(prev);
            if (at !== -1) {
                insertAt = at + 1;
                break;
            }
        }
        order.splice(insertAt, 0, def.id);
    });
    return order;
}

export function parseLayout(raw: string | null): DashLayout {
    if (!raw) return { order: defaultOrder(), hidden: [...baseHiddenSet()] };
    try {
        // Untrusted JSON — treat the arrays as raw strings and narrow each
        // entry to a known CardId at runtime.
        const parsed = JSON.parse(raw) as { order?: string[]; hidden?: string[] };
        const order = insertMissingAtRegistryPosition(
            (parsed.order ?? []).filter(
                (id): id is CardId => KNOWN_CARD_IDS.has(id as CardId),
            ),
        );
        const hidden = new Set<CardId>(
            (parsed.hidden ?? []).filter(
                (id): id is CardId => KNOWN_CARD_IDS.has(id as CardId),
            ),
        );
        // A card the user has never seen inherits its default visibility, so
        // a new opt-in-by-default card starts hidden even for existing users.
        const seen = new Set<string>([...(parsed.order ?? []), ...(parsed.hidden ?? [])]);
        for (const def of CARD_DEFS) {
            if (def.defaultHidden && !seen.has(def.id)) hidden.add(def.id);
        }
        return { order, hidden: [...hidden] };
    } catch {
        return { order: defaultOrder(), hidden: [...baseHiddenSet()] };
    }
}
