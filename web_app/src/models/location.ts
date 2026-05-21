// Mirrors LocationNodeDto from dora_api/features/locations/get_location_tree.py
export type LocationKind = 'zone' | 'area' | 'section';

export type AttentionReasons = {
    expired: number;
    expiring_soon: number;
    out_of_stock: number;
    low_stock: number;
    flagged: number;
    stocktake_overdue: number;
};

export type LocationItem = {
    stock_item_id: string;
    name: string;
    stock_level_name: string | null;
    expiry_date: string | null;
    is_flagged: boolean;
    attention_score: number;
    attention_reasons: AttentionReasons;
};

export type LocationNode = {
    location_id: string;
    name: string;
    kind: LocationKind;
    parent_id: string | null;
    sequence: number;
    direct_item_count: number;
    descendant_item_count: number;
    attention_score: number;
    attention_reasons: AttentionReasons;
    primary_reason: string | null;
    items: LocationItem[];
    children: LocationNode[];
};

// Colour bands per the spec: 0-20 green, 21-40 teal, 41-60 yellow,
// 61-80 orange, 81-100 red. Returns a Quasar colour token.
export function attentionColor(score: number): string {
    if (score <= 20) return 'green-5';
    if (score <= 40) return 'teal-5';
    if (score <= 60) return 'amber-6';
    if (score <= 80) return 'orange-7';
    return 'red-6';
}

export function attentionBackground(score: number): string {
    if (score <= 20) return 'rgba(76, 175, 80, 0.12)';
    if (score <= 40) return 'rgba(38, 166, 154, 0.14)';
    if (score <= 60) return 'rgba(255, 193, 7, 0.18)';
    if (score <= 80) return 'rgba(255, 152, 0, 0.22)';
    return 'rgba(244, 67, 54, 0.22)';
}

// Build human "2 expired, 4 low stock" summary from the reasons block.
export function summarizeReasons(reasons: AttentionReasons): string[] {
    const parts: string[] = [];
    if (reasons.expired) parts.push(`${reasons.expired} expired`);
    if (reasons.out_of_stock) parts.push(`${reasons.out_of_stock} out of stock`);
    if (reasons.low_stock) parts.push(`${reasons.low_stock} low stock`);
    if (reasons.expiring_soon) parts.push(`${reasons.expiring_soon} expiring soon`);
    if (reasons.stocktake_overdue)
        parts.push(`${reasons.stocktake_overdue} stocktake overdue`);
    if (reasons.flagged) parts.push(`${reasons.flagged} flagged`);
    return parts;
}
