import type { Merchant } from "@/models/Merchant";
import AxiosHttpClient from "./AxiosHttpClient";

export default class MerchantApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    getAll = async (): Promise<Merchant[]> =>
        await this.httpClient.get<Merchant[]>('/merchants');

}
