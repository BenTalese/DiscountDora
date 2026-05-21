import AxiosHttpClient from './axiosHttpClient';

export type MerchantConfig = {
    name: string;
    is_enabled: boolean;
};

export type DataProviderHealth = {
    base_url: string;
    is_healthy: boolean;
    /** True when an ad-hoc check skipped this provider (no enabled merchant). */
    skipped?: boolean;
};

/** Talks to the standalone merchant_api on port 5172 (config + provider
 *  health). Distinct from the `MerchantApiService` that reads merchant rows
 *  out of the main Dora API. */
export default class MerchantManagementApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient('merchant');
    }

    getMerchantsAsync = async (): Promise<MerchantConfig[]> =>
        await this.httpClient.get<MerchantConfig[]>('/merchants');

    toggleMerchantAsync = async (merchantName: string): Promise<void> =>
        await this.httpClient.patch<void>(`/merchants/${encodeURIComponent(merchantName)}`, {});

    getDataProvidersHealthAsync = async (): Promise<DataProviderHealth[]> =>
        await this.httpClient.get<DataProviderHealth[]>('/health/data-providers');

    runDataProviderHealthCheckAsync = async (): Promise<DataProviderHealth[]> =>
        await this.httpClient.post<DataProviderHealth[]>('/health/data-providers/check', {});

    getApiHealthAsync = async (): Promise<boolean> =>
        await this.httpClient.get<boolean>('/health');
}
