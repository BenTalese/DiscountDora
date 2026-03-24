import type { StockLevel } from 'src/models/stockLevel';
import AxiosHttpClient from './axiosHttpClient';

export default class StockLevelApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    getAllAsync = async (): Promise<StockLevel[]> => await this.httpClient.get<StockLevel[]>('/stock-levels');
}
