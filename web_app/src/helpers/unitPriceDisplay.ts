import {
    CANONICAL_PRICE_UNIT,
    COUNT_DENOMINATOR,
    PRICE_DISPLAY_RULES,
    PRICING_CONVENTION_BY_SYSTEM,
    UNIT_TABLE,
    type DisplayDenominator,
    type MeasurementSystem,
} from 'src/generated/units_table';

/**
 * How a per-unit price is *quoted* — the shelf-label convention.
 *
 * Owner feedback 2026-09-13: *"Log price and possibly other areas — shouldn't
 * be displaying in such low amounts e.g. '≈ $0.01 per g'. Stores always show
 * per 100g, or per 100ml. Ensure we match logical displays of pricing and
 * units compared to real store websites."*
 *
 * The convention itself is **not** decided here. It is
 * `dora_api/domain/units.py`'s `display_denominator_for`, mirrored into the
 * generated `units_table.ts` — this module is a reader of it, not a second
 * copy (R-003). Server-rendered surfaces (the YourPrices widget, the price
 * chart axis, the offers sidecar, reports) already go through the Python
 * side; this exists for the two places that genuinely cannot, because they
 * quote a price the server has never seen:
 *
 *   • `PriceEntry.vue` previews the denominator *while you type*;
 *   • `RecipeCostDialog.vue` renders a per-unit price the cost DTO ships in
 *     the product's own raw `size_unit`.
 */

/** The `divide_factor` half of the convention, plus what to call it. */
export function displayDenominatorFor(
    dimension: string,
    measureInCanonical: number,
    system: MeasurementSystem,
): DisplayDenominator {
    const rule = PRICE_DISPLAY_RULES[PRICING_CONVENTION_BY_SYSTEM[system]]?.[dimension];
    // Count, and any dimension the table doesn't price (a recipe-only one like
    // temperature reaching here would be a bug upstream, but an unreadable
    // label is a worse answer than an unscaled one).
    if (!rule) return COUNT_DENOMINATOR;
    return measureInCanonical >= rule.flipAt ? rule.full : rule.sub;
}

/**
 * Convert *measure* of *unit* into the dimension's canonical price unit
 * (L / kg / ea), or null when the unit isn't one we know.
 *
 * `UNIT_TABLE` factors are to the dimension's **base** unit (ml / g / ea)
 * while the canonical *price* unit is the larger one, so this is two lookups
 * rather than one.
 */
export function toCanonicalPriceUnit(
    measure: number,
    unit: string,
): { amount: number; dimension: string } | null {
    const def = UNIT_TABLE[unit.toLowerCase()] ?? UNIT_TABLE[unit];
    if (!def) return null;
    const canonical = CANONICAL_PRICE_UNIT[def.dimension];
    if (!canonical) return null;
    const canonicalDef = UNIT_TABLE[canonical.toLowerCase()] ?? UNIT_TABLE[canonical];
    if (!canonicalDef) return null;
    return { amount: (measure * def.factor) / canonicalDef.factor, dimension: def.dimension };
}

/**
 * "$3.50 for 500 g" → `{ amount: 0.70, unit: '100g' }`.
 *
 * Returns null when the unit is unrecognised or the measure is non-positive —
 * callers render nothing rather than a price per something we can't name.
 */
export function quoteUnitPrice(
    totalPrice: number,
    totalMeasure: number,
    unit: string,
    system: MeasurementSystem,
): { amount: number; unit: string } | null {
    if (totalMeasure <= 0) return null;
    const canonical = toCanonicalPriceUnit(totalMeasure, unit);
    if (canonical === null || canonical.amount <= 0) return null;
    const denominator = displayDenominatorFor(canonical.dimension, canonical.amount, system);
    return {
        amount: totalPrice / canonical.amount / denominator.factor,
        unit: denominator.label,
    };
}

/**
 * The same convention applied to a price that already *is* per-unit, where
 * the pack size behind it is unknown — the recipe cost breakdown's case.
 *
 * The size-aware flip has no pack size to read here, so it reads **one of the
 * unit the price is quoted in** instead. That is a real signal rather than a
 * stand-in: the cost DTO quotes per the linked product's own `size_unit`, and
 * a pack labelled in grams is a sub-kilo pack. So `$0.004 / g` becomes
 * `$0.40 / 100g` while `$6.90 / kg` and `$2.50 / ea` are left exactly as they
 * are — which is how each of the three reads on a shelf.
 */
export function requoteUnitPrice(
    pricePerUnit: number,
    unit: string,
    system: MeasurementSystem,
): { amount: number; unit: string } | null {
    const perOneUnit = toCanonicalPriceUnit(1, unit);
    if (perOneUnit === null || perOneUnit.amount <= 0) return null;
    // `pricePerUnit` is per *unit*; rebase it onto the canonical price unit
    // before the denominator's factor can mean anything.
    const perCanonical = pricePerUnit / perOneUnit.amount;
    const denominator = displayDenominatorFor(
        perOneUnit.dimension, perOneUnit.amount, system,
    );
    return { amount: perCanonical / denominator.factor, unit: denominator.label };
}
