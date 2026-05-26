import AxiosHttpClient from './axiosHttpClient';

export interface StockMapNode {
    location_id: string;
    x: number;
    y: number;
    w: number;
    h: number;
    shape: 'rect' | 'circle';
    colour: string;
    label: string;
}

export interface StockMapLayout {
    nodes: StockMapNode[];
    canvas: { w: number; h: number };
}

export interface StockMapResponse {
    layout: StockMapLayout;
    updated_at: string | null;
}

export default class StockMapApiService {
    private http = new AxiosHttpClient();

    getAsync = async (): Promise<StockMapResponse> =>
        await this.http.get<StockMapResponse>('/stock-map');

    saveAsync = async (layout: StockMapLayout): Promise<{ updated_at: string }> =>
        await this.http.put<{ updated_at: string }, { layout: StockMapLayout }>(
            '/stock-map', { layout },
        );
}
