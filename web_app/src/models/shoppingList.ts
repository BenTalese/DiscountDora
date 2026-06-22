// Mirrors DTOs in dora_api/features/shopping_lists/.

// P6-01 lifecycle status — single source of truth for where a list is in the
// shop loop (mirrors SHOPPING_LIST_STATUS_* on the server). Replaces the old
// is_archived / is_in_progress boolean pair.
export type ShoppingListStatus = 'draft' | 'shopping' | 'done';

export function isListDone(status: ShoppingListStatus): boolean {
    return status === 'done';
}

export function isListShopping(status: ShoppingListStatus): boolean {
    return status === 'shopping';
}

export type ShoppingListSummary = {
    shopping_list_id: string;
    /** The user's custom name; `null` = self-labelled from dates. Use
     *  `display_name` for rendering — this field only prefills rename. */
    name: string | null;
    /** UX-v2, server-owned (R-003): custom name > planned shop date >
     *  creation date. Always render this one. */
    display_name: string;
    status: ShoppingListStatus;
    created_at: string;
    completed_at: string | null;
    /** P6-01 Chunk 7 — optional ISO date (YYYY-MM-DD) this list is planned
     *  for. Drives landing-page pick, selector sort, and shopping-day
     *  banner. `null` = unscheduled. */
    planned_shop_date: string | null;
    /** UX-v2, server-owned: finalised shop date > planned shop date >
     *  created. The summaries response arrives sorted ascending by this —
     *  render the rail/dropdown in payload order. */
    effective_date: string;
    /** UX-v2, server-owned: exactly one summary is flagged as the list the
     *  UI should land on / mark "next up" (§3.3 rule lives server-side). */
    is_next_up: boolean;
    line_count: number;
    ticked_count: number;
};

export type LineProductOffer = {
    product_id: string;
    name: string;
    brand: string | null;
    store_id: string;
    store_name: string;
    size: string | null;
    price_now: number | null;
    price_was: number | null;
    is_selected: boolean;
};

export type AddedVia =
    | 'manual'
    | 'auto_low_stock'
    | 'auto_essential'
    | 'auto_flagged'
    | 'auto_recipe'
    | 'auto_meal_plan'
    | 'auto_frequently_added';

export type ShoppingListLine = {
    line_id: string;
    /** C-7 Chunk 3 — a line is anchored by `stock_item_id` OR
     *  `product_id` (or both, when a product is nested under a stock
     *  item). NULL `stock_item_id` ⇒ standalone "product only" line. */
    stock_item_id: string | null;
    product_id: string | null;
    stock_item_name: string;
    stock_level_name: string | null;
    stock_location_id: string | null;
    stock_location_breadcrumb: string[];
    quantity: number | null;
    is_ticked: boolean;
    selected_product_id: string | null;
    sequence: number;
    /** X5 — provenance of how this line landed on the list. */
    added_via: AddedVia;
    /** ISO timestamp when the line was added. */
    added_at: string | null;
    /** P2-02 — actual unit price the shopper typed in (override of the
     *  picked offer's price). `null` = no override; use the offer instead. */
    actual_unit_price: number | null;
    /** P2-02 — store the shopper actually bought from. `null` = use the
     *  selected_product's store (if any). */
    purchased_store_id: string | null;
    /** Resolved name for `purchased_store_id`, populated by the detail
     *  endpoint. */
    purchased_store_name: string | null;
    /** FU-227 chunk 5 (D3) — server-resolved per-item price suggestion for
     *  the till editor + its human source label ("from your last receipt" /
     *  "from Coles"). `null` when there's nothing to suggest. Display-only;
     *  seeds the editor and persists on first edit. */
    prefill_unit_price: number | null;
    prefill_source_label: string | null;
    offers: LineProductOffer[];
    /** FU-215 — optional PreferredBuy hint on the line + the item's available
     *  labels for the picker. */
    preferred_buy_id?: string | null;
    preferred_buys?: { preferred_buy_id: string; label: string }[];
};

/** Server-owned list-level money/count aggregates (state-ownership Type B).
 *  The client reads these instead of summing `priceOfLine`/`savingsOfLine`
 *  across the lines itself. Per-line display price stays a client concern. */
export type ShoppingListTotals = {
    total_price: number;
    remaining_price: number;
    total_savings: number;
    unticked_count: number;
    ticked_count: number;
    line_count: number;
};

export type ShoppingListDetail = {
    shopping_list_id: string;
    /** Custom name (`null` = self-labelled) — see ShoppingListSummary. */
    name: string | null;
    /** Resolved label to render — see ShoppingListSummary. */
    display_name: string;
    status: ShoppingListStatus;
    created_at: string;
    completed_at: string | null;
    /** P6-01 Chunk 7 — see ShoppingListSummary. */
    planned_shop_date: string | null;
    totals: ShoppingListTotals;
    lines: ShoppingListLine[];
};

export type ActiveListInfo = {
    shopping_list_id: string;
    name: string;
    status: ShoppingListStatus;
};

export type StockItemMembership = {
    stock_item_id: string;
    unticked_list_ids: string[];
    on_quick_add_target: boolean;
};

export type Membership = {
    quick_add_target_list_id: string | null;
    items: StockItemMembership[];
    active_lists?: ActiveListInfo[];
};

// Cart-button colour state derived from membership. The "target" is the
// inferred quick-add destination (only set when exactly one DRAFT exists).
export type CartState = 'none' | 'on_target' | 'on_other' | 'on_multiple';

export function cartStateFor(
    stockItemId: string | null,
    membership: Membership | null,
): CartState {
    if (!stockItemId || !membership) return 'none';
    const entry = membership.items.find((i) => i.stock_item_id === stockItemId);
    if (!entry || entry.unticked_list_ids.length === 0) return 'none';
    if (entry.unticked_list_ids.length > 1) return 'on_multiple';
    return entry.on_quick_add_target ? 'on_target' : 'on_other';
}

// Selected offer for a line OR the cheapest available offer as a fallback.
// Used to compute totals.
export function chosenOfferFor(line: ShoppingListLine): LineProductOffer | null {
    if (line.selected_product_id) {
        const selected = line.offers.find((o) => o.product_id === line.selected_product_id);
        if (selected) return selected;
    }
    // offers come back sorted cheapest-first from the API.
    return line.offers[0] ?? null;
}

export function priceOfLine(line: ShoppingListLine): number {
    const qty = line.quantity ?? 1;
    // P2-02 — a user-entered actual price overrides any store offer.
    if (line.actual_unit_price != null) {
        return line.actual_unit_price * qty;
    }
    const offer = chosenOfferFor(line);
    if (!offer || offer.price_now == null) return 0;
    return offer.price_now * qty;
}

// Savings vs the line's chosen offer's RRP (price_was). Zero when the offer
// has no `price_was` recorded or isn't currently discounted. Multiplied by
// quantity so list-level totals work without re-doing the math.
//
// If the user has entered an actual paid price, we use that against the
// offer's RRP — i.e. they could have saved more (or less) than the offer
// implied. Falls back to offer.price_now when no override is set.
export function savingsOfLine(line: ShoppingListLine): number {
    const offer = chosenOfferFor(line);
    if (!offer || offer.price_was == null) return 0;
    const paid = line.actual_unit_price ?? offer.price_now;
    if (paid == null) return 0;
    const diff = offer.price_was - paid;
    if (diff <= 0) return 0;
    const qty = line.quantity ?? 1;
    return diff * qty;
}
