import type { Merchant } from "src/models/Merchant";
import AxiosHttpClient from "./AxiosHttpClient";

// TODO: Migrate these API service to the boot folder maybe?? want to import a singleton service
export default class MerchantApiService {
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    getAllAsync = async (): Promise<Merchant[]> =>
        await this.mapiHttpClient.get<Merchant[]>('/merchants');

}
