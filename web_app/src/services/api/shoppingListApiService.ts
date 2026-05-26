import type {
    Membership,
    ShoppingListDetail,
    ShoppingListSummary
} from 'src/models/shoppingList';
import AxiosHttpClient from './axiosHttpClient';

export type CreateShoppingListCommand = {
    name?: string;
    make_primary?: boolean;
};

export type UpdateShoppingListCommand = {
    name?: string;
    is_primary?: boolean;
    is_archived?: boolean;
};

export type AddLineCommand = {
    stock_item_id: string;
    quantity?: number | null;
    selected_product_id?: string | null;
};

export type UpdateLineCommand = {
    quantity?: number | null;
    is_ticked?: boolean;
    selected_product_id?: string | null;
    clear_selected_product?: boolean;
    sequence?: number;
};

export type CopyShoppingListCommand = {
    include?: 'all' | 'unticked';
    name?: string | null;
};

export type FinishResult = {
    items_restocked: number;
    new_primary_list_id: string | null;
};

export type QuickAddResult = {
    shopping_list_id: string | null;
    line_id: string | null;
    already_on_list: boolean;
};

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

export type LevelRestoreSnapshot = {
    stock_item_id: string;
    stock_level_id: string;
};

export type UnfinishCommand = {
    was_primary?: boolean;
    demote_primary_list_id?: string | null;
    level_restores?: LevelRestoreSnapshot[];
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

    finishAsync = async (id: string): Promise<FinishResult> =>
        await this.httpClient.post<FinishResult, Record<string, never>>(
            `/shopping-lists/${id}/finish`,
            {},
        );

    /** F5: inverse of finish. The caller snapshots the pre-finish state and
     *  posts it back; the server un-archives, restores levels, and demotes
     *  whichever sibling was auto-promoted to primary. */
    unfinishAsync = async (
        id: string,
        command: UnfinishCommand,
    ): Promise<void> =>
        await this.httpClient.post<void, UnfinishCommand>(
            `/shopping-lists/${id}/unfinish`,
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

    quickAddToPrimaryAsync = async (stockItemId: string): Promise<QuickAddResult> =>
        await this.httpClient.post<QuickAddResult, { stock_item_id: string }>(
            '/shopping-lists/primary/lines',
            { stock_item_id: stockItemId },
        );

    autoGenerateAsync = async (
        command: AutoGenerateCommand,
    ): Promise<AutoGenerateResult> =>
        await this.httpClient.post<AutoGenerateResult, AutoGenerateCommand>(
            '/shopping-lists/auto-generate',
            command,
        );

    appendLowStockEssentialsAsync = async (
        listId: string,
    ): Promise<AutoGenerateResult> =>
        await this.httpClient.post<AutoGenerateResult, Record<string, never>>(
            `/shopping-lists/${listId}/append-low-stock-essentials`,
            {},
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

    startShoppingAsync = async (id: string): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>(
            `/shopping-lists/${id}/start`,
            {},
        );

    stopShoppingAsync = async (id: string): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>(
            `/shopping-lists/${id}/stop`,
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
}
