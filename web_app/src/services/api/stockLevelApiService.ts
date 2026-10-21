import type { StockLevel } from 'src/models/stockLevel';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export default class StockLevelApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    getAllAsync = async (): Promise<Page<StockLevel>> =>
        await this.httpClient.get<Page<StockLevel>>('/stock-levels');
}
