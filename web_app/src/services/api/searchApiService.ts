import AxiosHttpClient from './axiosHttpClient';

export type SearchHit = {
    kind: 'item' | 'location';
    id: string;
    name: string;
    breadcrumb: string[];
    location_id: string | null;
};

export type SearchResults = {
    query: string;
    items: SearchHit[];
    locations: SearchHit[];
};

export default class SearchApiService {
    private httpClient = new AxiosHttpClient();

    searchAsync = async (query: string): Promise<SearchResults> =>
        await this.httpClient.get<SearchResults>(
            `/search?q=${encodeURIComponent(query)}`
        );
}
