import AxiosHttpClient from './axiosHttpClient';

export interface GraphNode {
    id: string;
    name: string;
    level: string | null;
    group_id: string | null;
}

export interface GraphEdge {
    a: string;
    b: string;
    notes: string | null;
}

export interface SubstitutesGraph {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export interface UpsertPairBody {
    a: string;
    b: string;
    notes?: string | null;
}

export default class SubstitutesApiService {
    private httpClient = new AxiosHttpClient();

    getGraphAsync = () =>
        this.httpClient.get<SubstitutesGraph>('/substitutes/graph');

    upsertPairAsync = (body: UpsertPairBody) =>
        this.httpClient.post<{ created: boolean; updated: boolean }, UpsertPairBody>(
            '/substitutes',
            body,
        );

    deletePairAsync = (a: string, b: string) =>
        this.httpClient.delete<void>(
            `/substitutes?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`,
        );
}
