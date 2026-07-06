import { ICONS } from 'src/style/icons';

/**
 * Onboarding sell-copy — the SINGLE SOURCE OF TRUTH for the cinematic intro
 * (C-5.2). Centralised here on purpose so any future honesty pass is a
 * one-file edit.
 *
 * ✅ Honesty pass done — FU-184 closed 2026-07-06 (P3 Honest). Every `sell`
 * line below was reconciled against the running app; the two claims that
 * didn't back cleanly were adjusted:
 *   - `WelcomeWizard.vue`'s welcome-card blurb: "pantry, deals and meals"
 *     → "pantry, shopping and cooking" (scraping was divorced — "deals"
 *     was aspirational).
 *   - `PERSONA_PREVIEWS[cooking].centreSell`: "suggesting what to cook" →
 *     "flagging what you can cook now" (the cookable-now filter + Dora
 *     Score card are the day-1 surface; active suggestions require the
 *     opt-in assistant).
 * The provisional `LOOP_INSIGHT` node was already removed 2026-06-17 in
 * the FU-210 pass — nothing dimmed-and-"coming" remains here.
 *
 * If new sell copy lands, keep it truthful to what a user with an empty
 * install can see on day 1 (features gated by admin flags like
 * `money_enabled` are fine to allude to via the persona chips — they
 * describe *what turning it on would give you*, not what's on by default).
 */

// ── The loop spine ───────────────────────────────────────────────────────

export type LoopStageKey =
    | 'stock'
    | 'plan'
    | 'list'
    | 'shop'
    | 'restock'
    | 'cook';

export interface LoopStage {
    key: LoopStageKey;
    label: string;
    icon: string;
    /** One-line sell shown when the stage is focused. Verified against the
     *  running app on 2026-07-06 (FU-184 honesty pass). */
    sell: string;
}

/**
 * Stock → Plan → List → Shop → Restock → Cook. The "Deals" stage was dropped
 * when scraping was divorced; the price-memory claim lives on the provisional
 * `LOOP_INSIGHT` node below, not on Shop (which keeps only what's real today).
 */
export const LOOP_STAGES: readonly LoopStage[] = [
    {
        key: 'stock',
        label: 'Stock',
        icon: ICONS.inventory_2,
        sell: 'Everything you keep — levels, locations, expiry — in one place you can actually trust.',
    },
    {
        key: 'plan',
        label: 'Plan',
        icon: ICONS.event,
        sell: 'See what you can cook from what’s in, plan the week, and let Dora flag the gaps.',
    },
    {
        key: 'list',
        label: 'List',
        icon: ICONS.list_alt,
        sell: 'Low, out, and meal-plan gaps flow onto a shopping list that builds itself.',
    },
    {
        key: 'shop',
        label: 'Shop',
        icon: ICONS.storefront,
        sell: 'Tick items off as you go and finish a shop in a single tap.',
    },
    {
        key: 'restock',
        label: 'Restock',
        icon: ICONS.sync,
        sell: 'Finishing the shop bumps what you bought back to stocked — no re-counting.',
    },
    {
        key: 'cook',
        label: 'Cook',
        icon: ICONS.restaurant,
        sell: 'Cook mode walks each step and counts your ingredients back down.',
    },
] as const;

export interface LoopCentre {
    label: string;
    sell: string;
}

export const LOOP_CENTRE: LoopCentre = {
    label: 'Dora',
    sell: 'The brain in the middle — watching expiry and stock, and answering when you ask.',
};

// LOOP_INSIGHT was the dimmed "Spend smarter" emerging node — removed
// 2026-06-17 after the FU-210 revisit. The user-facing "your prices"
// surfaces are now real enough (FU-213 price observations, FU-216 cost
// consumers) that dangling an unbuilt insight node violates P3 Honest.
// If a richer "paying more than usual" surface ships later, reintroduce
// it as a real loop entry, not a provisional one.

// ── The cinematic narrative ──────────────────────────────────────────────

export type SceneVisual = 'problem' | 'loop' | 'brain' | 'control';

export interface NarrativeScene {
    id: string;
    visual: SceneVisual;
    kicker?: string;
    headline: string;
    sub?: string;
    /** ms before auto-advancing; `null` waits for the user (the hero loop). */
    autoAdvanceMs: number | null;
}

export const NARRATIVE_SCENES: readonly NarrativeScene[] = [
    {
        id: 'problem',
        visual: 'problem',
        kicker: 'The weekly shop',
        headline: 'is detective work.',
        sub: 'What’s run out? What’s already in the cupboard? What do you cook — and what did it cost?',
        autoAdvanceMs: 5200,
    },
    {
        id: 'loop',
        visual: 'loop',
        kicker: 'Dora turns it into',
        headline: 'one loop that mostly runs itself.',
        sub: 'Tap any stage — or Dora in the middle — to see how it hands off to the next.',
        autoAdvanceMs: null,
    },
    {
        id: 'brain',
        visual: 'brain',
        kicker: 'Dora is the brain',
        headline: 'doing the remembering, so you don’t.',
        sub: 'Expiry, stock and your questions — quietly watched over.',
        autoAdvanceMs: 5200,
    },
    {
        id: 'control',
        visual: 'control',
        kicker: 'You’re in control',
        headline: 'as quiet or as powerful as you like.',
        sub: 'Choose what Dora does for you next — and change it any time.',
        autoAdvanceMs: 5200,
    },
] as const;

// ── Loop-emphasis preview chips (illustrative; sets no flags) ────────────
// The hero lets the user preview how the loop FEELS for different reasons
// to use Dora. It writes nothing — the persona FORK was removed in the FU-210
// pass; only the visual preview survived. Re-framed 2026-06-17 from
// "pick your persona" labels into "what Dora does for…" outcomes (the keys
// stay so existing draft persistence is undisturbed).

export type PersonaPreviewKey = 'cooking' | 'spend' | 'everything';

export interface PersonaPreview {
    key: PersonaPreviewKey;
    /** Chip label — describes the user's reason, not a persona identity. */
    label: string;
    /** Override for the Dora-centre sell on this preview. Verified against
     *  the running app on 2026-07-06 (FU-184 honesty pass). */
    centreSell: string;
}

export const PERSONA_PREVIEWS: readonly PersonaPreview[] = [
    {
        key: 'cooking',
        label: 'Mostly cooking',
        centreSell: 'Watching expiry and stock, and flagging what you can cook now.',
    },
    {
        key: 'spend',
        label: 'Watching spend',
        centreSell: 'Watching expiry, stock, and what you’ve been paying.',
    },
    {
        key: 'everything',
        label: 'All of it',
        centreSell: 'The full brain — pantry, planning, spend and more.',
    },
] as const;

/** Default preview on first paint — "All of it", so the reveal sells the ceiling. */
export const DEFAULT_PERSONA_PREVIEW: PersonaPreviewKey = 'everything';

// ── Persona fork presets — REMOVED (FU-210) ──────────────────────────────
// Onboarding no longer forks on personas or writes install flags / per-user
// opt-ins; there is one "show everything" path and features are enabled in
// Settings (money/spend is its own Settings toggle). The hero-loop preview
// chips above stay — they are illustrative only and set nothing. See
// docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md §5.
