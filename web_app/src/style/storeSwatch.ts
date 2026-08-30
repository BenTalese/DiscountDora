/**
 * The colour a store is drawn in, and the fallback when it hasn't got one.
 *
 * Two consumers, one rule (previously the hash palette lived only in
 * `StoreLogo.vue`, and the shopping list's store card drew from the
 * categorical chart ramp instead — so the same store could be a mauve pill in
 * Settings and a chart-3 bar on the list):
 *
 *   1. `brand_colour` — the majority colour of the store's uploaded logo,
 *      derived server-side at upload (`features/stores/_logo_colour.py`).
 *      Woolworths comes out green, Coles red, Aldi blue.
 *   2. No logo (or a greyscale one) — a deterministic hash swatch off the
 *      store's name. Deterministic rather than random on purpose: a store
 *      that changed colour on every render would be worse than useless as an
 *      identity cue.
 *
 * R-002 carve-out: the hash palette is a sealed set of literal hexes, per
 * ENGINEERING_STANDARDS §R-002's "deterministic hash swatches" carve-out.
 * `brandColour` is likewise a literal, but it is *user data* — the store's own
 * logo — not a design decision being hardcoded past the token system.
 *
 * D-001 note: these are identity colours, not state colours. They never
 * encode success/warning/danger, and they are never the only channel — every
 * consumer pairs the colour with the store's name.
 */

/** Three values per entry, because the same store gets drawn two different
 *  ways and one colour can't serve both:
 *
 *    `background` — pale, for the logo placeholder, which draws the store's
 *      initial on top and therefore needs a surface with contrast to spare.
 *    `ink` — the dark letter that reads on `background`, in either theme.
 *    `fill` — saturated, for a bar segment or a dot: a shape with nothing
 *      drawn on it, whose whole job is to be identifiable at a glance.
 *
 *  The pale value used to serve both, which is why a store with no logo drew a
 *  bar segment and a chip dot that read as white — `#dfe1e8` on a light page is
 *  fine behind a letter and invisible as an 8px dot.
 *
 *  Sealed — adding entries reshuffles every existing store's colour, since the
 *  index comes from `hash % length`. */
const SWATCH_PALETTE = [
    ['#ece1c9', '#2e2820', '#b08a2e'], // sand
    ['#d8e3d0', '#1f2a1c', '#5f8a48'], // pesto-tint
    ['#e6dbe6', '#2c1f2c', '#8a5a88'], // mauve
    ['#dde6e9', '#1c2629', '#42798f'], // mist
    ['#ecd9d0', '#3a1f17', '#b0543a'], // terracotta
    ['#dfe1e8', '#1d1f28', '#525d7a'], // slate
] as const;

export type StoreSwatch = {
    /** Surface for a logo placeholder — pale, meant to be drawn on. */
    background: string;
    /** Ink that reads on `background`. Only meaningful for the hash swatch —
     *  a brand colour is used as a fill behind no text, so this stays the
     *  neutral default there. */
    ink: string;
    /** Fill for a bar segment or dot — saturated, meant to be seen. */
    fill: string;
};

function hashIndex(text: string): number {
    // 32-bit FNV-1a over the lowercased name. Plenty for picking one of N
    // palette entries with even-ish distribution.
    let h = 0x811c9dc5;
    const s = text.toLowerCase();
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 0x01000193);
    }
    return (h >>> 0) % SWATCH_PALETTE.length;
}

/** The deterministic name-derived swatch. Used on its own by the logo
 *  placeholder (which draws an initial on it, hence the ink). */
export function hashSwatch(name: string): StoreSwatch {
    const entry = SWATCH_PALETTE[hashIndex(name || '?')]!;
    return { background: entry[0], ink: entry[1], fill: entry[2] };
}

/** The colour to draw a store in as a solid shape — bar segment, chip dot:
 *  its logo's brand colour when it has one, otherwise the saturated hash
 *  fill. */
export function storeColour(
    name: string,
    brandColour: string | null | undefined,
): string {
    return brandColour ?? hashSwatch(name).fill;
}
