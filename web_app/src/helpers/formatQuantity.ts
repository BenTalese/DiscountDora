// C-3 Chunk 2 — DEC-3 unit-spacing rule. A handful of metric/imperial units
// are conventionally written tight against the number ("250g", "2ml");
// everything else gets a space ("2 cloves", "1 tbsp"). This is the single
// source of truth for the rule — call sites across cook mode, recipes,
// and shopping lists should route through here so the convention can never
// drift between surfaces.
//
// Inclusion list per IMPL_PLAN_COOK_MODE.md §1 Chunk 2 / DEC-3.
const NO_SPACE_UNITS: ReadonlySet<string> = new Set([
    'ml', 'g', 'kg', 'l', 'mg', 'oz', 'lb', 'floz', 'pt', 'qt',
]);

export function formatQuantity(
    quantity: number | string | null | undefined,
    unit: string | null | undefined,
): string {
    const qty = (quantity === null || quantity === undefined || quantity === '')
        ? ''
        : String(quantity);
    const trimmedUnit = (unit ?? '').trim();
    if (!qty && !trimmedUnit) return '';
    if (!trimmedUnit) return qty;
    if (!qty) return trimmedUnit;
    const noSpace = NO_SPACE_UNITS.has(trimmedUnit.toLowerCase());
    return noSpace ? `${qty}${trimmedUnit}` : `${qty} ${trimmedUnit}`;
}
