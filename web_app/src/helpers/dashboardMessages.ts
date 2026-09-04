// Dashboard welcome + hint message pools (feedback D1d).
//
// Two separate pools, per the user's spec:
//  • WEEKDAY_WELCOMES — day-of-week-flavoured greetings, ~5 per weekday
//    (≈35 total). Picked by weekday so a "Happy Monday" never shows on a
//    Wednesday, and rotated within the day's set by the calendar day so it
//    stays stable for a given date but varies day to day.
//  • HINTS — helpful tips NOT tied to the day; surfaced alongside the
//    welcome as a secondary line.
//
// Both picks are deterministic per calendar day (same date → same message),
// so the user sees one consistent welcome all day and a fresh one tomorrow.
// New phrases can be appended freely — the pickers just modulo over the array.

export const WEEKDAY_WELCOMES: Record<number, string[]> = {
    // 0 — Sunday: wind-down, prep for the week
    0: [
        "Sunday calm. A good day to glance at the week and let me do the worrying.",
        "Lazy Sunday? Same. But future-you will thank present-you for a quick plan.",
        "Sunday roast or Sunday reset — either way, the pantry's in good hands.",
        "The week hasn't started yet. Breathe. Then maybe peek at what's running low.",
        "Sundays are for leftovers and loose ends. Let's tidy the kitchen plan.",
    ],
    // 1 — Monday: fresh start, restock
    1: [
        "New week, fresh start. Let's see what needs topping up.",
        "Monday! I've already counted the milk so you don't have to.",
        "Mondays are easier with a plan — and I happen to have one ready.",
        "Coffee first, then conquering the shopping list. I'll wait.",
        "A tidy week begins with a tidy pantry. Shall we?",
    ],
    // 2 — Tuesday
    2: [
        "Tuesday momentum. The hard part (Monday) is behind us.",
        "Still early in the week — perfect time to use up what's fresh.",
        "Taco Tuesday is a suggestion, not a rule. But I'm not stopping you.",
        "Quietly humming along. Anything in the fridge giving you side-eye yet?",
        "Two days in, going strong. Let's not let anything expire on my watch.",
    ],
    // 3 — Wednesday
    3: [
        "Midweek already. Half the groceries gone, half the week to go.",
        "Hump day. The pantry's holding up — let's keep it that way.",
        "Wednesday check-in: anything worth cooking before it turns?",
        "Right in the thick of it. A good day to plan the back half of the week.",
        "Midweek is when the good intentions wobble. I've got your back.",
    ],
    // 4 — Thursday
    4: [
        "Thursday — the weekend's practically waving at you.",
        "Almost there. Let's make sure nothing's lurking past its use-by.",
        "One more push. Maybe plan something nice for the weekend?",
        "Thursday's a sneaky-good day for a quick deal hunt.",
        "Nearly the weekend. Time to think about the big shop.",
    ],
    // 5 — Friday: weekend incoming, a little treat
    5: [
        "Friday! You've earned something tasty this weekend.",
        "Weekend's at the door. What are we cooking?",
        "Friday energy. Let's burn down that shopping list before the fun starts.",
        "TGIF. Treat yourself — within budget, obviously. I'm watching.",
        "End of the week. A good time to plan the weekend's feasts.",
    ],
    // 6 — Saturday: the big shop, cooking day
    6: [
        "Saturday — prime shopping day. Got your list ready?",
        "Big-shop energy today. Let me show you what's on special.",
        "Weekend cooking time. The pantry's your playground.",
        "Saturday markets and full trolleys. Let's do this properly.",
        "A whole day to cook and stock up. I live for this.",
    ],
};

/** Which feature a hint talks about, when it talks about a gated one.
 *
 *  FU-823 — the pool used to advertise money and product features to every
 *  install, so a household that had switched money off got told, one day in
 *  fifteen, to set a grocery budget. That is the same contradiction with
 *  feedback L254 that the card gates exist to prevent (ADR-005): a gated
 *  feature shouldn't be *promoted* on an install that turned it off any more
 *  than it should be rendered. An ungated hint has no `gate`. */
export type HintGate = 'money' | 'products';

export type Hint = { text: string; gate?: HintGate };

/** Which gated hints the current install may show. */
export type HintGates = { money: boolean; products: boolean };

// Helpful hints, day-agnostic.
//
// **Curated + fact-checked 2026-09-04** on the owner's ask: *"Have a review of
// the hints tips and tricks shown on the 'Dora says' card. Fact check the
// existing ones, and curate them to add/remove so we have a useful list where
// dora can point out things that are not so obvious in the app. Basically the
// most valuable bits that would be found in a help or guides section."*
//
// The bar every line here has to clear, and the two ways a line failed it:
//
//   1. **It has to be true.** Each claim below was checked against the code
//      this session, not against memory. Two didn't survive contact:
//        · "Your saved products power the deals card" — the Best deals card was
//          CUT by FU-819. Rewritten to name Price drops, which is the card that
//          actually exists and the one products data actually feeds.
//        · The dashboard-cards line said reorder happened inside a group.
//          The zones were removed the same day, so it now says what the control
//          does.
//      A hint that names a surface is a hostage to that surface. If you retire
//      a card, an axis or a page, **grep this file**.
//
//   2. **It has to be non-obvious.** "I quietly judge anyone who lets the
//      salmon hit six months in the freezer" was the first hint in the pool and
//      it teaches nothing — charming, but the slot under the greeting is the
//      only place Dora gets to say "you know you can…", and there is no help
//      section competing for the job. The welcomes carry the personality; these
//      carry the manual. Cut, along with nothing else — the rest were all real
//      tips, and eight new ones were added for features that are genuinely
//      hidden: cook-mode substitutions, the essential flag, batch cook style,
//      per-meal fresh cooking, the keyboard cheatsheet, planned demand,
//      stock locations, and what the alerts bell is for.
//
// Order is not significance — `pickHint` rotates by day — but related hints sit
// together so a reader scanning this file sees the shape of what's covered.
export const HINTS: Hint[] = [
    // ── Stock ────────────────────────────────────────────────────────────
    { text: "Mark a stock item as 'open' and the opened-on date is recorded automatically." },
    { text: "Tap a stock item's level chip to change it without opening the full editor." },
    { text: "Sort the stock list by 'Expires soonest' to see what to cook first." },
    { text: "Stock groups are tags: one item can live in several, handy for filtering." },
    // Locations are a tree, deliberately — not a spatial map. Worth saying,
    // because "Freezer → Top drawer" is not discoverable from a flat list.
    { text: "Locations nest: put 'Top drawer' inside 'Freezer' and filter by either." },
    // The essential flag drives the essential-low alert kind and ranks items in
    // Before you shop — neither of which is visible from the toggle itself.
    { text: "Flag an item 'essential' and I'll treat running low on it as urgent." },

    // ── Recipes & cooking ────────────────────────────────────────────────
    { text: "Recipes greyed out on the list? At least one ingredient is fully out." },
    { text: "Filter recipes by 'all ingredients in stock' to decide what's actually cookable now." },
    { text: "Logging a cook bumps the recipe's last-made date, even if you log zero meals." },
    // True as written: a structured step can declare `timer_minutes`, and the
    // free-text and photo faces fall back to sniffing the step text.
    { text: "Cook mode spots 'X minutes' in a step and offers you a timer for it." },
    // Cook-session-only substitution is the single most hidden thing in cook
    // mode — the swap doesn't touch the recipe, which is exactly why people
    // don't try it.
    { text: "Out of something mid-cook? Swap in a substitute — it only applies to this cook." },

    // ── Meal plans ───────────────────────────────────────────────────────
    { text: "A meal plan entry's servings can exceed the recipe's; quantities scale." },
    // Batch cook style is install-wide and changes what half the app means, so
    // a household that never found the switch never finds the feature.
    { text: "Batch cooker? Turn on batch cooking and I'll track the portions you've frozen." },
    // The per-entry exception to that install-wide setting (2026-09-04).
    { text: "Cooking one meal fresh in a batch week? Mark it fresh in the meal's ⋮ menu." },

    // ── Shopping ─────────────────────────────────────────────────────────
    { text: "Setting your default shopping list makes the cart button one-tap." },
    { text: "Linking a product to a stock item lets me track its price over time.", gate: 'products' },
    // Was "Your saved products power the deals card" — that card is gone.
    { text: "Saved products feed the Price drops card — save the ones you actually buy.", gate: 'products' },
    { text: "Set a grocery budget and I'll quietly track spend against it for you.", gate: 'money' },

    // ── Getting around ───────────────────────────────────────────────────
    // Reworded 2026-09-04: reorder is no longer trapped inside a zone.
    { text: "Show, hide and reorder your dashboard cards from the Cards menu." },
    // The cheatsheet is the discoverability surface for the whole keyboard
    // layer, and nothing on screen points at it.
    { text: "Press ? anywhere for the keyboard shortcuts — 'g s' for stock, 'g l' for lists." },
    // The bell and the dashboard cards answer different questions; people
    // assume the bell is the only place things surface.
    { text: "The bell is your alerts; the cards below are what to do about them." },
];

// Days since the Unix epoch — the stable "which day is it" key both pickers
// share. Local-date based so the message flips at the user's midnight.
//
// Exported because the *dismissal* needs the same key: "Hide for today" has to
// mean the same "today" the message rotation means, or the band could come back
// mid-day or stay hidden into tomorrow (FU-825).
export function epochDay(date: Date): number {
    const local = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    return Math.floor(local.getTime() / 86_400_000);
}

/** Day-of-week-appropriate welcome, stable for a given calendar day. */
export function pickWelcome(date: Date = new Date()): string {
    const pool = WEEKDAY_WELCOMES[date.getDay()] ?? WEEKDAY_WELCOMES[1]!;
    return pool[epochDay(date) % pool.length]!;
}

/** The hints this install is allowed to show — ungated ones, plus the gated
 *  ones whose feature is on (FU-823). */
export function hintsFor(gates: HintGates): Hint[] {
    return HINTS.filter((h) => {
        if (h.gate === 'money') return gates.money;
        if (h.gate === 'products') return gates.products;
        return true;
    });
}

/** Day-agnostic hint, stable for a given calendar day. The +3 offset keeps the
 *  hint from rotating in lock-step with the welcome (so the pair feels fresh).
 *
 *  Rotates over the *gated* pool, so a money-off install cycles a shorter list
 *  rather than showing a blank on the days a money hint would have come up.
 *  That does mean the rotation differs per install — which is correct: the
 *  guarantee is "stable for a given day", not "the same hint everywhere". */
export function pickHint(
    gates: HintGates = { money: true, products: true },
    date: Date = new Date(),
): string {
    const pool = hintsFor(gates);
    if (pool.length === 0) return '';
    return pool[(epochDay(date) + 3) % pool.length]!.text;
}
