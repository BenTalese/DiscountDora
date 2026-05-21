// Mirrors DTOs in dora_api/features/shopping_lists/.

export type ShoppingListSummary = {
    shopping_list_id: string;
    name: string;
    is_primary: boolean;
    is_archived: boolean;
    is_in_progress: boolean;
    created_at: string;
    completed_at: string | null;
    line_count: number;
    ticked_count: number;
};

export type LineProductOffer = {
    product_id: string;
    name: string;
    brand: string | null;
    merchant_id: string;
    merchant_name: string;
    size: string | null;
    price_now: number | null;
    price_was: number | null;
    is_selected: boolean;
};

export type ShoppingListLine = {
    line_id: string;
    stock_item_id: string;
    stock_item_name: string;
    stock_level_name: string | null;
    quantity: number | null;
    is_ticked: boolean;
    selected_product_id: string | null;
    sequence: number;
    offers: LineProductOffer[];
};

export type ShoppingListDetail = {
    shopping_list_id: string;
    name: string;
    is_primary: boolean;
    is_archived: boolean;
    is_in_progress: boolean;
    created_at: string;
    completed_at: string | null;
    lines: ShoppingListLine[];
};

export type ActiveListInfo = {
    shopping_list_id: string;
    name: string;
    is_primary: boolean;
};

export type StockItemMembership = {
    stock_item_id: string;
    unticked_list_ids: string[];
    on_primary: boolean;
};

export type Membership = {
    primary_shopping_list_id: string | null;
    items: StockItemMembership[];
    active_lists?: ActiveListInfo[];
};

// Cart-button colour state derived from membership.
export type CartState = 'none' | 'on_primary' | 'on_other' | 'on_multiple';

export function cartStateFor(
    stockItemId: string,
    membership: Membership | null,
): CartState {
    if (!membership) return 'none';
    const entry = membership.items.find((i) => i.stock_item_id === stockItemId);
    if (!entry || entry.unticked_list_ids.length === 0) return 'none';
    if (entry.unticked_list_ids.length > 1) return 'on_multiple';
    return entry.on_primary ? 'on_primary' : 'on_other';
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
    const offer = chosenOfferFor(line);
    if (!offer || offer.price_now == null) return 0;
    const qty = line.quantity ?? 1;
    return offer.price_now * qty;
}
