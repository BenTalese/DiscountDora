import type { Merchant } from "src/models/merchant";
import AxiosHttpClient from "./axiosHttpClient";


export default class MerchantApiService {
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    getAllAsync = async (): Promise<Merchant[]> =>
        await this.mapiHttpClient.get<Merchant[]>('/merchants');

}
