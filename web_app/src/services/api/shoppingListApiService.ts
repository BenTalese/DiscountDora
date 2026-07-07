import type {
    Membership,
    ShoppingListDetail,
    ShoppingListStatus,
    ShoppingListSummary
} from 'src/models/shoppingList';
import AxiosHttpClient, { resolveBaseURL } from './axiosHttpClient';

/** FU-334 — URL for a single receipt attachment (raw bytes). Pass a
 *  `version` (e.g. a counter bumped after upload) to bust the browser cache. */
export function shoppingListAttachmentUrl(
    listId: string,
    attachmentId: string,
    version?: number | string,
): string {
    const base = resolveBaseURL();
    const suffix = version !== undefined ? `?v=${encodeURIComponent(String(version))}` : '';
    return `${base}/shopping-lists/${listId}/attachments/${attachmentId}${suffix}`;
}

export type CreateShoppingListCommand = {
    name?: string;
    /** P6-01 Chunk 7 — ISO date (YYYY-MM-DD). Optional. */
    planned_shop_date?: string | null;
};

export type UpdateShoppingListCommand = {
    /** UX-v2 — explicit `null` clears the custom name (the list then
     *  self-labels from its dates); omitting leaves it alone. */
    name?: string | null;
    /** FU-227 chunk 5 (E3) — a list becomes `done` only via POST /finish
     *  (which snapshots prices + restocks). PATCH can move it between
     *  draft/shopping; the server 400s on `status: 'done'` here. */
    status?: Exclude<ShoppingListStatus, 'done'>;
    /** P6-01 Chunk 7 — explicit `null` clears; omitting leaves it alone. */
    planned_shop_date?: string | null;
};

export type AddLineCommand = {
    /** C-7 Chunk 3 — a line may anchor on a stock item, a product, or
     *  both. At least one MUST be set; server returns 400 otherwise. */
    stock_item_id?: string | null;
    product_id?: string | null;
    quantity?: number | null;
    selected_product_id?: string | null;
};

export type UpdateLineCommand = {
    quantity?: number | null;
    is_ticked?: boolean;
    selected_product_id?: string | null;
    clear_selected_product?: boolean;
    sequence?: number;
    /** P2-02 — what the shopper actually paid per unit. Use
     *  `clear_actual_unit_price` to wipe a prior override (passing `null`
     *  here is treated as "leave alone" by the backend). */
    actual_unit_price?: number | null;
    clear_actual_unit_price?: boolean;
    /** P2-02 — store the shopper actually bought from. */
    purchased_store_id?: string | null;
    clear_purchased_store?: boolean;
    /** FU-215 — optional PreferredBuy hint on the line. */
    preferred_buy_id?: string | null;
    clear_preferred_buy?: boolean;
    /** FU-448 — "Add back" from the Deferred-to-fit-budget section.
     *  Only ever sent as `false`. Server clears the frozen reason chip
     *  in lock-step. */
    deferred_by_budget?: boolean;
};

/** FU-448 — POST /shopping-lists/<id>/trim-to-budget request/response. */
export type TrimToBudgetCommand = {
    /** `"preview"` computes cuts without mutation; `"apply"` sets
     *  `deferred_by_budget=true` on the chosen lines and returns the
     *  same shape with `applied: true`. */
    mode: 'preview' | 'apply';
    /** Override the target headroom. Omit to use the user's
     *  period-remaining budget for the shop's expected period. */
    budget_target?: number | null;
    /** Line IDs the user has explicitly kept from the preview. */
    exclude_line_ids?: string[];
};

export type TrimmedLine = {
    line_id: string;
    tier: number;
    reason_chip: string;
    saved: number;
};

export type TrimToBudgetResult = {
    projected_total: number;
    /** `null` when the user has no budget set (feature self-gates off). */
    budget_target: number | null;
    overshoot: number;
    trimmed: TrimmedLine[];
    /** `>0` when the safe-cut tiers exhausted before hitting the target. */
    still_over: number;
    applied: boolean;
};

export type CopyShoppingListCommand = {
    include?: 'all' | 'unticked';
    name?: string | null;
};

export type FinishResult = {
    items_restocked: number;
};

/** UX-v2 restock review — per-item level choice from the finish modal.
 *  Items without an override restock to Stocked (server default). */
export type FinishLevelOverride = {
    stock_item_id: string;
    stock_level_id: string;
};

export type FinishShoppingListCommand = {
    level_overrides?: FinishLevelOverride[];
};

export type QuickAddCandidate = {
    shopping_list_id: string;
    name: string;
};

/** Discriminated outcome of POST /api/shopping-lists/primary/lines.
 *  Chunk 2: "primary" is inferred from DRAFT count — the server replies with
 *  `ambiguous` when 2+ drafts exist, expecting the client to pick (and remember
 *  the choice in sessionStorage).
 */
export type QuickAddResult =
    | {
          result: 'added';
          shopping_list_id: string;
          line_id: string | null;
          already_on_list: boolean;
      }
    | { result: 'no_draft' }
    | { result: 'ambiguous'; candidates: QuickAddCandidate[] };

/** X5 — auto-generated shopping list provenance values. Mirrors the
 *  backend ADDED_VIA_* constants. A line on a shopping list always
 *  carries one of these so the UI can render a "why is this here?"
 *  chip; "manual" is the default and means no chip. */
export type AddedVia =
    | 'manual'
    | 'auto_low_stock'
    | 'auto_essential'
    | 'auto_flagged'
    | 'auto_recipe'
    | 'auto_meal_plan'
    | 'auto_frequently_added';

export type AutoGenerateSources = {
    low_stock?: boolean;
    out_of_stock?: boolean;
    essentials_only_for_low?: boolean;
    flagged?: boolean;
    frequently_added?: boolean;
    frequently_added_limit?: number;
    /** ISO date (YYYY-MM-DD) marking the start of the meal-plan week. */
    meal_plan_week?: string | null;
    recipes?: string[];
};

export type AutoGenerateCommand = {
    name?: string | null;
    sources: AutoGenerateSources;
    merge_into_list_id?: string | null;
};

export type AutoGenerateLine = {
    line_id: string;
    stock_item_id: string;
    added_via: AddedVia;
    detail: string | null;
};

export type AutoGenerateResult = {
    shopping_list_id: string | null;
    added_count: number;
    skipped_already_on_list: number;
    nothing_to_add: boolean;
    lines: AutoGenerateLine[];
};

export type MoveUntickedResult = {
    moved_count: number;
    skipped_duplicates: number;
};

export type RefreshDealsResult = {
    lines_checked: number;
    selections_cleared: number;
};

export type ClearListResult = {
    removed_count: number;
};

export type FrequentlyAddedItem = {
    stock_item_id: string;
    name: string;
    stock_level_id: string | null;
    add_count: number;
};

export default class ShoppingListApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<ShoppingListSummary[]> =>
        await this.httpClient.get<ShoppingListSummary[]>('/shopping-lists');

    getDetailAsync = async (id: string): Promise<ShoppingListDetail> =>
        await this.httpClient.get<ShoppingListDetail>(`/shopping-lists/${id}`);

    getMembershipAsync = async (): Promise<Membership> =>
        await this.httpClient.get<Membership>('/shopping-lists/membership');

    createAsync = async (command: CreateShoppingListCommand): Promise<{ shopping_list_id: string }> =>
        await this.httpClient.post<{ shopping_list_id: string }>('/shopping-lists', command);

    updateAsync = async (id: string, command: UpdateShoppingListCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateShoppingListCommand>(
            `/shopping-lists/${id}`,
            command,
        );

    deleteAsync = async (id: string): Promise<void> =>
        await this.httpClient.delete<void>(`/shopping-lists/${id}`);

    finishAsync = async (
        id: string,
        command: FinishShoppingListCommand = {},
    ): Promise<FinishResult> =>
        await this.httpClient.post<FinishResult, FinishShoppingListCommand>(
            `/shopping-lists/${id}/finish`,
            command,
        );

    copyAsync = async (id: string, command: CopyShoppingListCommand): Promise<{ shopping_list_id: string }> =>
        await this.httpClient.post<{ shopping_list_id: string }, CopyShoppingListCommand>(
            `/shopping-lists/${id}/copy`,
            command,
        );

    addLineAsync = async (listId: string, command: AddLineCommand): Promise<{ line_id: string; already_on_list: boolean }> =>
        await this.httpClient.post<{ line_id: string; already_on_list: boolean }, AddLineCommand>(
            `/shopping-lists/${listId}/lines`,
            command,
        );

    updateLineAsync = async (listId: string, lineId: string, command: UpdateLineCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateLineCommand>(
            `/shopping-lists/${listId}/lines/${lineId}`,
            command,
        );

    deleteLineAsync = async (listId: string, lineId: string): Promise<void> =>
        await this.httpClient.delete<void>(`/shopping-lists/${listId}/lines/${lineId}`);

    removeByStockItemFromListAsync = async (
        listId: string,
        stockItemId: string,
    ): Promise<void> =>
        await this.httpClient.delete<void>(
            `/shopping-lists/${listId}/lines/by-stock-item/${stockItemId}`,
        );

    quickAddToPrimaryAsync = async (
        stockItemId: string,
        shoppingListId?: string,
    ): Promise<QuickAddResult> =>
        await this.httpClient.post<
            QuickAddResult,
            { stock_item_id: string; shopping_list_id?: string }
        >('/shopping-lists/primary/lines', {
            stock_item_id: stockItemId,
            ...(shoppingListId ? { shopping_list_id: shoppingListId } : {}),
        });

    autoGenerateAsync = async (
        command: AutoGenerateCommand,
    ): Promise<AutoGenerateResult> =>
        await this.httpClient.post<AutoGenerateResult, AutoGenerateCommand>(
            '/shopping-lists/auto-generate',
            command,
        );

    /** FU-448 — trim-to-budget optimiser. Preview or apply. */
    trimToBudgetAsync = async (
        listId: string,
        command: TrimToBudgetCommand,
    ): Promise<TrimToBudgetResult> =>
        await this.httpClient.post<TrimToBudgetResult, TrimToBudgetCommand>(
            `/shopping-lists/${listId}/trim-to-budget`,
            command,
        );

    moveUntickedToAsync = async (
        sourceId: string,
        targetId: string,
    ): Promise<MoveUntickedResult> =>
        await this.httpClient.post<MoveUntickedResult, Record<string, never>>(
            `/shopping-lists/${sourceId}/move-unticked-to/${targetId}`,
            {},
        );

    refreshDealsAsync = async (id: string): Promise<RefreshDealsResult> =>
        await this.httpClient.post<RefreshDealsResult, Record<string, never>>(
            `/shopping-lists/${id}/refresh-deals`,
            {},
        );

    // UX-v2: there is deliberately no stopShoppingAsync — the lifecycle is
    // Start shopping → Finish & restock (→ Reopen); /stop was removed.
    startShoppingAsync = async (id: string): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>(
            `/shopping-lists/${id}/start`,
            {},
        );

    bulkTickAsync = async (
        id: string,
        lineIds: string[],
        isTicked: boolean,
    ): Promise<{ updated_count: number }> =>
        await this.httpClient.post<
            { updated_count: number },
            { line_ids: string[]; is_ticked: boolean }
        >(`/shopping-lists/${id}/lines/bulk-tick`, {
            line_ids: lineIds,
            is_ticked: isTicked,
        });

    reorderLinesAsync = async (id: string, lineIdsInOrder: string[]): Promise<void> =>
        await this.httpClient.post<void, { line_ids: string[] }>(
            `/shopping-lists/${id}/lines/reorder`,
            { line_ids: lineIdsInOrder },
        );

    clearListAsync = async (id: string): Promise<ClearListResult> =>
        await this.httpClient.post<ClearListResult, Record<string, never>>(
            `/shopping-lists/${id}/clear`,
            {},
        );

    getFrequentlyAddedAsync = async (limit = 12): Promise<FrequentlyAddedItem[]> =>
        await this.httpClient.get<FrequentlyAddedItem[]>(
            `/shopping-lists/frequently-added?limit=${limit}`,
        );

    // receipt-photo record-keeping. The image is sent as a
    // `data:image/...;base64,...` string produced by `processImageFile`
    // (R-003 centralised pipeline) — DO NOT bypass that helper.
    addAttachmentAsync = async (
        listId: string,
        imageDataUrl: string,
    ): Promise<{ attachment_id: string }> =>
        await this.httpClient.post<
            { attachment_id: string },
            { image_data_url: string }
        >(`/shopping-lists/${listId}/attachments`, {
            image_data_url: imageDataUrl,
        });

    deleteAttachmentAsync = async (
        listId: string,
        attachmentId: string,
    ): Promise<void> =>
        await this.httpClient.delete<void>(
            `/shopping-lists/${listId}/attachments/${attachmentId}`,
        );
}
