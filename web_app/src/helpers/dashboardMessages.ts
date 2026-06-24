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

// Helpful hints, day-agnostic. The first eight are the original "Dora says"
// tips; the rest are new (feedback D1d asked for a larger hint pool too).
export const HINTS: string[] = [
    "I quietly judge anyone who lets the salmon hit six months in the freezer.",
    "Mark a stock item as 'open' and the opened-on date is recorded automatically.",
    "Recipes greyed out on the list? At least one ingredient is fully out.",
    "Cook mode auto-detects 'X minutes' in your steps and offers a timer.",
    "Setting your default shopping list makes the cart button one-tap.",
    "Logging a cook on a recipe also bumps its last-cooked date.",
    "Filter recipes by 'all ingredients in stock' to decide what's actually cookable now.",
    "A meal plan entry's servings can exceed the recipe's; quantities scale.",
    "Tap a stock item's level chip to change it without opening the full editor.",
    "The 'Use soon' card pulls from real expiry dates — keep them current and it stays useful.",
    "Linking a product to a stock item lets me track its price over time.",
    "Your saved products power the 'Best deals' card — save the ones you actually buy.",
    "Set a grocery budget and I'll quietly track spend against it for you.",
    "Reorder dashboard cards from the Cards menu — drag the ones you check most to the top.",
    "Stock groups are tags: one item can live in several, handy for filtering.",
];

// Days since the Unix epoch — the stable "which day is it" key both pickers
// share. Local-date based so the message flips at the user's midnight.
function epochDay(date: Date): number {
    const local = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    return Math.floor(local.getTime() / 86_400_000);
}

/** Day-of-week-appropriate welcome, stable for a given calendar day. */
export function pickWelcome(date: Date = new Date()): string {
    const pool = WEEKDAY_WELCOMES[date.getDay()] ?? WEEKDAY_WELCOMES[1]!;
    return pool[epochDay(date) % pool.length]!;
}

/** Day-agnostic hint, stable for a given calendar day. The +3 offset keeps the
 *  hint from rotating in lock-step with the welcome (so the pair feels fresh). */
export function pickHint(date: Date = new Date()): string {
    return HINTS[(epochDay(date) + 3) % HINTS.length]!;
}
