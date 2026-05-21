import type { Merchant } from 'src/models/merchant';
import AxiosHttpClient from './axiosHttpClient';

/** Talks to the merchant_api service (port 5172) which owns merchant config
 *  and the scraper enablement flag. The merchant_api returns a flat array
 *  (not the dora_api `Page<T>` envelope), so this client mirrors that shape.
 *
 *  This is distinct from `MerchantManagementApiService`, which exposes the
 *  same merchants plus provider health + write operations for the settings
 *  page. The two share the merchant_api backend but serve different mental
 *  models (read-only for product search vs full management). */
export default class MerchantApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient('merchant');
    }

    getAllAsync = async (): Promise<Merchant[]> =>
        await this.httpClient.get<Merchant[]>('/merchants');
}
