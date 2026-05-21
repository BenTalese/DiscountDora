import AxiosHttpClient from './axiosHttpClient';

export type AddCandidate = {
    stock_item_id: string;
    name: string;
    location: string | null;
    stock_level: string | null;
};

export type AddItemStatus = 'ready' | 'ambiguous' | 'too_many' | 'not_found';

export type AddPlanItem = {
    query: string;
    quantity: number | null;
    status: AddItemStatus;
    candidates: AddCandidate[];
};

export type PendingAction = {
    type: 'add_to_shopping_list';
    no_primary: boolean;
    shopping_list: { id: string; name: string } | null;
    items: AddPlanItem[];
};

export type AssistantReply = {
    // When false, the model couldn't be reached — caller should fall back to
    // the rule-based assistant for this turn.
    available: boolean;
    // Reachable, but not a data question — let the local rule engine answer.
    defer_to_local: boolean;
    answer: string | null;
    mood: string;
    navigate_to: { path: string; label: string } | null;
    tool: string | null;
    result_count: number;
    // Present when the model proposed a data change (e.g. add to list). Nothing
    // has been mutated yet — commit via actAsync once any ambiguity is resolved.
    pending_action: PendingAction | null;
};

export type CommitAddItem = { stock_item_id: string; quantity: number | null };

export type CommitResult = {
    added: number;
    already: number;
    missing: number;
    shopping_list_id: string;
    answer: string;
};

export default class AssistantApiService {
    private httpClient = new AxiosHttpClient();

    getStatusAsync = async (): Promise<{ ai_available: boolean }> =>
        await this.httpClient.get<{ ai_available: boolean }>('/assistant/status');

    askAsync = async (message: string, currentPath: string): Promise<AssistantReply> =>
        await this.httpClient.post<AssistantReply>('/assistant/ask', {
            message,
            current_path: currentPath,
        });

    actAsync = async (shoppingListId: string, items: CommitAddItem[]): Promise<CommitResult> =>
        await this.httpClient.post<CommitResult>('/assistant/act', {
            shopping_list_id: shoppingListId,
            items,
        });
}
