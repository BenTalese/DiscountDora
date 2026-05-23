import AxiosHttpClient from './axiosHttpClient';

export type SearchResultType =
    | 'stock_item'
    | 'shopping_list'
    | 'recipe'
    | 'location'
    | 'product'
    | 'meal'
    | 'meal_plan';

export type SearchResult = {
    type: SearchResultType;
    id: string;
    title: string;
    subtitle: string | null;
    icon: string | null;
    score: number;
    /** Non-overlapping [start, end) substring ranges of the query in `title`. */
    match_spans: number[][];
};

export type SearchResponse = {
    results: SearchResult[];
};

export type SearchQuery = {
    /** Restrict to certain entity types. Empty = all types. */
    types?: SearchResultType[];
    /** Per-type cap (server clamps to a max). */
    limit?: number;
};

export default class SearchApiService {
    private httpClient = new AxiosHttpClient();

    searchAsync = async (query: string, opts: SearchQuery = {}): Promise<SearchResponse> => {
        const params = new URLSearchParams({ q: query });
        if (opts.types && opts.types.length > 0) params.set('types', opts.types.join(','));
        if (opts.limit) params.set('limit', String(opts.limit));
        return await this.httpClient.get<SearchResponse>(`/search?${params.toString()}`);
    };
}
